from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .models import (
    ANALYST_OPTIONS,
    LANGUAGE_OPTIONS,
    PROVIDER_OPTIONS,
    AnalysisJob,
    AnalysisRequest,
    JobStatus,
    OptionsResponse,
)
from .runner import AnalysisRunner
from .store import JobStore
from .tickers import ticker_aliases


settings = get_settings()
store = JobStore(settings.runtime_dir)
runner = AnalysisRunner(store, settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.mark_interrupted()
    yield
    runner.shutdown()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get(f"{settings.api_prefix}/options", response_model=OptionsResponse)
def options() -> OptionsResponse:
    return OptionsResponse(
        analysts=ANALYST_OPTIONS,
        providers=PROVIDER_OPTIONS,
        languages=LANGUAGE_OPTIONS,
        ticker_aliases=ticker_aliases(),
        defaults={
            "llm_provider": settings.default_llm_provider,
            "quick_think_llm": settings.default_quick_model,
            "deep_think_llm": settings.default_deep_model,
            "output_language": settings.default_output_language,
            "research_depth": 1,
            "checkpoint_enabled": False,
        },
    )


@app.post(
    f"{settings.api_prefix}/analyses",
    response_model=AnalysisJob,
    dependencies=[Depends(require_api_key)],
)
def create_analysis(request: AnalysisRequest) -> AnalysisJob:
    return runner.submit(request)


@app.get(
    f"{settings.api_prefix}/analyses",
    response_model=list[AnalysisJob],
    dependencies=[Depends(require_api_key)],
)
def list_analyses(limit: int = Query(50, ge=1, le=200)) -> list[AnalysisJob]:
    return store.list(limit=limit)


@app.get(
    f"{settings.api_prefix}/analyses/{{job_id}}",
    response_model=AnalysisJob,
    dependencies=[Depends(require_api_key)],
)
def get_analysis(job_id: str) -> AnalysisJob:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return job


@app.get(
    f"{settings.api_prefix}/analyses/{{job_id}}/report",
    response_model=AnalysisJob,
    dependencies=[Depends(require_api_key)],
)
def get_analysis_report(job_id: str) -> AnalysisJob:
    job = get_analysis(job_id)
    if job.status != JobStatus.completed:
        raise HTTPException(status_code=409, detail="Analysis has not completed yet.")
    return job


@app.delete(
    f"{settings.api_prefix}/analyses/{{job_id}}",
    dependencies=[Depends(require_api_key)],
)
def delete_analysis(job_id: str) -> dict[str, bool]:
    deleted = store.delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return {"deleted": True}
