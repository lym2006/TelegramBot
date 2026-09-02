# src/gui/controllers/__init__.py
"""
GUI 控制器门面模块

- 自动实例化控制器，并打包为 GUI 所需的契约格式 (btn_id, execute)
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from ._dashboard import DashboardController
from ._settings import SettingsController
from ._shutdown import ShutdownController
from ._system import LogsController, UpdateController

if TYPE_CHECKING:
    from gui import BotGUI

__all__ = [
    # 唯一打包函数
    "build_controllers",
]

# 内部收集所有 Controller 类，便于统一遍历
_ALL_CONTROLLER_CLASSES = (
    DashboardController,
    LogsController,
    SettingsController,
    ShutdownController,
    UpdateController,
)


def build_controllers(gui_ref: "BotGUI") -> list[tuple[str, Callable]]:
    """自动实例化所有控制器，并打包为契约格式"""
    controllers = []
    for cls in _ALL_CONTROLLER_CLASSES:
        # 注入 GUI 引用，实例化控制器
        instance = cls(gui_ref)

        # 提取契约并打包
        controllers.append((instance.btn_id, instance.execute))

    return controllers
