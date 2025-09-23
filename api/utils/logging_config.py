"""
Logging configuration utilities
"""

import logging
import sys
from datetime import datetime

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup a logger with consistent formatting"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger if not already added
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger