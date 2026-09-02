# src/gui/dialogs/__init__.py
"""
GUI 弹窗门面

- 所有弹窗组件
"""

from ._settings import NotChangedDialog, SettingsDialog
from ._shutdown import ShutdownDialog

__all__ = [
    # 配置修改
    "NotChangedDialog",
    "SettingsDialog",
    # 关闭事件
    "ShutdownDialog",
]
