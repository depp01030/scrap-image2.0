from __future__ import annotations

import os
import sys
import threading
from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True)
class ProgressEntry:
    job_id: str
    label: str
    status: str = "PENDING"
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
            return list(self._entries.values())

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M:%S")


class DisplayManager:
    def __init__(self, registry: ProgressRegistry, refresh_interval: float = 0.5) -> None:
        self.registry = registry
        self.refresh_interval = refresh_interval
        self._enabled = sys.stdout.isatty()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self._enabled:
            return
        print("Welcome to scrap-image2.0 local service")
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="cli-display", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        if not self._enabled:
            return
        self._stop_event.set()
        with self._lock:
            if self._thread:
                self._thread.join(timeout=2.0)
                self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(self.refresh_interval):
            self.render()

    def render(self) -> None:
        if not self._enabled:
            return
        entries = self.registry.snapshot()
        if not entries:
            return
        os.system("cls")
        print("scrap-image2.0 local service")
        print("==================================================")
        for entry in entries:
            print(self._format_entry(entry))

    def _format_entry(self, entry: ProgressEntry) -> str:
        if entry.status == "DONE":
            return (
                f"[DONE]    {entry.label} | {entry.message or self._build_progress(entry)}"
            )
        if entry.status == "FAILED":
            short_error = entry.error_summary or "Error"
            return f"[FAILED]  {entry.label} | {short_error}"
        return (
            f"[RUNNING] {entry.label} | {entry.stage} | {self._build_progress(entry)}"
            f" | ok={entry.success_count} fail={entry.failed_count}"
        )

    def _build_progress(self, entry: ProgressEntry) -> str:
        if entry.total:
            return f"{entry.current}/{entry.total}"
        return "-"


progress_registry = ProgressRegistry()
display_manager = DisplayManager(progress_registry)
