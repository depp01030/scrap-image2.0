from fastapi import APIRouter, HTTPException, status

from app.schemas.job_request import JobRequest
from app.schemas.job_response import JobResponse
from app.services.job_service import JobService


router = APIRouter(prefix="/jobs", tags=["jobs"])
job_service = JobService()


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(payload: JobRequest) -> JobResponse:
    try:
        return job_service.create_job(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

