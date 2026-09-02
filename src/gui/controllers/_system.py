# src/gui/controllers/_system.py
"""
GUI 控制器系统操作模块（内部实现）

- 打开日志目录
- 检查版本更新
"""

import asyncio
import os
import sys

from utils import ROOT_DIR, check_updates

from ._base import BaseController

_LOGS_DIR = ROOT_DIR / "logs"


class LogsController(BaseController):
    """日志控制器"""

    # ==================== 契约声明 ====================
    LOGGER_NAME = "GUI.Op.Logs"
    BTN_KEY = "log"

    # ==================== 业务逻辑实现 ====================
    def _execute(self) -> None:
        """打开日志文件所在目录"""
        self.logger.info("正在打开日志文件目录...")
        if sys.platform == "win32":
            try:
                os.startfile(_LOGS_DIR)
                self.logger.info("成功打开日志目录")

            except OSError as e:
                # 捕获 Windows 底层 API 可能抛出的系统级错误
                # 比如路径含空格、权限不足、explorer 崩溃等
                self.logger.send_error("打开日志目录失败", e)

            except Exception as e:
                # 防止任何未知异常导致 GUI 闪退
                self.logger.send_error("发生未知错误", e)


class UpdateController(BaseController):
    """更新控制器"""

    # ==================== 契约声明 ====================
    LOGGER_NAME = "GUI.Op.Update"
    BTN_KEY = "update"

    def _execute(self) -> None:
        """检查版本更新"""
        self.logger.info("正在检查版本更新...")
        asyncio.run(check_updates())
