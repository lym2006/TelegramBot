# src/gui/_main_window.py
"""
GUI 主窗口模块（内部实现）

- BotGUI 窗口类（纯 UI 渲染与指令执行层）
"""

import logging
from collections.abc import Callable
from typing import Protocol

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger

from .core import gui_bridge
from ._dashboard import DashboardWidget, TextHandler
from ._theme import BodyConfig, FontConfig, ToolbarConfig, WindowConfig


# 定义一个拦截器协议
class _CloseInterceptorProtocol(Protocol):
    """窗口关闭拦截器协议（内部使用）"""

    def handle(self, event: QCloseEvent) -> None: ...


class BotGUI(QMainWindow):
    """
    Bot 可视化窗口

    接收门面注入的主题数据与业务回调
    """

    # ==================== 1. 初始化 ====================

    def __init__(
        self,
        qss: str,
        buttons: list[tuple[str, str]],
        configs: tuple[FontConfig, WindowConfig, BodyConfig, ToolbarConfig],
        formatter: logging.Formatter,
        close_interceptor: _CloseInterceptorProtocol,
    ) -> None:
        super().__init__()
        self._qss = qss
        self._buttons = buttons
        self._fonts, self._windows, self._body, self._toolbar = configs

        self._logger=get_logger("GUI")

        # 基础窗口属性设置
        self.setWindowTitle(self._windows.title)
        self.resize(self._windows.width, self._windows.height)
        self.setMinimumSize(self._windows.min_width, self._windows.min_height)

        # 按钮事件映射表（按钮 ID -> 已包装的回调函数）
        self.action_map: dict[str, Callable] = {}

        # 仪表盘与文本处理器（纯 UI 组件，内部实例化）
        self._dashboard = DashboardWidget(self._fonts)
        self._text_handler: logging.Handler = TextHandler(self._dashboard, formatter)

        # 窗口关闭拦截器
        self._close_interceptor = close_interceptor

        # 构建纯 UI 界面
        self._build_ui()

    # ==================== 2. 界面构建 ====================

    def _build_ui(self) -> None:
        """组装窗口的整体布局结构"""
        # 中央容器
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        # 主布局（垂直排列，工具栏在上，仪表盘在下）
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(self._body.padding)

        # 顶部工具栏
        self._build_toolbar(main_layout)

        # 仪表盘区域
        main_layout.addWidget(self._dashboard)

        # 应用全局 QSS 样式表
        self.setStyleSheet(self._qss)

    def _build_toolbar(self, parent_layout: QVBoxLayout) -> None:
        """渲染顶部工具栏及按钮控件"""
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")  # 用于 QSS 选择器 #toolbar
        toolbar.setFixedHeight(self._toolbar.height)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setSpacing(self._body.padding)

        # 遍历配置列表，动态生成按钮
        for text, key in self._buttons:
            btn = QPushButton(text)
            btn_id = f"btn_{key}"
            btn.setObjectName(btn_id)  # 用于 QSS 选择器 QPushButton#btn_key

            # 统一绑定点击事件
            btn.clicked.connect(
                lambda checked=False, bid=btn_id: self._handle_button(bid)
            )

            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()  # 把按钮推到左侧
        parent_layout.addWidget(toolbar)

    # ==================== 3. 事件分发 ====================

    def _handle_button(self, btn_id: str) -> None:
        """响应按钮点击事件"""
        action = self.action_map.get(btn_id)
        if action:
            action()

    # ==================== 4. 生命周期 ====================

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """处理窗口关闭时的生命周期事件"""
        # 1. 弹出确认框（这会阻塞当前线程，等待用户点击）
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要关闭机器人并退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        # 2. 用户点“是”
        if reply == QMessageBox.StandardButton.Yes:
            self._logger.info("用户确认退出，开始清理...")
            # 发送清理信号给 Bot
            gui_bridge.request_shutdown.emit()
            # 接受关闭事件，让窗口先关掉
            event.accept() 
        else:
            # 3. 用户点“否”，极其冷酷地拒绝关闭
            self._logger.info("用户取消退出")
            event.ignore()

    # ==================== 5. 对外暴露的 UI 操作接口 ====================

    def set_action_map(self, action_map: dict[str, Callable]) -> None:
        """注入按钮 ID 与回调函数的映射"""
        self.action_map = action_map

    def set_logger_handler(self) -> None:
        """将仪表盘文本处理器挂载到 Bot 日志器"""
        root_logger = get_logger()
        if (handler := self._text_handler) not in root_logger.handlers:
            handler.setLevel(logging.INFO)
            root_logger.addHandler(handler)

    def clear_dashboard(self) -> None:
        """清空仪表盘内容"""
        self._dashboard.clear()
