# src/gui/core/__init__.py
"""
GUI 核心门面模块

导出：
- 窗口关闭事件拦截器
- GUI 与 Bot 之间的全局通信桥梁
- 全局信号桥单例实例
"""

from ._interceptors import WindowCloseInterceptor
from ._signals import GUIBridge, gui_bridge

__all__ = [
    # 事件拦截器
    "WindowCloseInterceptor",
    # 信号桥
    "GUIBridge",
    "gui_bridge",
]
