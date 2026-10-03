# src/core/contracts/_adapter.py
"""适配器契约

- 定义交互端口与适配器基类的抽象接口
"""

from abc import ABC, abstractmethod

from ..dto import MenuSpecDTO, MessageRefDTO, OutboundContentDTO, PrincipalDTO


class InteractionPort(ABC):
    """交互端口

    - 屏蔽平台底层差异
    """

    @abstractmethod
    async def send_message(
        self,
        principal: PrincipalDTO,
        content: OutboundContentDTO,
        *,
        mention: bool = False,
        spec: MenuSpecDTO | None = None,
        reply_ref: MessageRefDTO | None = None,
    ) -> MessageRefDTO | None:
        """发送消息

        - reply_ref 非空时引用该消息
        - mention 为真时提及目标主体
        - spec 非空时，由 Adapter 适配各端可用的交互菜单
        - 具体引用和提及实现由 Adapter 内部处理
        """

    @abstractmethod
    async def probe_existence(self, target: MessageRefDTO) -> bool:
        """探测消息是否仍存在"""

    @abstractmethod
    def mention_fragment(self, principal: PrincipalDTO) -> str:
        """生成提及文本片段

        - 纯字符串拼装，不发请求
        - 不同平台返回格式不同，由 Adapter 决定
        """
