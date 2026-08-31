# src/utils/logger/_enhancer.py
"""
日志输出增强模块（内部实现）

- 为指定 Logger 的 debug 方法注入自动 exc_info 捕获逻辑
"""

import logging
import sys


class BotLogger(logging.Logger):
    """Bot 专属的增强型日志器"""

    def __init__(self, name: str, level=logging.NOTSET) -> None:
        super().__init__(name, level)

    def debug(self, msg, *args, **kwargs) -> None:
        """增强型 debug，自动注入异常堆栈信息"""
        if "exc_info" not in kwargs and sys.exc_info()[0] is not None:
            kwargs["exc_info"] = True
        super().debug(msg, *args, **kwargs)

    def send_error(self, msg: str, e: Exception) -> None:
        """写入报错日志（分层 GUI 和文件）"""
        self.error(msg)
        self.debug(e)
