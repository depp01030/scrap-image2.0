from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


logger = logging.getLogger(__name__)


class CropService:
    def crop_directory(self, raw_dir: Path, processed_dir: Path, site_code: str | None = None) -> dict[str, object]:
        processed_files: list[str] = []
        skipped_files: list[str] = []
        split_files: list[str] = []

        for raw_file in sorted(raw_dir.glob("*")):
            if not raw_file.is_file():
                continue

            output_paths = self.crop_single_image(raw_file, processed_dir, site_code=site_code)
            if not output_paths:
                skipped_files.append(str(raw_file))
                continue

            if len(output_paths) == 1:
                processed_files.append(str(output_paths[0]))
            else:
                split_files.extend(str(path) for path in output_paths)

        return {
            "processed_count": len(processed_files) + len(split_files),
            "skipped_count": len(skipped_files),
            "processed_files": processed_files,
            "split_files": split_files,
            "skipped_files": skipped_files,
        }

    def crop_single_image(
        self,
        source_path: Path,
        processed_dir: Path,
        site_code: str | None = None,
    ) -> list[Path]:
        image = self._read_image(source_path)
        if image is None:
            return []
        if source_path.suffix.lower() in {".gif"}:
            return []

        height, width = image.shape[:2]
        if width < settings.min_process_width or height < settings.min_process_height:
            return []

        cropped = self._trim_white_border(image)
        segments = self._split_by_content_groups(cropped)
        if self._should_use_band_refine_only(source_path, site_code):
            band_segments: list[np.ndarray] = []
            for segment in segments:
                band_segments.extend(self._refine_segment_by_bands(segment))
            return self._write_output_segments(source_path, processed_dir, band_segments or segments)

        refined_segments: list[np.ndarray] = []
        for segment in segments:
            refined = self._refine_segment_by_bands(segment)
            for refined_segment in refined:
                refined_segments.extend(self._recursive_full_width_split(refined_segment, depth=0))
        segments = refined_segments or segments

        return self._write_output_segments(source_path, processed_dir, segments)

    def _should_use_band_refine_only(self, source_path: Path, site_code: str | None) -> bool:
        if site_code != "veryyou":
            return False
        return "_merge_" not in source_path.stem.lower()

    def _write_output_segments(
        self,
        source_path: Path,
        processed_dir: Path,
        segments: list[np.ndarray],
    ) -> list[Path]:
        output_paths: list[Path] = []
        stem = source_path.stem
        suffix = source_path.suffix or ".jpg"

        if len(segments) == 1:
            target_path = processed_dir / f"{stem}{suffix}"
            self._write_image(target_path, segments[0])
            output_paths.append(target_path)
            return output_paths

        for index, segment in enumerate(segments, start=1):
            target_path = processed_dir / f"{stem}_part{index:02d}{suffix}"
            self._write_image(target_path, segment)
            output_paths.append(target_path)
        return output_paths

    def _trim_white_border(self, image: np.ndarray) -> np.ndarray:
        content_mask = self._build_content_mask(image)
        coordinates = cv2.findNonZero(content_mask)
        if coordinates is None:
            return image

        x, y, w, h = cv2.boundingRect(coordinates)
        return image[y : y + h, x : x + w]

    def _build_content_mask(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshold = settings.trim_threshold
        content_mask = np.where(gray < threshold, 255, 0).astype(np.uint8)

        kernel = np.ones((3, 3), np.uint8)
        content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_OPEN, kernel)
        content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_CLOSE, kernel)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(content_mask, connectivity=8)
        filtered = np.zeros_like(content_mask)

        for label in range(1, num_labels):
            area = stats[label, cv2.CC_STAT_AREA]
            if area < settings.min_component_area:
                continue
            filtered[labels == label] = 255

        if cv2.countNonZero(filtered) == 0:
            return content_mask
        return filtered

    def _split_by_content_groups(self, image: np.ndarray) -> list[np.ndarray]:
        height, width = image.shape[:2]
        content_mask = self._build_content_mask(image)
        merge_kernel = np.ones((settings.vertical_merge_gap_rows, 3), np.uint8)
        merged_mask = cv2.dilate(content_mask, merge_kernel, iterations=1)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(merged_mask, connectivity=8)
        boxes: list[tuple[int, int, int, int]] = []
        for label in range(1, num_labels):
            area = stats[label, cv2.CC_STAT_AREA]
            if area < settings.min_component_area:
                continue
            x = stats[label, cv2.CC_STAT_LEFT]
            y = stats[label, cv2.CC_STAT_TOP]
            w = stats[label, cv2.CC_STAT_WIDTH]
            h = stats[label, cv2.CC_STAT_HEIGHT]
            if h < settings.min_segment_height:
                continue
            boxes.append((x, y, w, h))

        boxes.sort(key=lambda box: box[1])
        if not boxes:
            return [image]

        gap_candidates: list[tuple[int, int]] = []
        for index in range(len(boxes) - 1):
            _, y1, _, h1 = boxes[index]
            _, y2, _, _ = boxes[index + 1]
            gap = y2 - (y1 + h1)
            if gap >= settings.min_split_gap_rows:
                gap_candidates.append((index, gap))

        selected_gap_indexes = {
            index
            for index, _ in sorted(
                gap_candidates,
                key=lambda item: item[1],
                reverse=True,
            )[: max(settings.max_split_parts - 1, 0)]
        }

        grouped_boxes: list[tuple[int, int]] = []
        group_start = boxes[0][1]
        current_bottom = boxes[0][1] + boxes[0][3]

        for index, (_, y, _, h) in enumerate(boxes[:-1]):
            current_bottom = max(current_bottom, y + h)
            if index in selected_gap_indexes:
                grouped_boxes.append((group_start, current_bottom))
                next_y = boxes[index + 1][1]
                group_start = next_y
                current_bottom = next_y + boxes[index + 1][3]

        last_y = boxes[-1][1]
        last_h = boxes[-1][3]
        current_bottom = max(current_bottom, last_y + last_h)
        grouped_boxes.append((group_start, current_bottom))

        segments: list[np.ndarray] = []
        for top, bottom in grouped_boxes:
            top = max(top, 0)
            bottom = min(bottom, height)
            if bottom - top < settings.min_segment_height:
                continue
            segment = image[top:bottom, :]
            segment = self._trim_white_border(segment)
            segments.append(segment)

        return segments or [image]

    def _recursive_full_width_split(self, image: np.ndarray, depth: int) -> list[np.ndarray]:
        if depth >= settings.recursive_split_max_depth:
            return [image]

        split_segments = self._split_by_full_width_blank_bands(image)
        if len(split_segments) <= 1 and self._is_white_background_scene(image):
            split_segments = self._split_by_background_blank_bands(image)
        if len(split_segments) <= 1:
            return [image]

        refined: list[np.ndarray] = []
        for segment in split_segments:
            refined.extend(self._recursive_full_width_split(segment, depth + 1))
        return refined

    def _split_by_full_width_blank_bands(self, image: np.ndarray) -> list[np.ndarray]:
        height, width = image.shape[:2]
        if height < settings.min_segment_height * 2:
            return [image]

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blank_rows = (gray >= settings.split_row_threshold).sum(axis=1) / max(width, 1)

        blank_ranges: list[tuple[int, int]] = []
        start: int | None = None
        for y, ratio in enumerate(blank_rows):
            if ratio >= settings.full_width_blank_ratio and start is None:
                start = y
            elif ratio < settings.full_width_blank_ratio and start is not None:
                blank_ranges.append((start, y - 1))
                start = None
        if start is not None:
            blank_ranges.append((start, height - 1))

        cut_positions = []
        for blank_start, blank_end in blank_ranges:
            gap_height = blank_end - blank_start + 1
            if gap_height >= settings.full_width_min_gap_rows:
                cut_positions.append((blank_start + blank_end) // 2)

        if not cut_positions:
            return [image]

        segments: list[np.ndarray] = []
        top = 0
        for cut_y in cut_positions:
            if cut_y - top >= settings.min_segment_height:
                segment = image[top:cut_y, :]
                segment = self._trim_white_border(segment)
                segments.append(segment)
            top = cut_y + 1

        if height - top >= settings.min_segment_height:
            segment = image[top:height, :]
            segment = self._trim_white_border(segment)
            segments.append(segment)

        return segments or [image]

    def _has_meaningful_background_separated_content(
        self,
        image: np.ndarray,
        background_color: np.ndarray,
    ) -> bool:
        diff = np.abs(image.astype(np.int16) - background_color.astype(np.int16)).max(axis=2)
        foreground_mask = diff > settings.background_diff_threshold
        foreground_ratio = np.count_nonzero(foreground_mask) / max(image.shape[0] * image.shape[1], 1)
        active_row_ratio = (
            ((foreground_mask.sum(axis=1) / max(image.shape[1], 1)) > 0.02).mean()
            if image.shape[0] > 0
            else 0
        )
        return foreground_ratio >= 0.03 or active_row_ratio >= 0.2

    def _split_by_background_blank_bands(self, image: np.ndarray) -> list[np.ndarray]:
        height, width = image.shape[:2]
        if height < settings.min_segment_height * 2:
            return [image]

        border_size = max(20, min(height, width) // 40)
        background_color = self._estimate_background_color(image)
        background_diff = np.abs(image.astype(np.int16) - background_color.astype(np.int16)).max(axis=2)
        background_rows = (background_diff <= settings.background_diff_threshold).sum(axis=1) / max(width, 1)

        min_gap_rows = max(20, settings.min_split_gap_rows // 3)
        blank_ranges: list[tuple[int, int]] = []
        start: int | None = None
        for y, ratio in enumerate(background_rows):
            if ratio >= 0.95 and start is None:
                start = y
            elif ratio < 0.95 and start is not None:
                blank_ranges.append((start, y - 1))
                start = None
        if start is not None:
            blank_ranges.append((start, height - 1))

        cut_positions: list[int] = []
        for blank_start, blank_end in blank_ranges:
            gap_height = blank_end - blank_start + 1
            # Ignore outer margins; only use interior background bands as split points.
            if blank_start <= border_size or blank_end >= height - border_size:
                continue
            if gap_height >= min_gap_rows:
                cut_positions.append((blank_start + blank_end) // 2)

        if not cut_positions:
            return [image]

        segments: list[np.ndarray] = []
        top = 0
        for cut_y in cut_positions:
            if cut_y - top >= settings.min_segment_height:
                segment = image[top:cut_y, :]
                segment = self._trim_white_border(segment)
                if self._has_meaningful_background_separated_content(segment, background_color):
                    segments.append(segment)
            top = cut_y + 1

        if height - top >= settings.min_segment_height:
            segment = image[top:height, :]
            segment = self._trim_white_border(segment)
            if self._has_meaningful_background_separated_content(segment, background_color):
                segments.append(segment)

        return segments or [image]

    def _is_white_background_scene(self, image: np.ndarray) -> bool:
        background_color = self._estimate_background_color(image)
        white_diff = np.abs(background_color.astype(np.int16) - 255).max()
        return bool(white_diff <= settings.white_background_max_diff)

    def _estimate_background_color(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        border_size = max(20, min(height, width) // 40)
        border_samples = np.concatenate(
            [
                image[:border_size, :, :].reshape(-1, 3),
                image[-border_size:, :, :].reshape(-1, 3),
                image[:, :border_size, :].reshape(-1, 3),
                image[:, -border_size:, :].reshape(-1, 3),
            ],
            axis=0,
        )
        return np.median(border_samples, axis=0)

    def _refine_segment_by_bands(self, image: np.ndarray) -> list[np.ndarray]:
        height, width = image.shape[:2]
        if height < settings.min_segment_height * 2:
            return [image]

        content_mask = self._build_content_mask(image)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
        band_mask = cv2.dilate(content_mask, kernel, iterations=1)
        row_density = np.count_nonzero(band_mask, axis=1) / max(width, 1)
        content_rows = row_density > settings.band_row_ratio_threshold

        bands: list[tuple[int, int]] = []
        start: int | None = None
        for y, has_content in enumerate(content_rows):
            if has_content and start is None:
                start = y
            elif not has_content and start is not None:
                if y - start >= settings.min_band_height:
                    bands.append((start, y))
                start = None
        if start is not None and height - start >= settings.min_band_height:
            bands.append((start, height))

        if len(bands) <= 1:
            return [image]

        segments: list[np.ndarray] = []
        for top, bottom in bands:
            segment = image[top:bottom, :]
            segment = self._trim_white_border(segment)
            seg_h, seg_w = segment.shape[:2]
            if seg_h < settings.min_segment_height or seg_w < settings.min_process_width:
                continue
            segments.append(segment)

        return segments or [image]

    def _read_image(self, source_path: Path) -> np.ndarray | None:
        try:
            if source_path.suffix.lower() == ".webp":
                with Image.open(source_path) as probe_image:
                    if getattr(probe_image, "is_animated", False):
                        logger.warning("Skipping animated WebP file: %s", source_path.name)
                        return None

            data = np.fromfile(str(source_path), dtype=np.uint8)
            if data.size == 0:
                return None
            decoded = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if decoded is not None:
                return decoded
        except Exception:
            pass

        try:
            with Image.open(source_path) as pil_image:
                if getattr(pil_image, "is_animated", False):
                    logger.warning("Skipping animated image file: %s", source_path.name)
                    return None
                rgb_image = pil_image.convert("RGB")
                return cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
        except (UnidentifiedImageError, OSError):
            return None

    def _write_image(self, target_path: Path, image: np.ndarray) -> None:
        suffix = target_path.suffix.lower() or ".jpg"
        extension = ".jpg" if suffix == ".jpg" else suffix
        success, encoded = cv2.imencode(extension, image)
        if not success:
            raise RuntimeError(f"failed to encode image for {target_path}")
        encoded.tofile(str(target_path))
