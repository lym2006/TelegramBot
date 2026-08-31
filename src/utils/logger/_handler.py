# src/utils/logger/_handler.py
"""
日志处理器工厂模块（内部实现）

- 文件输出 Handler（RotatingFileHandler）
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def create_file_handler(
    formatter: logging.Formatter,
    log_path: Path,
    max_bytes: int,
    backup_count: int,
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
    handler.setLevel(logging.DEBUG)
    return handler
