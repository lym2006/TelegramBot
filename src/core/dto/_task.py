# src/core/dto/_task.py
"""任务数据传输对象

- 定义任务队列的只读视图、创建请求与状态增量
"""

from dataclasses import dataclass

from ..domain import TaskKind, TaskPriority, TaskStatus
from ._content import ContentDTO
from ._identity import MessageRefDTO, PrincipalDTO


@dataclass(frozen=True, slots=True)
class TaskDTO:
    """任务只读视图"""

    task_id: str
    principal: PrincipalDTO
    kind: TaskKind
    status: TaskStatus
    priority: TaskPriority

    source_ref: MessageRefDTO | None = None
    payload: tuple[tuple[str, str], ...] = ()
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    error_text: str = ""


@dataclass(frozen=True, slots=True)
class TaskRequestDTO:
    """任务创建请求

    - enqueue 的唯一入参
    """

    principal: PrincipalDTO
    kind: TaskKind

    priority: TaskPriority = TaskPriority.NORMAL
    dedupe_key: str = ""  # 防重复提交
    content: ContentDTO | None = None
    source_ref: MessageRefDTO | None = None
    payload: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class TaskPatchDTO:
    """任务增量

    - 状态推进与产物回填统一走此
    - None 表示不修改
    """

    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    error_text: str | None = None
    finished_at: float | None = None
