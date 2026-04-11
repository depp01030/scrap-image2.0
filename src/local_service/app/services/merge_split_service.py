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

        site_config = settings.merge_split_sites.get(site_code)
        if site_config is None or not site_config.enabled:
            self._copy_passthrough(files, stitched_dir)
            return {
                "processing_input_dir": str(stitched_dir),
                "merge_enabled": False,
                "prepared_files": [str(stitched_dir / path.name) for path in files],
                "merged_groups": [],
            }

        prepared_files: list[str] = []
        merged_groups: list[dict[str, object]] = []
        site_config = settings.merge_split_sites.get(site_code)
        index = 0
        while index < len(files):
            current = files[index]
            forced_group = self._match_forced_group(files, index, site_config.force_merge_groups if site_config else [])
            if forced_group is not None:
                group_files, group_label = forced_group
                merged_path = stitched_dir / f"{group_label}.jpg"
                self._merge_group(group_files, merged_path)
                prepared_files.append(str(merged_path))
                merged_groups.append(
                    {
                        "inputs": [str(path) for path in group_files],
                        "output": str(merged_path),
                    }
                )
                index += len(group_files)
                continue

            if index + 1 < len(files):
                following = files[index + 1]
                if self._should_merge_pair(current, following, site_code):
                    merged_path = stitched_dir / f"{current.stem}_merge_{following.stem}.jpg"
                    self._merge_pair(current, following, merged_path)
                    prepared_files.append(str(merged_path))
                    merged_groups.append(
                        {
                            "inputs": [str(current), str(following)],
                            "output": str(merged_path),
                        }
                    )
                    index += 2
                    continue

            target = stitched_dir / current.name
            shutil.copy2(current, target)
            prepared_files.append(str(target))
            index += 1

        return {
            "processing_input_dir": str(stitched_dir),
            "merge_enabled": True,
            "prepared_files": prepared_files,
            "merged_groups": merged_groups,
        }

    def _copy_passthrough(self, files: list[Path], stitched_dir: Path) -> None:
        for source in files:
            shutil.copy2(source, stitched_dir / source.name)

    def _should_merge_pair(self, current_path: Path, following_path: Path, site_code: str) -> bool:
        site_config = settings.merge_split_sites.get(site_code)
        if site_config is None or not site_config.enabled:
            return False
        if self._is_forced_merge_pair(current_path, following_path, site_config.force_merge_groups):
            return True

        current = self.crop_service._read_image(current_path)
        following = self.crop_service._read_image(following_path)
        if current is None or following is None:
            return False

        current_height, current_width = current.shape[:2]
        following_height, following_width = following.shape[:2]

        if current_width != following_width:
            return False
        if current_height < site_config.min_primary_height:
            return False
        if following_height > site_config.max_following_height:
            return False

        if not self._content_touches_bottom(current, site_config.boundary_scan_rows, site_config.boundary_foreground_ratio):
            return False
        if not self._content_touches_top(following, site_config.boundary_scan_rows, site_config.boundary_foreground_ratio):
            return False
        if not self._backgrounds_match(current, following, site_config.background_color_tolerance):
            return False

        return True

    def _is_forced_merge_pair(
        self,
        current_path: Path,
        following_path: Path,
        force_merge_groups: list[list[str]],
    ) -> bool:
        current_name = current_path.name.lower()
        following_name = following_path.name.lower()
        for group in force_merge_groups:
            if len(group) != 2:
                continue
            expected_current = group[0].strip().lower()
            expected_following = group[1].strip().lower()
            if current_name == expected_current and following_name == expected_following:
                return True
        return False

    def _match_forced_group(
        self,
        files: list[Path],
        start_index: int,
        force_merge_groups: list[list[str]],
    ) -> tuple[list[Path], str] | None:
        if not force_merge_groups:
            return None

        remaining = files[start_index:]
        for group in force_merge_groups:
            if len(group) < 2 or len(group) > len(remaining):
                continue
            normalized_group = [name.strip().lower() for name in group]
            candidate = remaining[: len(group)]
            candidate_names = [path.name.lower() for path in candidate]
            if candidate_names == normalized_group:
                label = "_merge_".join(path.stem for path in candidate)
                return candidate, label
        return None

    def _content_touches_bottom(self, image: np.ndarray, scan_rows: int, min_ratio: float) -> bool:
        rows = image[-scan_rows:, :, :]
        return self._foreground_ratio(rows) >= min_ratio

    def _content_touches_top(self, image: np.ndarray, scan_rows: int, min_ratio: float) -> bool:
        rows = image[:scan_rows, :, :]
        return self._foreground_ratio(rows) >= min_ratio

    def _foreground_ratio(self, rows: np.ndarray) -> float:
        gray = cv2.cvtColor(rows, cv2.COLOR_BGR2GRAY)
        foreground_mask = gray < settings.trim_threshold
        return float(np.count_nonzero(foreground_mask) / max(foreground_mask.size, 1))

    def _backgrounds_match(self, current: np.ndarray, following: np.ndarray, tolerance: int) -> bool:
        current_background = self._estimate_background_color(current)
        following_background = self._estimate_background_color(following)
        return bool(np.max(np.abs(current_background.astype(np.int16) - following_background.astype(np.int16))) <= tolerance)

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

    def _merge_pair(self, current_path: Path, following_path: Path, target_path: Path) -> None:
        current = self.crop_service._read_image(current_path)
        following = self.crop_service._read_image(following_path)
        if current is None or following is None:
            raise RuntimeError(f"failed to read images for merge: {current_path}, {following_path}")

        merged = np.vstack([current, following])
        self.crop_service._write_image(target_path, merged)

    def _merge_group(self, paths: list[Path], target_path: Path) -> None:
        images: list[np.ndarray] = []
        for path in paths:
            image = self.crop_service._read_image(path)
            if image is None:
                raise RuntimeError(f"failed to read image for merge: {path}")
            images.append(image)

        merged = np.vstack(images)
        self.crop_service._write_image(target_path, merged)
