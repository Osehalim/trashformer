"""
Logging utility for Trashformer robot.

Logs to console and (optionally) a file with timestamped filenames.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


class RobotLogger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RobotLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not RobotLogger._initialized:
            self.setup_logging()
            RobotLogger._initialized = True

    def setup_logging(self, log_level=logging.INFO, log_to_file=True):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"robot_{timestamp}.log"

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        if log_to_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            logging.info(f"Logging to file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    RobotLogger()
    return logging.getLogger(name)


def set_log_level(level):
    logging.getLogger().setLevel(level)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)


def setup_logging(level=logging.INFO, log_to_file=True):
    logger = RobotLogger()
    logger.setup_logging(level, log_to_file)