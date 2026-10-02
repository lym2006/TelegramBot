# src/core/domain/_platform.py
"""平台与会话值对象

- 定义跨平台归一的分类词表
"""

from enum import StrEnum


class Platform(StrEnum):
    """平台标识"""

    TELEGRAM = "telegram"
    QQ = "qq"


class ChatScope(StrEnum):
    """会话作用域

    - 平台语义在此归一
    """

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    UNKNOWN = "unknown"
