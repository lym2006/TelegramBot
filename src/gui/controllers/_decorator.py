# src/gui/controllers/_decorator.py
"""
GUI 控制器异常处理模块（内部实现）

- 拦截 Controller 业务逻辑中的所有异常
- 防止未捕获的异常导致 GUI 线程卡死或崩溃

Todo:
- 未来可引入异常分级处理机制（区分业务异常与系统异常）
"""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar, cast

from utils.logger import get_logger

logger = get_logger("GUI.Op.Guard")

# 泛型定义
P = ParamSpec("P")
T = TypeVar("T")


def gui_guard(func: Callable[P, T]) -> Callable[P, T]:
    """
    GUI 按钮事件安全装饰器

    作为 BaseController 的底层防御机制，自动拦截所有异常，
    防止未捕获的异常导致 GUI 线程卡死，并统一记录错误日志
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            return func(*args, **kwargs)

        except Exception as e:
            logger.send_error(f"❌ 执行 [{func.__name__}] 时发生错误", e)

        return

    return cast(Callable[P, T], wrapper)
