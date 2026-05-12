"""Logging helpers for PropertyHunter."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging once.

    Parameters
    ----------
    level:
        Standard library logging level name, for example ``INFO`` or ``DEBUG``.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
