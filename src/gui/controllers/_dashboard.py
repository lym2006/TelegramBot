# src/gui/controllers/_dashboard.py
"""
GUI 控制器仪表盘模块（内部实现）

负责：
- 清空仪表盘日志
"""

from ._base import BaseController


class DashboardController(BaseController):
    """仪表盘业务逻辑"""

    LOGGER_NAME = "Bot.GUI.Op.Dashboard"

    @BaseController.guard
    def clear_dashboard(self) -> None:
        """清空仪表盘内容"""
        self.gui.dashboard.clear()
        self.logger.info("🧹 仪表盘已清空")
