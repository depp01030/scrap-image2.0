from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import sys


ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_SERVICE_SRC = ROOT_DIR / "src" / "local_service"
if str(LOCAL_SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(LOCAL_SERVICE_SRC))

from app.services.crop_service import CropService
from app.services.merge_split_service import MergeSplitService
from app.services.storage_service import StorageService


TMP_OUTPUT_ROOT = ROOT_DIR / "tmp_output"
REPLAY_ROOT = ROOT_DIR / "test_output" / "processing_replay"
REPLAY_TMP_ROOT = REPLAY_ROOT / "tmp"
REPLAY_FINAL_ROOT = REPLAY_ROOT / "final"
REPORT_PATH = REPLAY_ROOT / "report.json"

TARGET_SITES = {
    "love_minuet": "love-minuet",
    "naver_smartstore": "naver",
    "maybe_baby": "maybe-baby",
    "veryyou": "veryyou",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _select_latest_metadata_files() -> dict[str, Path]:
    selected: dict[str, tuple[Path, dict[str, Any]]] = {}
    for metadata_path in TMP_OUTPUT_ROOT.glob("*/metadata.json"):
        payload = _load_json(metadata_path)
        site_code = payload.get("site_code")
        if site_code not in TARGET_SITES:
            continue
        existing = selected.get(site_code)
        if existing is None:
            selected[site_code] = (metadata_path, payload)
            continue
        current_created_at = payload.get("created_at", "")
        previous_created_at = existing[1].get("created_at", "")
        if current_created_at >= previous_created_at:
            selected[site_code] = (metadata_path, payload)

    missing_sites = sorted(set(TARGET_SITES) - set(selected))
    if missing_sites:
        missing = ", ".join(missing_sites)
        raise RuntimeError(f"missing metadata.json for sites: {missing}")

    return {site_code: item[0] for site_code, item in selected.items()}


def reprocess_saved_downloads() -> dict[str, Any]:
    if REPLAY_ROOT.exists():
        shutil.rmtree(REPLAY_ROOT)
    REPLAY_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    REPLAY_FINAL_ROOT.mkdir(parents=True, exist_ok=True)

    crop_service = CropService()
    merge_split_service = MergeSplitService()
    storage_service = StorageService()
    results: list[dict[str, Any]] = []

    for site_code, metadata_path in _select_latest_metadata_files().items():
        metadata = _load_json(metadata_path)
        source_root = metadata_path.parent
        source_raw_dir = source_root / "raw"

        folder_name = source_root.name
        replay_root = REPLAY_TMP_ROOT / folder_name
        stitched_dir = replay_root / "stitched"
        processed_dir = replay_root / "processed"
        final_dir = REPLAY_FINAL_ROOT / folder_name

        if replay_root.exists():
            shutil.rmtree(replay_root)
        if final_dir.exists():
            shutil.rmtree(final_dir)

        stitched_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)

        merge_split_result = merge_split_service.prepare_processing_inputs(
            site_code,
            source_raw_dir,
            stitched_dir,
        )
        crop_result = crop_service.crop_directory(
            Path(str(merge_split_result["processing_input_dir"])),
            processed_dir,
            site_code=site_code,
        )
        published_files = storage_service.publish_processed_outputs(processed_dir, final_dir)

        replay_metadata = {
            "site_code": site_code,
            "source_metadata": str(metadata_path),
            "source_raw_dir": str(source_raw_dir),
            "replay_stitched_dir": str(stitched_dir),
            "replay_processed_dir": str(processed_dir),
            "replay_final_dir": str(final_dir),
            "product_id": metadata.get("product_id"),
            "product_name": metadata.get("product_name"),
            "merge_split_result": merge_split_result,
            "crop_result": crop_result,
            "published_files": published_files,
        }
        storage_service.write_metadata(replay_root, replay_metadata)
        storage_service.write_final_manifest(final_dir, replay_metadata)

        results.append(
            {
                "site_code": site_code,
                "folder_name": folder_name,
                "source_metadata": str(metadata_path),
                "source_raw_dir": str(source_raw_dir),
                "replay_stitched_dir": str(stitched_dir),
                "replay_processed_dir": str(processed_dir),
                "replay_final_dir": str(final_dir),
                "merge_split_result": merge_split_result,
                "processed_count": crop_result["processed_count"],
                "skipped_count": crop_result["skipped_count"],
                "published_count": len(published_files),
            }
        )

    report = {
        "replay_tmp_root": str(REPLAY_TMP_ROOT),
        "replay_final_root": str(REPLAY_FINAL_ROOT),
        "results": results,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def main() -> None:
    report = reprocess_saved_downloads()
    print(f"tmp:   {report['replay_tmp_root']}")
    print(f"final: {report['replay_final_root']}")
    print(f"report:{REPORT_PATH}")


if __name__ == "__main__":
    main()
