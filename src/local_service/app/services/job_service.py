from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.progress import display_manager, progress_registry
from app.schemas.job_request import JobRequest
from app.schemas.job_response import JobResponse
from app.services.crop_service import CropService
from app.services.download_service import DownloadService
from app.services.merge_split_service import MergeSplitService
from app.services.storage_service import StorageService


logger = logging.getLogger(__name__)


class JobService:
    def __init__(self) -> None:
        self.storage_service = StorageService()
        self.download_service = DownloadService()
        self.crop_service = CropService()
        self.merge_split_service = MergeSplitService()

    def create_job(self, payload: JobRequest) -> JobResponse:
        if payload.site_code not in settings.supported_sites:
            raise ValueError(f"unsupported site_code: {payload.site_code}")

        job_id = self._build_job_id(payload)
        folder_name = self._build_folder_name(payload)
        progress_registry.register(job_id, folder_name)
        progress_registry.update(job_id, status="RUNNING", stage="preparing", message="create job")

        logger.info("[%s] 收到任務，準備建立工作目錄", folder_name)

        try:
            job_paths = self.storage_service.create_job_dirs(folder_name)
            download_result = self.download_service.download_images(
                [str(url) for url in payload.image_urls],
                job_paths["raw"],
                job_label=folder_name,
                job_id=job_id,
            )

            progress_registry.update(
                job_id,
                status="RUNNING",
                stage="merge-split",
                current=0,
                total=0,
                success_count=int(download_result["downloaded_count"]),
                failed_count=int(download_result["failed_count"]),
                message="prepare inputs",
            )
            merge_split_result = self.merge_split_service.prepare_processing_inputs(
                payload.site_code,
                job_paths["raw"],
                job_paths["stitched"],
            )

            crop_result = self.crop_service.crop_directory(
                Path(str(merge_split_result["processing_input_dir"])),
                job_paths["processed"],
                site_code=payload.site_code,
                job_id=job_id,
                job_label=folder_name,
            )

            progress_registry.update(
                job_id,
                status="RUNNING",
                stage="publishing",
                current=0,
                total=0,
                success_count=int(crop_result["processed_count"]),
                failed_count=int(crop_result["skipped_count"]),
                message="copy final outputs",
            )
            published_files = self.storage_service.publish_processed_outputs(
                job_paths["processed"],
                job_paths["final"],
            )

            metadata = {
                "job_id": job_id,
                "site_code": payload.site_code,
                "page_url": str(payload.page_url),
                "product_id": payload.product_id,
                "product_name": payload.product_name,
                "folder_name": folder_name,
                "tmp_output_dir": str(job_paths["root"]),
                "final_output_dir": str(job_paths["final"]),
                "image_urls": [str(url) for url in payload.image_urls],
                "download_result": download_result,
                "merge_split_result": merge_split_result,
                "crop_result": crop_result,
                "published_files": published_files,
                "metadata": payload.metadata,
                "created_at": datetime.now().astimezone().isoformat(),
                "tmp_output_deleted": False,
            }
            self.storage_service.write_metadata(job_paths["root"], metadata)
            self.storage_service.write_final_manifest(
                job_paths["final"],
                {
                    "site_code": payload.site_code,
                    "page_url": str(payload.page_url),
                    "product_id": payload.product_id,
                    "product_name": payload.product_name,
                    "folder_name": folder_name,
                    "source_job_id": job_id,
                    "tmp_output_dir": str(job_paths["root"]),
                    "final_output_dir": str(job_paths["final"]),
                    "published_files": published_files,
                    "created_at": metadata["created_at"],
                    "tmp_output_deleted": settings.is_delete_tmp_output,
                },
            )

            if settings.is_delete_tmp_output:
                self.storage_service.delete_tmp_job_root(job_paths["root"])
                metadata["tmp_output_deleted"] = True
                logger.info("[%s] 已刪除暫存資料夾", folder_name)

            logger.info(
                "[%s] 任務完成：job=%s，圖片 %s 張，下載成功 %s，失敗 %s",
                folder_name,
                job_id,
                len(payload.image_urls),
                download_result["downloaded_count"],
                download_result["failed_count"],
            )
            progress_registry.update(
                job_id,
                status="DONE",
                stage="completed",
                current=len(payload.image_urls),
                total=len(payload.image_urls),
                success_count=len(published_files),
                failed_count=int(crop_result["skipped_count"]),
                message=f"raw={len(payload.image_urls)} output={len(published_files)}",
                error_summary="",
            )

            return JobResponse(
                success=True,
                job_id=job_id,
                message="job accepted",
                tmp_output_dir=str(job_paths["root"]),
                final_output_dir=str(job_paths["final"]),
                downloaded_count=int(download_result["downloaded_count"]),
                failed_count=int(download_result["failed_count"]),
            )
        except Exception as exc:
            logger.exception("[%s] 任務失敗", folder_name)
            progress_registry.update(
                job_id,
                status="FAILED",
                stage="error",
                message="failed",
                error_summary=exc.__class__.__name__,
            )
            raise

    def _build_job_id(self, payload: JobRequest) -> str:
        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        suffix = payload.product_id or "manual"
        return f"{timestamp}_{suffix}"

    def _build_folder_name(self, payload: JobRequest) -> str:
        site_label = self._build_site_label(payload.site_code)
        product_label = self._normalize_segment(payload.product_name or "")
        product_id = self._normalize_segment(payload.product_id or "")

        info_parts: list[str] = []
        if product_label:
            info_parts.append(product_label)
        if product_id and product_id not in product_label:
            info_parts.append(product_id)

        info_label = "_".join(part for part in info_parts if part).strip("._-")
        if not info_label:
            info_label = "manual"

        folder_name = f"{site_label}-{info_label}"
        return folder_name[:120].rstrip("._-") or f"{site_label}-manual"

    def _build_site_label(self, site_code: str) -> str:
        aliases = {
            "naver_smartstore": "naver",
            "love_minuet": "love-minuet",
            "maybe_baby": "maybe-baby",
            "veryyou": "veryyou",
        }
        return self._normalize_segment(aliases.get(site_code, site_code))

    def _normalize_segment(self, value: str) -> str:
        cleaned = re.sub(r"\s+", "_", value.strip())
        cleaned = re.sub(r'[<>:"/\\\\|?*#%&{}$!@+=`~]+', "", cleaned)
        cleaned = re.sub(r"_+", "_", cleaned)
        return cleaned.strip("._")
