from pydantic import BaseModel


class JobResponse(BaseModel):
    success: bool
    job_id: str | None = None
    message: str
    tmp_output_dir: str | None = None
    final_output_dir: str | None = None
    downloaded_count: int = 0
    failed_count: int = 0
