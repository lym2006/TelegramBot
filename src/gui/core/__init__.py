# src/gui/core/__init__.py
"""
GUI 核心门面

- 全局信号桥单例实例
"""

from ._signals import gui_bridge

__all__ = [
    # 信号桥
    "gui_bridge",
]
