# src/gui/dialogs/_shutdown.py
"""
GUI 配置关闭拦截弹窗模块（内部实现）

- 在用户关闭动作时提供退出反馈
- 防止用户强杀进程导致资源泄漏
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar

from .._theme import BODY
from .._theme import SHUTDOWN_DIALOG as DIALOG
from ._base import BaseDialog


class ShutdownDialog(BaseDialog):
    """极其冷酷的退出提示弹窗：无按钮，仅用于展示清理进度"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

        # 退出弹窗无边框
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(DIALOG.width, DIALOG.height)

        # 设置背景色
        self.setStyleSheet(
            "\n".join(
                [
                    f"QDialog {{ background-color: {BODY.bg}; }}",
                    f"QLabel {{ color: {BODY.color}; }}",
                ]
            )
        )

        # 布局与 UI 渲染
        layout = QHBoxLayout(self)

        # 加载动画
        self._progress = QProgressBar()
        self._progress.setFixedSize(DIALOG.icon_size, DIALOG.icon_size)
        self._progress.setTextVisible(False)
        self._progress.setRange(0, 0)  # 触发无限循环的忙碌动画

        # 提示文字
        self._label = QLabel(DIALOG.message)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._progress)
        layout.addWidget(self._label)
