# src/gui/controllers/_shutdown.py
"""
GUI 控制器关闭模块（内部实现）

负责：
- 拦截关闭事件
- 优雅地清理资源（保存配置、停止后台线程等）
- 触发最终的窗口销毁
"""

from ._base import BaseController


class ShutdownController(BaseController):
    """安全退出与资源清理业务逻辑"""

    LOGGER_NAME = "Bot.GUI.Op.Shutdown"

    @BaseController.guard
    def safe_exit(self) -> None:
        """
        执行安全退出流程

        当用户确认退出后，由拦截器调用此方法
        确保所有关键资源被正确释放
        """
        self.logger.info("🛑 收到安全退出指令，正在清理资源...")

        # TODO: 1. 保存当前配置到本地文件
        # self.gui.config.save()

        # TODO: 2. 通知核心业务线程停止工作
        # self.gui.core.stop()

        # TODO: 3. 关闭其他可能存在的子窗口或弹窗
        # for dialog in self.gui.open_dialogs:
        #     dialog.close()

        # TODO: 4. 真正销毁主窗口并退出事件循环
        # self.gui.close()

        self.logger.info("👋 程序已安全关闭，再见！")
