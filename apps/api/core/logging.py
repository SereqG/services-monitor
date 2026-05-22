from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG_FILE = Path(__file__).parent.parent / "log.log"
_FMT = "%(asctime)s | %(levelname)s | %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("services_monitor")
    if logger.handlers:
        return logger

    if not _LOG_FILE.exists():
        _LOG_FILE.touch()

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(_FMT, datefmt=_DATEFMT)

    file_handler = logging.FileHandler(_LOG_FILE)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


logger = _build_logger()
