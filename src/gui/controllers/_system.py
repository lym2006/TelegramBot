# src/gui/controllers/_system.py
"""
GUI 控制器系统操作模块（内部实现）

负责：
- 打开日志
- 检查更新
"""

from ._base import BaseController


class LogsController(BaseController):
    """日志"""

    LOGGER_NAME = "Bot.GUI.Op.Logs"

    @BaseController.guard
    def on_log_click(self) -> None:
        """打开日志文件所在目录"""
        self.logger.info("📂 正在打开日志文件目录...")
        # TODO: 调用打开日志模块


class UpdateController(BaseController):
    """更新"""

    LOGGER_NAME = "Bot.GUI.Op.Update"

    @BaseController.guard
    def on_update_click(self) -> None:
        """检查更新"""
        self.logger.info("🔄 正在检查版本更新...")
        # TODO: 调用更新检查模块
