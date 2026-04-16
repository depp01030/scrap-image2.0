from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.progress import progress_registry


logger = logging.getLogger(__name__)


class DownloadService:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(30.0, connect=15.0)

    def download_images(
        self,
        image_urls: list[str],
        raw_dir: Path,
        job_label: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, object]:
        downloaded_files: list[str] = []
        failures: list[dict[str, str]] = []
        total_count = len(image_urls)
        label = job_label or "job"

        logger.info("[%s] 開始下載：總共 %s 張", label, total_count)
        if job_id:
            progress_registry.update(
                job_id,
                status="RUNNING",
                stage="downloading",
                current=0,
                total=total_count,
                success_count=0,
                failed_count=0,
                message="starting",
                error_summary="",
            )

        with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
            for index, image_url in enumerate(image_urls, start=1):
                try:
                    target_path = self._build_target_path(raw_dir, index, image_url)
                    self._download_with_retry(client, image_url, target_path)
                    downloaded_files.append(str(target_path))
                except Exception as exc:
                    failures.append({"url": image_url, "error": str(exc)})
                    logger.exception("[%s] 下載失敗：%s", label, image_url)
                finally:
                    logger.info(
                        "[%s] 下載進度：%s/%s，成功 %s，失敗 %s",
                        label,
                        index,
                        total_count,
                        len(downloaded_files),
                        len(failures),
                    )
                    if job_id:
                        progress_registry.update(
                            job_id,
                            status="RUNNING",
                            stage="downloading",
                            current=index,
                            total=total_count,
                            success_count=len(downloaded_files),
                            failed_count=len(failures),
                            message="active",
                        )

        logger.info(
            "[%s] 下載完成：成功 %s 張，失敗 %s 張",
            label,
            len(downloaded_files),
            len(failures),
        )

        return {
            "downloaded_count": len(downloaded_files),
            "failed_count": len(failures),
            "downloaded_files": downloaded_files,
            "failures": failures,
        }

    def _download_with_retry(self, client: httpx.Client, image_url: str, target_path: Path) -> None:
        last_error: Exception | None = None
        for _ in range(settings.retry_count + 1):
            try:
                with client.stream("GET", image_url) as response:
                    response.raise_for_status()
                    with target_path.open("wb") as file_obj:
                        for chunk in response.iter_bytes():
                            file_obj.write(chunk)
                return
            except Exception as exc:
                last_error = exc

        raise RuntimeError(f"download failed for {image_url}: {last_error}")

    def _build_target_path(self, raw_dir: Path, index: int, image_url: str) -> Path:
        parsed = urlparse(image_url)
        suffix = Path(parsed.path).suffix.lower()
        if not suffix:
            guessed_suffix, _ = mimetypes.guess_type(image_url)
            suffix = mimetypes.guess_extension(guessed_suffix or "") or ".jpg"
        if len(suffix) > 5:
            suffix = ".jpg"
        return raw_dir / f"{index:03d}{suffix}"
