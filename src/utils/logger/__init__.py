# src/utils/logger/__init__.py
"""
日志系统门面模块

导出：
- 获取日志器方法（自动懒初始化）
- 日志格式
"""

import logging

from ._enhancer import enhance_logger
from ._filter import suppress_third_party_logs
from ._formatter import create_formatter
from ._handlers import create_console_handler, create_file_handler

# 模块级状态
_initialized = False

# 全局常量
FORMATTER = create_formatter()

__all__ = [
    # 获取日志器
    "get_logger",
    # 日志格式
    "FORMATTER",
]


def _setup_logger() -> None:
    """初始化全局日志系统"""
    global _initialized
    if _initialized:
        return

    root_logger = logging.getLogger("Bot")
    root_logger.setLevel(logging.INFO)

    root_logger.addHandler(create_console_handler(FORMATTER))
    root_logger.addHandler(create_file_handler(formatter=FORMATTER))

    enhance_logger(root_logger)

    suppress_third_party_logs()

    _initialized = True


def get_logger(name: str = "Bot") -> logging.Logger:
    """获取日志器，如果未初始化则自动配置根日志器"""
    if not _initialized:
        _setup_logger()

    return logging.getLogger(name)
