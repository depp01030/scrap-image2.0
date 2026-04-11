from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_SERVICE_SRC = ROOT_DIR / "src" / "local_service"
if str(LOCAL_SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(LOCAL_SERVICE_SRC))

from app.core.config import settings
from app.schemas.job_request import JobRequest
from app.services.job_service import JobService


TMP_OUTPUT_ROOT = ROOT_DIR / "tmp_output"
FIXTURE_ROOT = ROOT_DIR / "tests" / "fixtures" / "site_metadata"
REPLAY_ROOT = ROOT_DIR / "test_output" / "metadata_replay"
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


def _build_fixture_payload(metadata: dict[str, Any], source_path: Path) -> dict[str, Any]:
    return {
        "site_code": metadata["site_code"],
        "page_url": metadata["page_url"],
        "product_id": metadata.get("product_id"),
        "product_name": metadata.get("product_name"),
        "image_urls": metadata["image_urls"],
        "metadata": {
            **metadata.get("metadata", {}),
            "fixture_source": str(source_path),
            "fixture_created_at": metadata.get("created_at"),
        },
    }


def export_fixtures() -> list[Path]:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    fixture_paths: list[Path] = []

    for site_code, metadata_path in _select_latest_metadata_files().items():
        metadata = _load_json(metadata_path)
        fixture_payload = _build_fixture_payload(metadata, metadata_path)
        target_path = FIXTURE_ROOT / f"{TARGET_SITES[site_code]}.json"
        target_path.write_text(
            json.dumps(fixture_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        fixture_paths.append(target_path)

    return fixture_paths


def _iter_fixture_paths() -> list[Path]:
    paths = sorted(FIXTURE_ROOT.glob("*.json"))
    if len(paths) != len(TARGET_SITES):
        export_fixtures()
        paths = sorted(FIXTURE_ROOT.glob("*.json"))
    return paths


def replay_fixtures() -> dict[str, Any]:
    if REPLAY_ROOT.exists():
        shutil.rmtree(REPLAY_ROOT)
    REPLAY_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    REPLAY_FINAL_ROOT.mkdir(parents=True, exist_ok=True)

    original_tmp_root = settings.tmp_output_root
    original_final_root = settings.final_output_root
    original_clean_flag = settings.clean_work_dirs_on_rerun

    settings.tmp_output_root = REPLAY_TMP_ROOT
    settings.final_output_root = REPLAY_FINAL_ROOT
    settings.clean_work_dirs_on_rerun = True

    service = JobService()
    results: list[dict[str, Any]] = []

    try:
        for fixture_path in _iter_fixture_paths():
            fixture_payload = _load_json(fixture_path)
            request = JobRequest(**fixture_payload)
            response = service.create_job(request)
            results.append(
                {
                    "fixture": fixture_path.name,
                    "site_code": request.site_code,
                    "job_id": response.job_id,
                    "tmp_output_dir": response.tmp_output_dir,
                    "final_output_dir": response.final_output_dir,
                    "downloaded_count": response.downloaded_count,
                    "failed_count": response.failed_count,
                }
            )
    finally:
        settings.tmp_output_root = original_tmp_root
        settings.final_output_root = original_final_root
        settings.clean_work_dirs_on_rerun = original_clean_flag

    report = {
        "fixture_root": str(FIXTURE_ROOT),
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
    fixture_paths = export_fixtures()
    report = replay_fixtures()
    print("Exported fixtures:")
    for path in fixture_paths:
        print(f"  {path}")
    print("Replay output:")
    print(f"  tmp:   {report['replay_tmp_root']}")
    print(f"  final: {report['replay_final_root']}")
    print(f"  report:{REPORT_PATH}")


if __name__ == "__main__":
    main()
