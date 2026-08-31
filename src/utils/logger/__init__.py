# src/utils/logger/__init__.py
"""
日志系统门面

- 专属增强型日志器（自动懒初始化，强制 Bot 命名空间）
- 增强型日志器类（支持自动堆栈捕获与分层报错）
- 全局日志格式器
"""

import logging
import threading
from typing import cast

from .._root_dir import ROOT_DIR
from ._enhancer import BotLogger
from ._formatter import create_formatter
from ._handler import create_file_handler

# 模块级状态
_initialized = False
_setup_lock = threading.Lock()

# 日志格式配置
_FMT = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

# 文件输出配置
_LOG_PATH = ROOT_DIR / "logs" / "bot.log"
_MAX_SIZE = 10  # 最大文件大小（单位：MB）
_BACKUP_COUNT = 2  # 旧文件备份数量

# 全局派生常量（对外提供）
FORMATTER = create_formatter(_FMT, _DATEFMT)

__all__ = [
    # 获取日志器
    "get_logger",
    # 增强型日志器类
    "BotLogger",
    # 日志格式
    "FORMATTER",
]

# 在模块加载时，接管全局 Logger 类
logging.setLoggerClass(BotLogger)


def get_logger(name: str = "") -> BotLogger:
    """获取 Bot 专属日志器（首次调用时自动完成全局初始化）"""
    global _initialized

    name = "Bot." + name if name else "Bot"
    logger = cast(BotLogger, logging.getLogger(name))

    # 快速路径：已初始化，直接返回（无锁开销）
    if _initialized:
        return logger

    # 慢速路径：需要初始化，加锁保护
    with _setup_lock:
        if _initialized:  # 双重检查，防止两个线程同时进入后重复初始化
            return logger

        # 1. 根 Logger 静默
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.CRITICAL + 1)

        # 2. Bot Logger
        bot_logger = logging.getLogger("Bot")
        bot_logger.setLevel(logging.DEBUG)
        bot_logger.propagate = False  # 绝对不向根 Logger 冒泡

        # 3. 文件 Handler
        file_handler = create_file_handler(
            formatter=FORMATTER,
            log_path=_LOG_PATH,
            max_bytes=_MAX_SIZE * 1024 * 1024,
            backup_count=_BACKUP_COUNT,
        )
        bot_logger.addHandler(file_handler)

        # 4. 标记初始化完成
        _initialized = True

    return logger
