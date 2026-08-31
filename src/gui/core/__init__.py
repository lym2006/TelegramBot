# src/gui/core/__init__.py
"""
GUI 核心门面

- 窗口关闭事件拦截器
- 全局信号桥单例实例
"""

from ._interceptors import WindowCloseInterceptor
from ._signals import gui_bridge

__all__ = [
    # 事件拦截器
    "WindowCloseInterceptor",
    # 信号桥
    "gui_bridge",
]
