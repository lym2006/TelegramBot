# src/core/dto/_event.py
"""事件数据传输对象

- 定义入站事件和交互回调事件
"""

from dataclasses import dataclass

from ._content import ContentDTO
from ._identity import MessageRefDTO, PrincipalDTO


@dataclass(frozen=True, slots=True)
class InboundEventDTO:
    """入站事件

    - 中间件与业务层的唯一事件输入
    """

    ref: MessageRefDTO
    principal: PrincipalDTO
    content: ContentDTO

    is_command: bool = False
    command_name: str = ""
    command_args: tuple[str, ...] = ()
    reply_ref: MessageRefDTO | None = None
    is_mention_bot: bool = False
    created_at: float = 0.0
    display_name: str = ""


@dataclass(frozen=True, slots=True)
class CallbackEventDTO:
    """交互回调事件

    - TG 内联按键与 QQ 引用回复命令归一
    """

    ref: MessageRefDTO
    principal: PrincipalDTO
    action_id: str

    source_ref: MessageRefDTO | None = None
    payload: tuple[tuple[str, str], ...] = ()
    created_at: float = 0.0
