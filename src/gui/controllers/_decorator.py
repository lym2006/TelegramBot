# src/gui/controllers/_decorator.py
"""
GUI 控制器异常处理模块（内部实现）

负责：
- 统一的异常捕获与日志记录
- 针对已知业务异常与未知系统异常的分级处理
"""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar, cast

# from utils.exception import BotError
from utils.logger import get_logger

logger = get_logger("Bot.GUI.Controller")

# 泛型定义
P = ParamSpec("P")
T = TypeVar("T")


def gui_guard(func: Callable[P, T]) -> Callable[P, T]:
    """
    GUI 按钮事件安全装饰器

    自动捕获业务逻辑中的异常，防止 GUI 卡死，并记录日志
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            return func(*args, **kwargs)

        except Exception as e:
            logger.error(f"❌ 执行 [{func.__name__}] 时发生错误：{e}")

        return

    return cast(Callable[P, T], wrapper)
