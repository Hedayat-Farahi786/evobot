"""
Logging utilities for the trading system
"""
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
import json

from config.settings import config


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'trade_id'):
            log_obj['trade_id'] = record.trade_id
        if hasattr(record, 'signal_id'):
            log_obj['signal_id'] = record.signal_id
        if hasattr(record, 'symbol'):
            log_obj['symbol'] = record.symbol
        if hasattr(record, 'extra_data'):
            log_obj['data'] = record.extra_data
            
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    name: str = "evobot",
    level: Optional[str] = None,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging with file and console handlers
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        
    Returns:
        Configured logger
    """
    level = level or config.logging.log_level
    log_dir = log_dir or config.logging.log_dir
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure the ROOT "evobot" logger so all child loggers inherit handlers
    root_logger = logging.getLogger("evobot")
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Get the specific logger requested
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers - check root logger
    if root_logger.handlers:
        return logger
    
    # Console handler with colors - add to ROOT logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    console_handler.setFormatter(ColoredFormatter(console_format))
    root_logger.addHandler(console_handler)
    
    # System log file handler
    system_log_path = os.path.join(log_dir, config.logging.system_log_file)
    system_handler = RotatingFileHandler(
        system_log_path,
        maxBytes=config.logging.max_log_size_mb * 1024 * 1024,
        backupCount=config.logging.backup_count
    )
    system_handler.setLevel(logging.DEBUG)
    system_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(system_handler)
    
    # Error log file handler
    error_log_path = os.path.join(log_dir, config.logging.error_log_file)
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=config.logging.max_log_size_mb * 1024 * 1024,
        backupCount=config.logging.backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    return logger


def get_trade_logger() -> logging.Logger:
    """Get dedicated trade logger"""
    log_dir = config.logging.log_dir
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("evobot.trades")
    
    if not logger.handlers:
        trade_log_path = os.path.join(log_dir, config.logging.trade_log_file)
        handler = RotatingFileHandler(
            trade_log_path,
            maxBytes=config.logging.max_log_size_mb * 1024 * 1024,
            backupCount=config.logging.backup_count
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def log_trade_event(
    event: str,
    trade_id: str,
    symbol: str,
    data: dict = None,
    level: str = "INFO"
):
    """
    Log a trade event with structured data
    
    Args:
        event: Event type (OPENED, CLOSED, TP_HIT, etc.)
        trade_id: Trade identifier
        symbol: Trading symbol
        data: Additional event data
        level: Log level
    """
    logger = get_trade_logger()
    extra = {
        'trade_id': trade_id,
        'symbol': symbol,
        'extra_data': {
            'event': event,
            **(data or {})
        }
    }
    
    log_func = getattr(logger, level.lower())
    log_func(f"Trade Event: {event}", extra=extra)


def log_signal_event(
    event: str,
    signal_id: str,
    symbol: str,
    data: dict = None,
    level: str = "INFO"
):
    """Log a signal event"""
    logger = logging.getLogger("evobot.signals")
    extra = {
        'signal_id': signal_id,
        'symbol': symbol,
        'extra_data': {
            'event': event,
            **(data or {})
        }
    }
    
    log_func = getattr(logger, level.lower())
    log_func(f"Signal Event: {event}", extra=extra)
