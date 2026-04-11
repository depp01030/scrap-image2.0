from __future__ import annotations

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.config import settings


class DownloadService:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(30.0, connect=15.0)

    def download_images(self, image_urls: list[str], raw_dir: Path) -> dict[str, object]:
        downloaded_files: list[str] = []
        failures: list[dict[str, str]] = []

        with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
            for index, image_url in enumerate(image_urls, start=1):
                try:
                    target_path = self._build_target_path(raw_dir, index, image_url)
                    self._download_with_retry(client, image_url, target_path)
                    downloaded_files.append(str(target_path))
                except Exception as exc:
                    failures.append(
                        {
                            "url": image_url,
                            "error": str(exc),
                        }
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

