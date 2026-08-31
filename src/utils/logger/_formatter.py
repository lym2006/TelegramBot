# src/utils/logger/_formatter.py
"""
日志格式器创建模块（内部实现）

- 创建统一的日志格式器
"""

import logging


def create_formatter(
    fmt: str,
    datefmt: str,
) -> logging.Formatter:
    """创建日志格式器"""
    return logging.Formatter(fmt=fmt, datefmt=datefmt)
