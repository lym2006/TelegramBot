# src/core/dto/_session.py
"""会话数据传输对象

- 定义消息会话上下文与状态变更的数据快照
"""

from dataclasses import dataclass

from ..domain import ChatRole
from ._identity import PrincipalDTO


@dataclass(frozen=True, slots=True)
class MessageDTO:
    """单条会话消息"""

    role: ChatRole
    content: str
    created_at: float = 0.0


@dataclass(frozen=True, slots=True)
class SessionDTO:
    """会话快照

    - 只读投影，禁止原地修改
    """

    principal: PrincipalDTO
    messages: tuple[MessageDTO, ...] = ()
    is_active: bool = False
    last_active: float = 0.0


@dataclass(frozen=True, slots=True)
class SessionPatchDTO:
    """会话增量

    - 修改会话的唯一入参形态
    """

    append: tuple[MessageDTO, ...] | None = None
