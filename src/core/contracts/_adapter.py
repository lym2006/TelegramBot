# src/core/ports/_adapter.py
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
        mention: bool = False,
        reply_ref: MessageRefDTO | None = None,
    ) -> MessageRefDTO | None:
        """发送消息

        - reply_ref 非空时回复消息
        - mention 为 True 时点名 principal，TG 正文前缀深链、QQ 加 at 段
        - 文件超平台限制时降级为原样发送，由 Adapter 内部处理
        """

    @abstractmethod
    async def edit_message(self, target: MessageRefDTO, text: str) -> bool:
        """编辑已发消息

        - 不支持或失败返回 False，调用方决定降级
        """

    @abstractmethod
    async def delete_message(self, target: MessageRefDTO) -> bool:
        """删除消息"""

    @abstractmethod
    async def probe_existence(self, target: MessageRefDTO) -> bool:
        """探测消息是否仍存在"""

    @abstractmethod
    def mention_fragment(self, principal: PrincipalDTO, user_id: str) -> str:
        """生成提及文本片段

        - TG 返回 markdown 深链，可嵌进长文本
        - QQ 返回纯用户名，真点名靠 at 消息段、字符串表达不了高亮
        - 同步方法，纯字符串拼装不发请求
        """

    @abstractmethod
    async def send_status(
        self,
        principal: PrincipalDTO,
        text: str,
        spec: MenuSpecDTO | None = None,
        ref: MessageRefDTO | None = None,
    ) -> MessageRefDTO | None:
        """发送状态占位消息

        - 两端均发，引用 reply_ref 指向的原消息，不点名
        - 返回占位 ref，终态统一删除占位后经 send_message 新发结果
        - spec 非空：TG 挂键盘 / QQ 降级为占位内可操作提示，终态新发结果不带键盘
        """
