"""
Logging configuration for LuggageIQ
"""

import logging
import os
from datetime import datetime
from typing import Optional

from .config import Config


def setup_logger(name: str = 'luggageiq', level: Optional[str] = None) -> logging.Logger:
    """
    Set up logger with file and console handlers
    
    Args:
        name: Logger name
        level: Logging level (default from config)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    log_level = level or Config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_timestamp() -> str:
    """Get current timestamp for logging"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
