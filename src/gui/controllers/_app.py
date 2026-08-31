# src/gui/controllers/_app.py
"""
GUI 控制器总调度模块（内部实现）

- 接管全局生命周期信号
- 调度退出流程与配置重载
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from utils import get_logger
from utils.config import AppConfigData, AppSchema, save_config, set_config

from ..core import gui_bridge
from ..dialogs import ShutdownDialog

if TYPE_CHECKING:
    from gui import BotGUI


class AppController:
    """应用总调度器"""

    def __init__(self, main_window: "BotGUI") -> None:
        self._window = main_window
        self._shutdown_dialog: ShutdownDialog | None = None
        self._schema: AppSchema | None = None
        self._current_config: AppConfigData | None = None
        self._logger = get_logger("GUI")

        # 监听拦截信号，弹出退出提示
        gui_bridge.close_intercepted.connect(self._on_close_intercepted)

        # 监听底层清理完成信号，关闭弹窗并退出程序
        gui_bridge.shutdown_confirmed.connect(self._on_shutdown_confirmed)

        # 配置重载
        gui_bridge.config_updated.connect(self._on_config_reloaded)

        # 后台数据回灌
        gui_bridge.real_config_loaded.connect(self._on_real_config_loaded)

    def _on_close_intercepted(self) -> None:
        """用户点击了 X，拦截器捕获到意图"""
        reply = QMessageBox.question(
            self._window,
            "确认退出",
            "确定要关闭机器人并退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            gui_bridge.request_shutdown.emit()
        '''# 1. 创建弹窗
        self._shutdown_dialog = ShutdownDialog(parent=self._window)

        # 2. 用 exec() 阻塞，直到用户点击按钮。
        result = self._shutdown_dialog.exec()

        # 3. 判断结果
        if result == QDialog.DialogCode.Accepted:
            # 点“确认”，发送信号
            gui_bridge.request_shutdown.emit()
        else:
            # 点“取消”，关闭弹窗
            self._shutdown_dialog = None'''

    def _on_shutdown_confirmed(self) -> None:
        """收到清理完成信号"""
        # 1. 关闭弹窗
        if self._shutdown_dialog:
            self._shutdown_dialog.close()
            self._shutdown_dialog = None

        # 2. 退出整个 Qt 事件循环
        QApplication.quit()

    def _on_config_reloaded(self, new_config: AppConfigData) -> None:
        """
        收到配置重载信号

        保存配置，通知底层热重载
        """
        save_config(new_config)
        set_config(new_config)  # 更新内存中的全局配置单例

        # 通知底层引擎热重载
        gui_bridge.request_reload.emit()

        # 日志反馈
        self._logger.info("✅ 配置已保存并重载")

    def _on_real_config_loaded(
        self, schema: AppSchema, real_config: AppConfigData
    ) -> None:
        """
        数据回灌中枢

        后台静默加载完配置后，把真实数据注入到 BotGUI
        """
        # 1. 更新总调度室的内存引用
        self._schema = schema
        self._current_config = real_config

        # 2. 向下分发数据（假设你有一个 SettingsController）
        action_map = getattr(self._window, "action_map", None)
        if action_map and "setting" in action_map:
            settings_ctrl = action_map["setting"]
            if hasattr(settings_ctrl, "update_data"):
                settings_ctrl.update_data(schema, real_config)

        self._logger.info("✅ 真实配置已注入 BotGUI")
