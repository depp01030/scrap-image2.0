from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_SERVICE_ROOT = REPO_ROOT / "src" / "local_service"
if str(LOCAL_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_SERVICE_ROOT))

from app.core.config import settings  # noqa: E402
from app.schemas.job_request import JobRequest  # noqa: E402
from app.services.crop_service import CropService  # noqa: E402
from app.services.download_service import DownloadService  # noqa: E402
from app.services.merge_split_service import MergeSplitService  # noqa: E402
from app.services.storage_service import StorageService  # noqa: E402


logger = logging.getLogger("replay_dataset_cases")

TESTS_ROOT = REPO_ROOT / "tests"
DATASET_ROOT = TESTS_ROOT / "dataset"
OUTPUT_ROOT = TESTS_ROOT / "output"

SITE_ALIASES = {
    "love-minuet": "love_minuet",
    "naver": "naver_smartstore",
    "maybe-baby": "maybe_baby",
    "veryyou": "veryyou",
}


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@contextmanager
def override_settings(*, tmp_output_root: Path, final_output_root: Path) -> Iterator[None]:
    original_tmp_output_root = settings.tmp_output_root
    original_final_output_root = settings.final_output_root
    original_is_delete_tmp_output = settings.is_delete_tmp_output
    try:
        settings.tmp_output_root = tmp_output_root
        settings.final_output_root = final_output_root
        settings.is_delete_tmp_output = False
        yield
    finally:
        settings.tmp_output_root = original_tmp_output_root
        settings.final_output_root = original_final_output_root
        settings.is_delete_tmp_output = original_is_delete_tmp_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay dataset cases from tests/dataset into tests/output.",
    )
    parser.add_argument(
        "--case",
        dest="case_name",
        help="Run a single case folder under tests/dataset.",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Do not clear tests/output/<case> before replaying.",
    )
    return parser.parse_args()


def discover_cases(case_name: str | None) -> list[Path]:
    if case_name:
        case_dir = DATASET_ROOT / case_name
        if not case_dir.is_dir():
            raise FileNotFoundError(f"case not found: {case_dir}")
        return [case_dir]

    return sorted(path for path in DATASET_ROOT.iterdir() if path.is_dir())


def load_metadata(case_dir: Path) -> dict | None:
    metadata_path = case_dir / "metadata.json"
    if not metadata_path.exists():
        return None
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def infer_site_code(case_dir: Path, metadata: dict | None) -> str:
    if metadata and metadata.get("site_code"):
        return str(metadata["site_code"])

    folder_name = case_dir.name
    site_label = folder_name.split("-", 1)[0]
    inferred = SITE_ALIASES.get(site_label)
    if inferred:
        return inferred

    raise ValueError(f"cannot infer site_code for case: {case_dir.name}")


def build_request_from_metadata(metadata: dict) -> JobRequest:
    return JobRequest(
        site_code=str(metadata["site_code"]),
        page_url=str(metadata["page_url"]),
        product_id=metadata.get("product_id"),
        product_name=metadata.get("product_name"),
        image_urls=[str(url) for url in metadata.get("image_urls", [])],
        metadata=metadata.get("metadata", {}),
    )


def run_case_from_metadata(case_dir: Path, output_case_dir: Path, metadata: dict) -> dict[str, object]:
    request = build_request_from_metadata(metadata)
    folder_name = case_dir.name
    storage_service = StorageService()
    download_service = DownloadService()
    merge_split_service = MergeSplitService()
    crop_service = CropService()

    with override_settings(
        tmp_output_root=case_dir.parent,
        final_output_root=OUTPUT_ROOT,
    ):
        job_paths = storage_service.create_job_dirs(folder_name)
        download_result = download_service.download_images(
            [str(url) for url in request.image_urls],
            job_paths["raw"],
            job_label=folder_name,
        )
        merge_split_result = merge_split_service.prepare_processing_inputs(
            request.site_code,
            job_paths["raw"],
            job_paths["stitched"],
        )
        crop_result = crop_service.crop_directory(
            Path(str(merge_split_result["processing_input_dir"])),
            job_paths["processed"],
            site_code=request.site_code,
        )
        published_files = storage_service.publish_processed_outputs(
            job_paths["processed"],
            job_paths["final"],
        )
        metadata_payload = {
            "site_code": request.site_code,
            "page_url": str(request.page_url),
            "product_id": request.product_id,
            "product_name": request.product_name,
            "folder_name": folder_name,
            "dataset_case_dir": str(case_dir),
            "tmp_output_dir": str(job_paths["root"]),
            "final_output_dir": str(job_paths["final"]),
            "download_result": download_result,
            "merge_split_result": merge_split_result,
            "crop_result": crop_result,
            "published_files": published_files,
            "metadata": request.metadata,
        }
        storage_service.write_metadata(job_paths["root"], metadata_payload)

    return {
        "mode": "download",
        "success": True,
        "tmp_output_dir": str(case_dir),
        "final_output_dir": str(output_case_dir),
        "downloaded_count": int(download_result["downloaded_count"]),
        "failed_count": int(download_result["failed_count"]),
    }


