from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, replace
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProgressEntry:
    job_id: str
    label: str
    status: str = "pending"
    stage: str = "pending"
    current: int = 0
    total: int = 0
    success_count: int = 0
    failed_count: int = 0
    message: str = ""
    error_summary: str = ""
    updated_at: str = ""


class ProgressRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, ProgressEntry] = {}

    def register(self, job_id: str, label: str) -> None:
        with self._lock:
            self._entries[job_id] = ProgressEntry(
                job_id=job_id,
                label=label,
                updated_at=self._now(),
            )

    def update(self, job_id: str, **changes: object) -> None:
        with self._lock:
            entry = self._entries.get(job_id)
            if entry is None:
                return
            self._entries[job_id] = replace(entry, updated_at=self._now(), **changes)

    def snapshot(self) -> list[ProgressEntry]:
        with self._lock:
            return sorted(self._entries.values(), key=lambda item: item.label.lower())

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M:%S")


class DisplayManager:
    def __init__(self, registry: ProgressRegistry) -> None:
        self.registry = registry

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def log_summary(self, job_id: str) -> None:
        entry = next((item for item in self.registry.snapshot() if item.job_id == job_id), None)
        if entry is None:
            return
        logger.info(self._format_entry(entry))

    def _format_entry(self, entry: ProgressEntry) -> str:
        progress = f"{entry.current}/{entry.total}" if entry.total else "-"
        message = entry.error_summary or entry.message or "-"
        return (
            f"[{entry.label}] {entry.status} | {entry.stage} | "
            f"progress={progress} | success={entry.success_count} | failed={entry.failed_count} | {message}"
        )


progress_registry = ProgressRegistry()
display_manager = DisplayManager(progress_registry)
