# src/gui/controllers/_shutdown.py
"""
GUI 控制器进程关闭模块（内部实现）

- 调度退出流程
"""

import os

from PySide6.QtCore import QTimer

from ..core import gui_bridge
from ..dialogs import ShutdownDialog
from ._base import BaseController


class ShutdownController(BaseController):
    """进程关闭控制器"""

    # ==================== 契约声明 ====================
    LOGGER_NAME = "GUI.Op.Shutdown"
    BTN_KEY = "shutdown"

    # ==================== 初始化 ====================

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._check_shutdown_timer: QTimer = None  # type: ignore
        self._force_exit_timer: QTimer = None  # type: ignore
        self._is_shutting_down = False

    def _execute(self) -> None:
        """执行退出逻辑"""
        self._on_close_intercepted()

    def _on_close_intercepted(self) -> None:
        """弹出确认框，确认后启动清理流程"""
        # 不重复执行
        if self._is_shutting_down:
            return

        dialog = ShutdownDialog(parent=self.gui)
        reply = dialog.exec()

        if reply == ShutdownDialog.DialogCode.Accepted:
            self.logger.info("🚨 用户点击确认，准备发信号并启动定时器")
            self._start_shutdown()

        else:
            self.logger.info("🚨 用户取消关闭操作")
            self._is_shutting_down = False
            gui_bridge.shutdown_completed_event.clear()
            self._stop_timers()

    def _start_shutdown(self) -> None:
        self._is_shutting_down = True
        gui_bridge.request_shutdown.emit()

        # 检查定时器：每 0.1 秒检查一次底层清理状态
        self.logger.info("⏳ 正在等待 Bot 线程清理资源...")
        self._check_shutdown_timer = QTimer(self.gui)
        self._check_shutdown_timer.timeout.connect(self._check_shutdown_status)
        self._check_shutdown_timer.start(100)
        self.logger.info("⌚️ 检查定时器已启动，轮询检查间隔 0.1 秒")

        # 超时定时器：如果 10 秒后还没清理完，强行退出
        self._force_exit_timer = QTimer(self.gui)
        self._force_exit_timer.setSingleShot(True)
        self._force_exit_timer.timeout.connect(self._force_exit)
        self._force_exit_timer.start(10000)
        self.logger.info("⌚️ 超时定时器已启动，若出现意外，10 秒后强制退出")

    def _check_shutdown_status(self) -> None:
        """轮询检查 Bot 线程是否清理完毕"""
        # 用户取消清理，不检查
        if not self._is_shutting_down:
            return

        if gui_bridge.shutdown_completed_event.is_set():
            # 停掉定时器与超时定时器（如果有）
            self._stop_timers()
            self.logger.info("⏳ 资源已清理完毕，程序将在 3 秒后退出...")
            QTimer.singleShot(3000, lambda: os._exit(0))

    def _force_exit(self) -> None:
        """超时强制退出"""
        # 取消或已完成时直接放行
        if not self._is_shutting_down or gui_bridge.shutdown_completed_event.is_set():
            return
        self.logger.warning("⚠️ 底层清理超时，强制终止进程")
        os._exit(1)  # 返回非零退出码，表示异常退出

    def _stop_timers(self) -> None:
        """停掉所有定时器"""
        if self._check_shutdown_timer:
            self._check_shutdown_timer.stop()
        if self._force_exit_timer:
            self._force_exit_timer.stop()
