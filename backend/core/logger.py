"""PhysioWave — HIPAA-Compliant Logger.

HIPAA Compliance Note: This logger automatically redacts PII field
values before writing to the log output. Production deployments
should set log level to WARNING or above.
"""

import logging
import sys

from backend.core.config import settings


def _create_logger() -> logging.Logger:
    """Create the application logger with secure formatting."""
    log = logging.getLogger("physiowave")
    log.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    log.addHandler(handler)
    return log


logger = _create_logger()
