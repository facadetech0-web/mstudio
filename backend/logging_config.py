import os
import re
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from backend.config import settings

LOGS_DIR = Path(settings.LOGS_DIR)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class SensitiveDataFilter(logging.Filter):
    """Filters out any potential API keys from log messages."""
    API_KEY_PATTERN = re.compile(r'(sk-or-v1-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_-]{10,})')

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.API_KEY_PATTERN.sub("[REDACTED_API_KEY]", record.msg)
        return True

def setup_logger(name: str, log_filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addFilter(SensitiveDataFilter())

    if not logger.handlers:
        file_path = LOGS_DIR / log_filename
        file_handler = RotatingFileHandler(file_path, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

api_logger = setup_logger("api", "api.log")
ai_logger = setup_logger("ai", "ai.log")
worker_logger = setup_logger("worker", "worker.log")
generation_logger = setup_logger("generation", "generation.log")
