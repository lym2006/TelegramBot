# src/gui/controllers/_config.py
"""
GUI 控制器修改配置模块（内部实现）

负责：
- 显示当前配置
- 还原默认配置
- 修改与保存
"""

from ._base import BaseController


class ConfigController(BaseController):
    """日志"""

    LOGGER_NAME = "Bot.GUI.Op.Config"

    @BaseController.guard
    def on_config_click(self) -> None:
        """打开配置面包"""
        self.logger.info("⚙️ 正在打开配置面板...")
        # TODO: 调用打开日志模块
