# src/utils/logger/_formatter.py
"""
日志格式器创建模块（内部实现）

负责：
- 创建统一的日志格式器
"""

import logging

FMT = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def create_formatter(
    fmt: str = FMT,
    datefmt: str = DATEFMT,
) -> logging.Formatter:
    """创建日志格式器"""
    return logging.Formatter(fmt=fmt, datefmt=datefmt)
