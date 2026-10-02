# src/core/domain/__init__.py
"""领域类型门面

- 定义业务类型，将不同平台的原始类型归一化
- 零外部依赖，不包含实例数据
"""

from ._content import ContentKind
from ._platform import ChatScope, Platform
from ._role import ChatRole
from ._task import TaskKind, TaskPriority, TaskStatus

__all__ = [
    # 平台
    "Platform",
    "ChatScope",
    # 内容与角色
    "ContentKind",
    "ChatRole",
    # 任务
    "TaskKind",
    "TaskStatus",
    "TaskPriority",
]
