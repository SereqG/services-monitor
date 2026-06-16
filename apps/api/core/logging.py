from __future__ import annotations

import logging
import sys
from pathlib import Path

from core.config import settings

_FMT = "%(asctime)s | %(levelname)s | %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("services_monitor")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    formatter = logging.Formatter(_FMT, datefmt=_DATEFMT)

    # stdout is always available so container runtimes can collect logs.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # A file handler is opt-in via LOG_DIR and never written inside the source tree.
    if settings.log_dir:
        log_dir = Path(settings.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "services_monitor.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = _build_logger()
