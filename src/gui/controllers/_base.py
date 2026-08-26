# src/gui/controllers/_base.py
"""
GUI 控制器基类模块（内部实现）

负责：
- 提供控制器基类，统一处理 GUI 引用
"""

from typing import TYPE_CHECKING

from utils.logger import get_logger

from ._decorator import gui_guard

if TYPE_CHECKING:
    from gui._app import BotGUI


class BaseController:
    """所有控制器的基类，统一处理 GUI 引用"""

    LOGGER_NAME: str

    guard = staticmethod(gui_guard)

    def __init__(self, gui_ref: "BotGUI") -> None:
        self.gui = gui_ref
        self.logger = get_logger(self.LOGGER_NAME)

    def close(self) -> None:
        """清理资源，子类可覆盖"""
