"""
Logging utility for Trashformer robot.

Provides consistent logging configuration across all modules.
Logs to both file and console with timestamps and severity levels.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class RobotLogger:
    """Centralized logging configuration for the robot."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure one logger configuration."""
        if cls._instance is None:
            cls._instance = super(RobotLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger (only once)."""
        if not RobotLogger._initialized:
            self.setup_logging()
            RobotLogger._initialized = True
    
    def setup_logging(self, log_level=logging.INFO, log_to_file=True):
        """
        Configure logging for the entire application.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to file in addition to console
        """
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"robot_{timestamp}.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Console handler (always enabled)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_to_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            logging.info(f"Logging to file: {log_file}")


def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Starting arm controller")
    """
    # Ensure logging is configured
    RobotLogger()
    return logging.getLogger(name)


def set_log_level(level):
    """
    Change the logging level for all loggers.
    
    Args:
        level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.getLogger().setLevel(level)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)


# Convenience function for quick setup
def setup_logging(level=logging.INFO, log_to_file=True):
    """
    Quick setup function for logging.
    
    Args:
        level: Logging level
        log_to_file: Whether to log to file
    """
    logger = RobotLogger()
    logger.setup_logging(level, log_to_file)


if __name__ == "__main__":
    # Test the logger
    setup_logging(logging.DEBUG)
    
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")