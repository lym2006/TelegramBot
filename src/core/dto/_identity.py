# src/core/dto/_identity.py
"""身份数据传输对象

- 定义会话主体与消息定位
"""

from dataclasses import dataclass

from ..domain import ChatScope, Platform


@dataclass(frozen=True, slots=True)
class PrincipalDTO:
    """会话主体标识"""

    platform: Platform
    scope: ChatScope
    chat_id: str
    user_id: str

    @property
    def key(self) -> str:
        """全局唯一键

        - 形如 telegram:group:-100123:456
        """
        return ":".join(
            v or "-" for v in (self.platform, self.scope, self.chat_id, self.user_id)
        )


@dataclass(frozen=True, slots=True)
class MessageRefDTO:
    """消息定位四元组

    - 图片定位接口的寻址依据
    """

    platform: Platform
    chat_id: str
    user_id: str
    message_id: str

    @property
    def key(self) -> str:
        """四元组联合键"""
        return ":".join(
            v or "-"
            for v in (self.platform, self.chat_id, self.user_id, self.message_id)
        )
