import json
from pathlib import Path

from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[4]
CONFIG_PATH = ROOT_DIR / "config.json"


class Settings(BaseModel):
    port: int = 8765
    tmp_output_root: Path = ROOT_DIR / "tmp_output"
    final_output_root: Path = ROOT_DIR / "output"
    is_delete_tmp_output: bool = False
    supported_sites: list[str] = [
        "love_minuet",
        "naver_smartstore",
        "maybe_baby",
        "veryyou",
    ]
    merge_split_sites: list[str] = ["veryyou"]
    retry_count: int = 2
    trim_threshold: int = Field(default=245, ge=0, le=255)
    background_diff_threshold: int = Field(default=12, ge=0, le=255)
    split_row_threshold: int = Field(default=250, ge=0, le=255)
    min_split_gap_rows: int = Field(default=24, ge=1)
    min_segment_height: int = Field(default=120, ge=1)
    min_process_width: int = Field(default=300, ge=1)
    min_process_height: int = Field(default=300, ge=1)
    min_component_area: int = Field(default=2000, ge=1)
    blank_row_ratio_threshold: float = Field(default=0.01, ge=0, le=1)
    vertical_merge_gap_rows: int = Field(default=120, ge=1)
    max_split_parts: int = Field(default=3, ge=1)
    band_row_ratio_threshold: float = Field(default=0.015, ge=0, le=1)
    min_band_height: int = Field(default=80, ge=1)
    full_width_blank_ratio: float = Field(default=0.7, ge=0, le=1)
    full_width_min_gap_rows: int = Field(default=1, ge=1)
    recursive_split_max_depth: int = Field(default=2, ge=0)
    white_background_max_diff: int = Field(default=30, ge=0, le=255)
    cors_allow_origins: list[str] = ["*"]
    clean_work_dirs_on_rerun: bool = True


def load_settings() -> Settings:
    if not CONFIG_PATH.exists():
        return Settings()

    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for key in ("tmp_output_root", "final_output_root"):
        if key not in payload:
            continue
        configured_output = Path(payload[key])
        payload[key] = (
            configured_output
            if configured_output.is_absolute()
            else ROOT_DIR / configured_output
        )
    return Settings(**payload)


settings = load_settings()
