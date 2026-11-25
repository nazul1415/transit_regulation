# API de consulta del Reglamento de Tránsito de la CDMX (MVP)

Backend en FastAPI que responde preguntas sobre el Reglamento de Tránsito de la CDMX
(texto vigente, última reforma GOCDMX 06-05-2026) con citas a artículo, fracción e inciso.

**Reglas del sistema**
- El texto legal que ve el usuario **siempre sale de la base de datos** (Qdrant / JSON de artículos). El modelo solo redacta un resumen breve.
- Cada respuesta trae sus citas (`Art. 14, fracc. I, inciso a)`) con el texto literal, páginas, sanciones en UMA y su equivalente en pesos.
- Solo se aceptan citas a fragmentos que estaban en el contexto. Si el modelo inventa un id o menciona un artículo que no se recuperó, la respuesta se descarta y se devuelve "no encontré".
- Si la búsqueda no tiene soporte suficiente, se responde "no encontré" **sin llamar al LLM**.
- Si el LLM no responde, se devuelven los fragmentos más relevantes sin resumen (modo degradado).
- **Sin PyTorch.** No hay entrenamiento ni fine-tuning. El LLM (Qwen3) y los embeddings (bge-m3) se consumen por API compatible con OpenAI desde el servidor de inferencia en la GPU en la nube.

## Arquitectura

```
app/
├── api/              Capa HTTP: routers, esquemas, dependencias (Depends)
├── services/         Casos de uso: ingesta, recuperación híbrida, contexto, respuesta, artículos
├── domain/           Entidades, puertos (Protocol) y reglas puras (referencias legales, multas)
├── infrastructure/   Adaptadores: Qdrant, embeddings por API, LLM por LangChain, repositorio JSON
└── core/             Configuración (YAML + .env), contenedor de dependencias, logging
config/
├── settings.yaml     Configuración no secreta
└── prompts/          Prompt de sistema y plantilla de consulta (editables sin tocar código)
data/                 Chunks (768) y artículos generados por el extractor
tests/                Pruebas unitarias y de API (sin red)
```

Patrones usados:
- **Puertos y adaptadores**: los servicios dependen de `EmbeddingProvider`, `SparseEncoder`, `ChunkRepository`, `ArticleRepository` y `LLMProvider` (`app/domain/ports.py`), no de Qdrant ni de LangChain.
- **Repositorio**: `QdrantChunkRepository` (chunks + vectores) y `JsonArticleRepository` (artículos completos). Cambiar a PostgreSQL es escribir otro adaptador.
- **Estrategia + fábrica**: `crear_embeddings()` y `crear_llm()` eligen el proveedor según la configuración (`openai_compatible`, o `hashing`/`fake` para pruebas).
- **Inyección de dependencias**: `app/core/container.py` es la raíz de composición. Los servicios reciben dependencias por constructor y FastAPI las obtiene con `Depends` (`app/api/dependencies.py`). En pruebas se inyectan adaptadores falsos.
- **Fábrica de aplicación**: `create_app(settings, container)`.

### Flujo de una consulta (`POST /v1/consultas`)
1. **Referencias exactas**: si la pregunta dice "artículo 14, fracción I, inciso a)", se traen esos fragmentos por filtro de payload y van primero.
2. **Búsqueda híbrida**: semántica (vector denso de bge-m3) + palabras clave (vector disperso con IDF de Qdrant, tipo BM25, sin descargar modelos), fusionadas con Reciprocal Rank Fusion.
3. **Umbral de soporte**: referencia exacta, o similitud semántica ≥ `min_dense_score`, o cobertura de palabras clave ≥ `min_cobertura_lexica`. Si no, "no encontré".
4. **Parent document retrieval**: se manda al LLM el artículo padre completo (como lista de fragmentos con id) para no perder la sanción que suele ir al final del artículo.
5. **LLM** (LangChain `ChatOpenAI` contra vLLM/Qwen3) devuelve JSON `{encontrado, respuesta, citas: [ids]}`.
6. **Verificación de citas** y armado de la respuesta con el texto desde la BD.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health` | Estado de Qdrant y número de chunks indexados |
| POST | `/v1/consultas` | Pregunta en lenguaje natural → resumen + citas verificadas |
| GET | `/v1/busqueda?q=` | Búsqueda híbrida sin LLM (útil si la GPU está apagada) |
| GET | `/v1/articulos` | Índice de los 70 artículos |
| GET | `/v1/articulos/{n}` | Texto completo de un artículo |
| GET | `/v1/articulos/{n}/fragmentos?fraccion=&inciso=` | Fracciones/incisos con sanciones en UMA y pesos |

Documentación interactiva en `http://localhost:8080/docs`.

