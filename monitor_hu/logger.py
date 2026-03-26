import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "monitor.log"

def get_logger(module_name: str):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s | [%(levelname)s] | %(name)s | %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Silencia logs externos ruidosos
    logging.getLogger("WDM").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)

    return logger