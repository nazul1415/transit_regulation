from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import ArticleServiceDep
from app.api.schemas import ArticuloOut, ArticuloResumenOut, FragmentoOut
from app.domain.models import Articulo
from app.services.articulos import ArticuloNoEncontrado

router = APIRouter(prefix="/v1/articulos", tags=["artículos"])


def _resumen(a: Articulo) -> ArticuloResumenOut:
    return ArticuloResumenOut(
        articulo_num=a.articulo_num,
        cita=a.cita,
        titulo=a.titulo,
        capitulo=a.capitulo,
        capitulo_nombre=a.capitulo_nombre,
        derogado=a.derogado,
    )


@router.get("", response_model=list[ArticuloResumenOut], summary="Índice de artículos")
def listar(service: ArticleServiceDep) -> list[ArticuloResumenOut]:
    return [_resumen(a) for a in service.listar()]


@router.get("/{numero}", response_model=ArticuloOut, summary="Texto completo de un artículo")
def obtener(numero: int, service: ArticleServiceDep) -> ArticuloOut:
    try:
        a = service.obtener(numero)
    except ArticuloNoEncontrado as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ArticuloOut(
        **_resumen(a).model_dump(),
        texto=a.texto,
        texto_intro=a.texto_intro,
        paginas=a.paginas,
        fracciones=a.fracciones,
        sanciones=a.sanciones,
    )


@router.get(
    "/{numero}/fragmentos",
    response_model=list[FragmentoOut],
    summary="Fracciones e incisos de un artículo, con sanciones en UMA y pesos",
)
def fragmentos(
    numero: int,
    service: ArticleServiceDep,
    fraccion: str | None = Query(default=None, examples=["I", "XLVIII Bis"]),
    inciso: str | None = Query(default=None, examples=["a"]),
) -> list[FragmentoOut]:
    try:
        chunks = service.fragmentos(numero, fraccion, inciso)
    except ArticuloNoEncontrado as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        FragmentoOut(
            chunk_id=c.id,
            cita=c.cita,
            texto=c.texto,
            tipo=c.tipo,
            articulo_num=c.articulo_num,
            fraccion=c.fraccion,
            inciso=c.inciso,
            paginas=c.paginas,
            sanciones=c.sanciones,
            multas_en_pesos=service.multas(c),
        )
        for c in chunks
    ]
