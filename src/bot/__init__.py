# src/bot/__init__.py
"""Bot 门面模块

导出：
- Bot 核心引擎类
"""

from typing import TYPE_CHECKING

__all__ = ["BotEngine"]


if TYPE_CHECKING:
    from ._core import BotEngine


# 延迟导入
def __getattr__(name: str) -> type["BotEngine"]:
    if name == "BotEngine":
        from ._core import BotEngine

        return BotEngine
    raise AttributeError(f"模块 {__name__!r} 没有 {name!r} 属性")
