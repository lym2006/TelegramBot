# src/gui/dialogs/_base.py
"""
GUI 弹窗基类模块（内部实现）

负责：
- 提取所有弹窗共有的样式、尺寸和初始化逻辑
- 统一应用全局主题
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QWidget

from .._theme import DIALOG_QSS


class BaseDialog(QDialog):
    """所有自定义弹窗的基类"""

    def __init__(self, parent: QWidget | None = None, title: str = "") -> None:
        super().__init__()

        # 1. 基础窗口属性
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # 2. 应用弹窗专属样式表
        self.setStyleSheet(DIALOG_QSS)
