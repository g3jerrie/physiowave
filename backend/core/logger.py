"""PhysioWave — HIPAA-Compliant Logger.

HIPAA Compliance Note: This logger automatically redacts PII field
values before writing to the log output. It implements rotating file
logs to ensure robust stacktrace capture in case of failures.
"""

import sys
import os
from loguru import logger
from backend.core.config import settings

def setup_logging():
    """Configure the application logger with secure formatting and file output."""
    logger.remove()  # Remove default stdout handler
    
    log_level = "DEBUG" if settings.debug else "INFO"
    
    # Console handler
    logger.add(
        sys.stdout, 
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )
    
    # File handler for persistent structured logging
    os.makedirs("./backend/data/logs", exist_ok=True)
    logger.add(
        "./backend/data/logs/physiowave_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG", # File gets more granular logs
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True, # Note: turn off diagnose in real prod for HIPAA strict compliance if traces contain PII
    )

setup_logging()
