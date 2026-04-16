from __future__ import annotations

import logging
from app.core.config import settings


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    settings.final_output_root.mkdir(parents=True, exist_ok=True)
    log_path = settings.final_output_root / "service.log"

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
