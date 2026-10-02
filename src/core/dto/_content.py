# src/core/dto/_content.py
"""内容数据传输对象

- 定义消息内容
"""

from dataclasses import dataclass

from ..domain import ContentKind
from ._identity import MessageRefDTO


@dataclass(frozen=True, slots=True)
class ContentDTO:
    """消息内容

    - 平台载荷归一
    """

    kind: ContentKind
    text: str = ""
    file_name: str = ""
    file_token: str = ""  # 平台侧文件标识，惰性下载
    image_count: int = 0
    raw_ref: MessageRefDTO | None = None  # 媒体实际挂载的消息，引用与转发时指回原消息
