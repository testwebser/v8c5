"""
Logging configuration for the Stock Bot
Provides consistent logging across all modules
"""
import logging
import sys
from config import Config


def setup_logger(name: str = 'StockBot') -> logging.Logger:
    """
    Setup logger with consistent formatting
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Format: [2025-10-20 10:30:45] INFO - Message
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
