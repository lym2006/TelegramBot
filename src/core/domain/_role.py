# src/core/domain/_role.py
"""AI 对话身份对象

- 定义跨平台归一的 AI 对话角色词表
"""

from enum import StrEnum


class ChatRole(StrEnum):
    """AI 对话角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
