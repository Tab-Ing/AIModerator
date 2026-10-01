"""Endpoints de trabajos asíncronos (cola Redis/arq)."""

from __future__ import annotations

from arq.jobs import Job, JobStatus
from fastapi import APIRouter, status

from aimoderator.api.deps import ModerateKeyParam, RateLimitParam, RedisParam
from aimoderator.core.errors import QueueUnavailableError
from aimoderator.schemas.jobs import BatchJobRequest, JobAcceptedResponse, JobStatusResponse

router = APIRouter(tags=["trabajos"])


@router.post(
    "/jobs/moderate",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Encolar un lote de moderación (asíncrono)",
)
async def enqueue_moderation_batch(
    payload: BatchJobRequest,
    api_key: ModerateKeyParam,
    _: RateLimitParam,
    redis: RedisParam,
) -> JobAcceptedResponse:
    """Encola un lote y devuelve el ``job_id`` para consultar el resultado."""
    job = await redis.enqueue_job(
        "moderate_batch_task",
        str(api_key.tenant_id),
        payload.profile_id,
        [item.model_dump(mode="json") for item in payload.items],
    )
    if job is None:
        raise QueueUnavailableError("No se pudo encolar el trabajo")
    return JobAcceptedResponse(job_id=job.job_id, status="queued")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse, summary="Estado de un trabajo")
async def get_job(
    job_id: str,
    api_key: ModerateKeyParam,
    redis: RedisParam,
) -> JobStatusResponse:
    """Consulta el estado y, si terminó, el resultado del trabajo."""
    job = Job(job_id, redis)
    job_status = await job.status()
    result = await job.result() if job_status == JobStatus.complete else None
    return JobStatusResponse(job_id=job_id, status=job_status.name, result=result)
