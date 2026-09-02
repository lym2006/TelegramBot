# src/gui/controllers/_dashboard.py
"""
GUI 控制器仪表盘模块（内部实现）

- 清空仪表盘日志
"""

from ._base import BaseController


class DashboardController(BaseController):
    """仪表盘控制器"""

    # ==================== 契约声明 ====================

    LOGGER_NAME = "GUI.Op.Dashboard"
    BTN_KEY = "clear"

    # ==================== 业务逻辑实现 ====================

    def _execute(self) -> None:
        """清空仪表盘内容"""
        self.gui.clear_dashboard()
        self.logger.info("仪表盘已清空")