Ejemplo:
```bash
curl -s localhost:8080/v1/consultas -H 'Content-Type: application/json' \
  -d '{"pregunta": "¿Puedo ir en bicicleta por el carril confinado?"}'
```

## Configuración

Prioridad: variables de entorno > `.env` > `config/settings.yaml` > valores por defecto.
Formato de las variables: `RT_<SECCION>__<CLAVE>` (p. ej. `RT_LLM__BASE_URL`). Los secretos (`*_API_KEY`) van solo en `.env`.

Lo mínimo para producción:
```dotenv
RT_LLM__BASE_URL=https://tu-servidor-gpu/v1      # vLLM: vllm serve Qwen/Qwen3-8B
RT_LLM__API_KEY=...
RT_EMBEDDINGS__BASE_URL=https://tu-servidor-gpu-embeddings/v1   # TEI o vLLM con BAAI/bge-m3
RT_EMBEDDINGS__API_KEY=...
```

Servir los modelos en la GPU (referencia):
```bash
# LLM
vllm serve Qwen/Qwen3-8B --api-key $LLM_KEY --port 8000
# Embeddings (Hugging Face TEI; expone /v1/embeddings)
docker run --gpus all -p 8081:80 ghcr.io/huggingface/text-embeddings-inference:1.8 --model-id BAAI/bge-m3
```
Para usar otro modelo de embeddings (p. ej. `intfloat/multilingual-e5-large`), cambia `RT_EMBEDDINGS__MODEL`, `RT_EMBEDDINGS__DIMENSION` y los prefijos `query_prefix: "query: "` / `document_prefix: "passage: "`, y vuelve a indexar con `--recrear`.

El valor de la UMA (`uma.valor_diario`) cambia cada 1 de febrero: actualízalo en el YAML o con `RT_UMA__VALOR_DIARIO`. **Verifica el valor de 2026 contra el INEGI antes de mostrar montos en pesos.**

## Cómo correrlo

### Con Docker
```bash
cp .env.example .env               # llena las URLs y claves de la GPU
docker compose up -d qdrant api
docker compose run --rm ingest     # indexa los 768 chunks
curl localhost:8080/health
```
Sin GPU todavía, puedes levantar bge-m3 en CPU para desarrollo:
`docker compose --profile embeddings-local up -d embeddings` y `RT_EMBEDDINGS__BASE_URL=http://embeddings/v1`.

### Local, sin Docker
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m app.cli ingest --recrear
uvicorn app.main:app --reload --port 8080
```

### Modo sin servidores (solo para probar el flujo)
```bash
RT_QDRANT__LOCATION=":memory:" RT_EMBEDDINGS__PROVIDER=hashing RT_EMBEDDINGS__DIMENSION=256 \
RT_LLM__PROVIDER=fake python -c "
from app.core.config import Settings; from app.core.container import Container
c = Container(Settings()); c.ingestion_service.ingestar(recrear=True)
print(c.answer_service.responder('¿Qué dice el artículo 14, fracción I, inciso a)?').model_dump_json(indent=2))"
```
Los embeddings `hashing` no entienden semántica; solo sirven para pruebas.

## Pruebas
```bash
pytest          # 33 pruebas, sin red: Qdrant en memoria, embeddings por hashing, LLM falso
ruff check .
```

## Actualizar el reglamento
1. Regenerar los archivos con `reglamento-transito/extraer_reglamento.py` a partir del PDF vigente.
2. Copiarlos a `data/`.
3. `python -m app.cli ingest --recrear`.

## Pendiente (siguientes fases)
- Calibrar `min_dense_score` con bge-m3 real y un set de preguntas de evaluación (agentes y ciudadanos).
- Reranker (bge-reranker-v2-m3) servido por API como otro adaptador.
- Autenticación, límites de uso y registro de consultas.
- Voz (segunda fase).
