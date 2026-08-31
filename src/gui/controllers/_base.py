# src/gui/controllers/_base.py
"""
GUI 控制器基类模块（内部实现）

- 提供控制器基类，统一处理 GUI 引用
- 强制声明按钮绑定契约与业务执行入口
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from utils.logger import get_logger

from ._decorator import gui_guard

if TYPE_CHECKING:
    from gui import BotGUI


class BaseController(ABC):
    """
    所有控制器的基类

    统一处理 GUI 引用、日志注入，并强制子类声明按钮绑定契约
    """

    # ==================== 1. 契约声明区 ====================
    # 子类必须声明这两个属性，否则实例化时会报错

    LOGGER_NAME: str  # 日志器名称
    BTN_KEY: str  # 绑定的按钮标识（如 "func"，底层会自动拼接为 "btn_func"）

    @abstractmethod
    def _execute(self) -> None:
        """
        纯粹的业务逻辑（子类必须实现）

        如果子类忘记实现此方法，实例化时将直接抛出 TypeError
        """

    # ==================== 2. 初始化与生命周期 ====================

    def __init__(self, gui_ref: "BotGUI") -> None:
        self.gui = gui_ref
        self.logger = get_logger(self.LOGGER_NAME)

    # ==================== 3. 自动生成的绑定标识 ====================

    @property
    def btn_id(self) -> str:
        """获取完整的按钮 ID"""
        return f"btn_{self.BTN_KEY}"

    # ==================== 4. 公开业务执行入口 ====================

    @gui_guard
    def execute(self) -> None:
        """
        统一的业务执行入口

        门面会调用这个方法，自动触发安全守卫，
        然后将实际业务委托给子类的 _execute() 方法
        """
        self._execute()
