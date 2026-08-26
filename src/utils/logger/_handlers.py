# src/utils/logger/_handlers.py
"""
日志处理器工厂模块（内部实现）

负责：
- 控制台输出 Handler（stdout）
- 文件输出 Handler（RotatingFileHandler，10MB 自动切割）
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_PATH = Path("logs/bot.log")  # 本地日志路径
MAX_SIZE = 10  # 最大文件大小（单位：MB）
BACKUP_COUNT = 2  # 备份数量（2旧1新）


def create_console_handler(formatter: logging.Formatter) -> logging.StreamHandler:
    """创建控制台输出 Handler"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    return handler


def create_file_handler(
    log_path: Path = LOG_PATH,
    max_bytes: int = MAX_SIZE * 1024 * 1024,
    backup_count: int = BACKUP_COUNT,
    formatter: logging.Formatter | None = None,
) -> RotatingFileHandler:
    """创建文件输出 Handler"""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    return handler
