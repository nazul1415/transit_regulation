from fastapi import APIRouter, Query

from app.api.dependencies import AnswerServiceDep, ArticleServiceDep, RetrievalServiceDep
from app.api.schemas import BusquedaResponse, ConsultaRequest, FragmentoOut
from app.domain.models import Respuesta

router = APIRouter(prefix="/v1", tags=["consultas"])


@router.post("/consultas", response_model=Respuesta, summary="Pregunta en lenguaje natural con citas")
def consultar(body: ConsultaRequest, service: AnswerServiceDep) -> Respuesta:
    return service.responder(body.pregunta, body.top_k)


@router.get("/busqueda", response_model=BusquedaResponse, summary="Búsqueda híbrida sin LLM")
def buscar(
    retrieval: RetrievalServiceDep,
    articulos: ArticleServiceDep,
    q: str = Query(min_length=2, max_length=500),
    top_k: int = Query(default=8, ge=1, le=50),
) -> BusquedaResponse:
    rec = retrieval.buscar(q, top_k)
    return BusquedaResponse(
        pregunta=q,
        resultados=[
            FragmentoOut(
                chunk_id=r.chunk.id,
                cita=r.chunk.cita,
                texto=r.chunk.texto,
                tipo=r.chunk.tipo,
                articulo_num=r.chunk.articulo_num,
                fraccion=r.chunk.fraccion,
                inciso=r.chunk.inciso,
                paginas=r.chunk.paginas,
                sanciones=r.chunk.sanciones,
                multas_en_pesos=articulos.multas(r.chunk),
                score=r.score,
                coincidencia_exacta=r.coincidencia_exacta,
            )
            for r in rec.resultados
        ],
    )
