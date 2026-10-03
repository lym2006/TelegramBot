# src/core/dto/_interaction.py
"""交互数据传输对象

- 定义外发内容负载与内联菜单规格
"""

from dataclasses import dataclass

from ..domain import ContentKind


@dataclass(frozen=True, slots=True)
class OutboundContentDTO:
    """外发内容负载

    - kind 分派文字与媒体两种形态
    """

    kind: ContentKind
    text: str = ""  # 负载文字时为正文，媒体时为附言
    local_path: str = ""  # 仅媒体种类使用
    file_name: str = ""  # 对外展示文件名，缺省取 local_path 末段


@dataclass(frozen=True, slots=True)
class MenuActionDTO:
    """菜单单个按钮"""

    action_id: str
    label: str


@dataclass(frozen=True, slots=True)
class MenuSpecDTO:
    """内联菜单规格"""

    title: str
    rows: tuple[tuple[MenuActionDTO, ...], ...] = ()
