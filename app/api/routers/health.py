from fastapi import APIRouter

from app.api.dependencies import ContainerDep
from app.api.schemas import HealthResponse

router = APIRouter(tags=["salud"])


@router.get("/health", response_model=HealthResponse)
def health(container: ContainerDep) -> HealthResponse:
    repo = container.chunk_repo
    ok = repo.healthy()
    total = repo.count() if ok else 0
    return HealthResponse(
        estado="ok" if ok and total > 0 else "degradado",
        qdrant=ok,
        chunks_indexados=total,
        version=container.settings.app.version,
    )
