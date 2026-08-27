# src/utils/gui/__init__.py
"""
GUI 门面模块

导出：
- BotGUI 类型
- 创建并初始化 GUI 的方法
"""

import sys

from utils.exception import FontError, GUIError
from utils.logger import get_logger

from ._dashboard import DashboardWidget, TextHandler
from ._main_window import BotGUI

logger = get_logger("Bot.GUI")

__all__ = [
    # 类型
    "BotGUI",
    # 方法
    "create_gui",
]


def create_gui() -> BotGUI:
    """将控制器自动注入到主窗口中，并初始化仪表盘与日志流"""
    # ==================== 1. 组装仪表盘与日志流 ====================
    try:
        # 实例化窗口
        window = BotGUI()

        # 实例化仪表盘
        dashboard = DashboardWidget(parent=window)

        # 创建日志处理器，并将仪表盘绑定给它
        log_handler = TextHandler(widget=dashboard)

        # 将处理器注入到全局日志系统中
        root_logger = get_logger("Bot")
        root_logger.addHandler(log_handler)

        # 将仪表盘挂载到主窗口
        window.dashboard = dashboard

    except FontError as e:
        # 字体加载失败，记录严重错误并优雅退出
        logger.critical(f"❌ GUI 初始化失败: {e}")
        sys.exit(1)
    except GUIError as e:
        # 捕获其他 GUI 初始化异常
        logger.critical(f"❌ GUI 组装异常: {e}")
        sys.exit(1)

    # ==================== 2. 预留 Dialogs 坑位 ====================
    # TODO: 未来在此处初始化各类对话框 (Dialogs)
    # from ._dialogs import SomeDialog
    # window.some_dialog = SomeDialog(parent=window)

    # ==================== 3. 注入 Controller ====================
    # TODO: 将业务控制器注入到主窗口
    # window.controller = controller_instance
    return window
