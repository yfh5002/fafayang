# -*- coding: utf-8 -*-
"""
HJSYSTEM 统一日志系统
提供标准化的日志记录功能
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from backend.config import LOG_DIR, LOG_LEVEL

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)

# 创建日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 创建格式化器
formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，通常使用 __name__
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（带轮转）
    log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 创建应用全局日志记录器
app_logger = get_logger("hjsystem")
api_logger = get_logger("hjsystem.api")
db_logger = get_logger("hjsystem.database")
auth_logger = get_logger("hjsystem.auth")
excel_logger = get_logger("hjsystem.excel")