def run_case_from_raw(case_dir: Path, output_case_dir: Path, metadata: dict | None) -> dict[str, object]:
    raw_dir = case_dir / "raw"
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"raw directory not found: {raw_dir}")

    folder_name = case_dir.name
    tmp_root = case_dir
    final_root = output_case_dir
    for child in final_root.iterdir() if final_root.exists() else []:
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    storage_service = StorageService()
    merge_split_service = MergeSplitService()
    crop_service = CropService()

    with override_settings(
        tmp_output_root=case_dir.parent,
        final_output_root=OUTPUT_ROOT,
    ):
        processed_dir = case_dir / "processed"
        stitched_dir = case_dir / "stitched"
        split_dir = case_dir / "split"
        logs_dir = case_dir / "logs"
        for path in (processed_dir, stitched_dir, split_dir, logs_dir):
            if path.exists():
                shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)

        dataset_raw_files = sorted(path for path in raw_dir.glob("*") if path.is_file())

        site_code = infer_site_code(case_dir, metadata)
        merge_split_result = merge_split_service.prepare_processing_inputs(
            site_code,
            raw_dir,
            stitched_dir,
        )
        crop_result = crop_service.crop_directory(
            Path(str(merge_split_result["processing_input_dir"])),
            processed_dir,
            site_code=site_code,
        )
        published_files = storage_service.publish_processed_outputs(
            processed_dir,
            final_root,
        )

        metadata_payload = {
            "site_code": site_code,
            "page_url": metadata.get("page_url") if metadata else None,
            "product_id": metadata.get("product_id") if metadata else None,
            "product_name": metadata.get("product_name") if metadata else None,
            "folder_name": folder_name,
            "dataset_case_dir": str(case_dir),
            "tmp_output_dir": str(case_dir),
            "final_output_dir": str(final_root),
            "download_result": {
                "downloaded_count": len(dataset_raw_files),
                "failed_count": 0,
                "downloaded_files": [str(path) for path in dataset_raw_files],
                "failures": [],
                "source": "dataset_raw",
            },
            "merge_split_result": merge_split_result,
            "crop_result": crop_result,
            "published_files": published_files,
            "metadata": metadata.get("metadata", {}) if metadata else {},
        }
        storage_service.write_metadata(case_dir, metadata_payload)

    return {
        "mode": "raw",
        "success": True,
        "downloaded_count": len(dataset_raw_files),
        "failed_count": 0,
        "tmp_output_dir": str(tmp_root),
        "final_output_dir": str(final_root),
    }


def run_case(case_dir: Path, keep_output: bool) -> dict[str, object]:
    output_case_dir = OUTPUT_ROOT / case_dir.name
    if output_case_dir.exists() and not keep_output:
        shutil.rmtree(output_case_dir)
    output_case_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_metadata(case_dir)
    if metadata is not None:
        return run_case_from_metadata(case_dir, output_case_dir, metadata)
    return run_case_from_raw(case_dir, output_case_dir, metadata)


def main() -> int:
    configure_logging()
    args = parse_args()
    cases = discover_cases(args.case_name)

    summary: dict[str, dict[str, object]] = {}
    for case_dir in cases:
        logger.info("Running dataset case: %s", case_dir.name)
        try:
            result = run_case(case_dir, keep_output=args.keep_output)
            summary[case_dir.name] = result
            logger.info(
                "Finished case: %s | mode=%s | output=%s",
                case_dir.name,
                result["mode"],
                result["final_output_dir"],
            )
        except Exception as exc:
            logger.exception("Failed case: %s", case_dir.name)
            summary[case_dir.name] = {
                "success": False,
                "error": str(exc),
            }

    report_path = OUTPUT_ROOT / "report.json"
    report_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Wrote replay report: %s", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
