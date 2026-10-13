"""Shared structured logger for the test suite.

Writes to both the console and a per-run log file under logs/, so a failure
can be diagnosed from the log alone without re-running the suite.
"""

import logging
import os
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, f"run_{datetime.now():%Y%m%d_%H%M%S}.log")

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured

    if not _configured:
        os.makedirs(_LOG_DIR, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            handlers=[
                logging.FileHandler(_LOG_FILE, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        _configured = True

    return logging.getLogger(name)
