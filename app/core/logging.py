import logging
import sys

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger("app")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")
