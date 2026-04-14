from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings
from app.services.crop_service import CropService


class MergeSplitService:
    def __init__(self) -> None:
        self.crop_service = CropService()
        self.boundary_scan_rows = 12
        self.boundary_foreground_ratio = 0.03
        self.background_color_tolerance = 12
        self.strip_diff_threshold = 30.0

    def prepare_processing_inputs(
        self,
        site_code: str,
        raw_dir: Path,
        stitched_dir: Path,
    ) -> dict[str, object]:
        files = sorted(path for path in raw_dir.glob("*") if path.is_file())
        if not files:
            return {
                "processing_input_dir": str(raw_dir),
                "merge_enabled": False,
                "prepared_files": [],
                "merged_groups": [],
            }

        if site_code not in settings.merge_split_sites:
            self._copy_passthrough(files, stitched_dir)
            return {
                "processing_input_dir": str(stitched_dir),
                "merge_enabled": False,
                "prepared_files": [str(stitched_dir / path.name) for path in files],
                "merged_groups": [],
            }

        groups = self._build_merge_groups(files, site_code)
        prepared_files: list[str] = []
        merged_groups: list[dict[str, object]] = []

        for group in groups:
            if len(group) == 1:
                target = stitched_dir / group[0].name
                shutil.copy2(group[0], target)
                prepared_files.append(str(target))
                continue

            merged_path = stitched_dir / f"{'_merge_'.join(path.stem for path in group)}.jpg"
            self._merge_group(group, merged_path)
            prepared_files.append(str(merged_path))
            merged_groups.append(
                {
                    "inputs": [str(path) for path in group],
                    "output": str(merged_path),
                }
            )

        return {
            "processing_input_dir": str(stitched_dir),
            "merge_enabled": True,
            "prepared_files": prepared_files,
            "merged_groups": merged_groups,
        }

    def _copy_passthrough(self, files: list[Path], stitched_dir: Path) -> None:
        for source in files:
            shutil.copy2(source, stitched_dir / source.name)

    def _build_merge_groups(self, files: list[Path], site_code: str) -> list[list[Path]]:
        groups: list[list[Path]] = []
        index = 0

        while index < len(files):
            current_group = [files[index]]
            while index + 1 < len(files):
                current = current_group[-1]
                following = files[index + 1]
                should_merge = self._should_merge_pair(current, following, site_code)
                if not should_merge:
                    break
                current_group.append(following)
                index += 1
            groups.append(current_group)
            index += 1

        return groups

    def _should_merge_pair(self, current_path: Path, following_path: Path, site_code: str) -> bool:
        if site_code not in settings.merge_split_sites:
            return False

        current = self.crop_service._read_image(current_path)
        following = self.crop_service._read_image(following_path)
        if current is None or following is None:
            return False

        current_height, current_width = current.shape[:2]
        following_height, following_width = following.shape[:2]

        if current_width != following_width:
            return False
        if current_height < settings.min_process_height or following_height < settings.min_process_height:
            return False
        if not self._content_touches_bottom(current):
            return False
        if not self._content_touches_top(following):
            return False
        strip_difference = self._boundary_strip_difference(current, following)
        if strip_difference <= self.strip_diff_threshold:
            return True

        return self._backgrounds_match(current, following) and strip_difference <= (self.strip_diff_threshold + 8.0)

    def _content_touches_bottom(self, image: np.ndarray) -> bool:
        rows = image[-self.boundary_scan_rows :, :, :]
        return self._foreground_ratio(rows) >= self.boundary_foreground_ratio

    def _content_touches_top(self, image: np.ndarray) -> bool:
        rows = image[: self.boundary_scan_rows, :, :]
        return self._foreground_ratio(rows) >= self.boundary_foreground_ratio

    def _foreground_ratio(self, rows: np.ndarray) -> float:
        gray = cv2.cvtColor(rows, cv2.COLOR_BGR2GRAY)
        foreground_mask = gray < settings.trim_threshold
        return float(np.count_nonzero(foreground_mask) / max(foreground_mask.size, 1))

    def _backgrounds_match(self, current: np.ndarray, following: np.ndarray) -> bool:
        current_background = self._estimate_background_color(current)
        following_background = self._estimate_background_color(following)
        return bool(
            np.max(
                np.abs(
                    current_background.astype(np.int16) - following_background.astype(np.int16)
                )
            )
            <= self.background_color_tolerance
        )

    def _estimate_background_color(self, image: np.ndarray) -> np.ndarray:
        border = max(12, min(image.shape[:2]) // 40)
        samples = np.concatenate(
            [
                image[:border, :, :].reshape(-1, 3),
                image[-border:, :, :].reshape(-1, 3),
                image[:, :border, :].reshape(-1, 3),
                image[:, -border:, :].reshape(-1, 3),
            ],
            axis=0,
        )
        return np.median(samples, axis=0).astype(np.uint8)

    def _boundary_strip_difference(self, current: np.ndarray, following: np.ndarray) -> float:
        current_strip = current[-min(self.boundary_scan_rows * 10, current.shape[0]) :, :, :]
        following_strip = following[: min(self.boundary_scan_rows * 10, following.shape[0]), :, :]
        height = min(current_strip.shape[0], following_strip.shape[0])
        if height <= 0:
            return float("inf")

        current_strip = current_strip[-height:, :, :]
        following_strip = following_strip[:height, :, :]
        target_width = 128
        current_strip = cv2.resize(current_strip, (target_width, height), interpolation=cv2.INTER_AREA)
        following_strip = cv2.resize(following_strip, (target_width, height), interpolation=cv2.INTER_AREA)
        return float(
            np.mean(np.abs(current_strip.astype(np.float32) - following_strip.astype(np.float32)))
        )

    def _merge_group(self, paths: list[Path], target_path: Path) -> None:
        images: list[np.ndarray] = []
        for path in paths:
            image = self.crop_service._read_image(path)
            if image is None:
                raise RuntimeError(f"failed to read image for merge: {path}")
            images.append(image)

        merged = np.vstack(images)
        self.crop_service._write_image(target_path, merged)
