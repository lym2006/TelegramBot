# src/plugins/AI/utils.py
"""
AI 插件通用工具模块

- AI 消息数据构建工具
- 用户唯一身份标识提取
- 消息发送指数退避重试装饰器
"""

import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from aiogram.exceptions import TelegramNetworkError
from aiogram.types import Message
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils import get_logger

if TYPE_CHECKING:
    from .core.models import UserSession

logger_retry = get_logger("Plugins.AI.Retry")

__all__ = [
    "build_message",
    "make_data",
    "get_name",
    "retry_sending",
]

# ==================== 1. 内部常量与泛型定义 ====================

P = ParamSpec("P")
T = TypeVar("T")

# 重试器硬编码配置
_MAX_RETRIES = 3
_MIN_RETRY_DELAY = 1
_MAX_RETRY_DELAY = 10


# ==================== 2. 消息构建工具 ====================


def build_message(role: str, content: str) -> dict[str, str]:
    """
    构建发送给 AI 的消息字典

    消息角色可选 "user"、"system" 、"assistant"
    """
    return {"role": role, "content": content}


def make_data(session: "UserSession", thisinput: str) -> list[dict[str, str]]:
    """构建包含新输入的用户消息数据列表"""
    return session.message + [build_message("user", thisinput)]


# ==================== 3. 用户信息提取 ====================


def get_name(message: Message) -> str:
    """
    获取用户的唯一身份标识

    用户身份标识格式为 u_{user_id}（私聊）或 g_{group_id}_{user_id}（群聊）
    """
    id_ = message.chat.id
    return (
        f"g_{abs(id_)}_{getattr(getattr(message, 'from_user', None), 'id', 'unknown')}"
        if id_ < 0
        else f"u_{id_}"
    )


# ==================== 4. 异步重试装饰器 ====================


def retry_sending() -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    消息发送重试装饰器工厂

    用于包装 Telegram 消息发送逻辑，在遇到网络异常时自动进行指数退避重试（默认底数为1）
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        @retry(
            retry=retry_if_exception_type(TelegramNetworkError),
            stop=stop_after_attempt(_MAX_RETRIES),
            wait=wait_exponential(min=_MIN_RETRY_DELAY, max=_MAX_RETRY_DELAY),
            before_sleep=lambda retry_state: logger_retry.warning(
                f"消息发送失败，正在第 {retry_state.attempt_number} 次重试..."
            ),
            reraise=True,
        )
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator
