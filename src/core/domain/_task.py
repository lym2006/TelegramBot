# src/core/domain/_task.py
"""任务对象

- 定义跨平台归一的任务类型、状态与优先级词表
"""

from enum import IntEnum, StrEnum


class TaskKind(StrEnum):
    """任务类型"""

    CHAT = "chat"
    TOGGLE = "toggle"
    HISTORY = "history"
    CLEAR = "clear"
    MD = "md"
    SYSTEM = "system"


class TaskStatus(StrEnum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(IntEnum):
    """任务优先级

    - 数值越小越优先
    """

    IMMEDIATE = 0  # 控制类命令：清队、停止、切换
    HIGH = 10  # 查询类：history、md
    NORMAL = 50  # 普通对话
