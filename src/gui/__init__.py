# src/gui/__init__.py
"""
GUI 门面

- BotGUI 类型
- 创建并初始化 GUI 的方法
"""

from utils.config import AppConfigData, AppSchema
from utils.logger import FORMATTER, get_logger

from ._main_window import BotGUI
from ._qss import build_global_qss
from ._theme import BODY, FONT, TOOLBAR, TOOLBAR_BUTTONS, WINDOW
from .controllers import build_controllers

logger = get_logger("GUI")

__all__ = [
    # 类型
    "BotGUI",
    # 唯一创建和初始化 GUI 方法
    "create_gui",
]


def create_gui(schema: AppSchema, current_config: AppConfigData) -> BotGUI:
    """创建并装配 BotGUI 实例"""
    # ==================== 1. 创建纯粹的 UI 渲染器 ====================

    botgui = BotGUI(
        qss=build_global_qss(),
        buttons=TOOLBAR_BUTTONS,
        configs=(FONT, WINDOW, BODY, TOOLBAR),
        formatter=FORMATTER,
    )

    # ==================== 2. 打包业务控制器 ====================

    controllers = build_controllers(botgui, schema, current_config)

    # ==================== 3. 防呆校验 ====================

    valid_ui_keys = {key for _, key in TOOLBAR_BUTTONS}
    registered_keys = {btn_id.replace("btn_", "", 1) for btn_id, _ in controllers}

    if unregistered := registered_keys - valid_ui_keys:
        raise ValueError(
            f"控制器绑定失败: 发现未在 UI 层定义的按钮标识 -> {unregistered}"
        )

    if missing := valid_ui_keys - registered_keys:
        raise ValueError(
            f"控制器缺失: UI 层定义了按钮，但缺少对应的 Controller -> {missing}"
        )

    # ==================== 4. 注入依赖并返回 ====================

    botgui.set_action_map(dict(controllers))
    botgui.set_logger_handler()
    return botgui


# TODO:在这里接住自定义异常并写日志
