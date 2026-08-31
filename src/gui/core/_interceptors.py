# src/gui/core/_interceptors.py
"""
GUI 核心事件拦截模块（内部实现）

- 拦截 Qt 底层事件
- 阻断默认行为，发射对应信号
"""

from PySide6.QtGui import QCloseEvent

from ._signals import gui_bridge


class WindowCloseInterceptor:
    """窗口关闭拦截器"""

    def handle(self, event: QCloseEvent) -> None:
        """处理原生关闭事件"""
        # 1. 阻止 Qt 默认的销毁行为
        event.ignore()

        # 2. 发射拦截信号
        gui_bridge.close_intercepted.emit()
