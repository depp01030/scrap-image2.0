from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.core.config import settings


class StorageService:
    def create_job_dirs(self, folder_name: str) -> dict[str, Path]:
        root = settings.tmp_output_root / folder_name
        paths = {
            "root": root,
            "raw": root / "raw",
            "processed": root / "processed",
            "stitched": root / "stitched",
            "split": root / "split",
            "logs": root / "logs",
            "final": settings.final_output_root / folder_name,
        }
        root.mkdir(parents=True, exist_ok=True)
        for key, path in paths.items():
            if key in {"root", "final"}:
                continue
            if settings.clean_work_dirs_on_rerun and path.exists():
                shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)
        if settings.clean_work_dirs_on_rerun and paths["final"].exists():
            for child in paths["final"].iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        paths["final"].mkdir(parents=True, exist_ok=True)
        return paths

    def write_metadata(self, job_root: Path, metadata: dict) -> None:
        target = job_root / "metadata.json"
        target.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def write_final_manifest(self, final_root: Path, metadata: dict) -> None:
        target = final_root / "manifest.json"
        target.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def publish_processed_outputs(self, processed_dir: Path, final_root: Path) -> list[str]:
        published_files: list[str] = []
        for processed_file in sorted(processed_dir.glob("*")):
            if not processed_file.is_file():
                continue
            target = final_root / processed_file.name
            shutil.copy2(processed_file, target)
            published_files.append(str(target))
        return published_files
