# src/gui/_main_window.py
"""
GUI 主窗口模块（内部实现）

- BotGUI 窗口类（纯 UI 渲染与指令执行层）
"""

import logging
from collections.abc import Callable

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.logger import get_logger

from ._dashboard import DashboardWidget, TextHandler
from ._theme import BodyConfig, FontConfig, ToolbarConfig, WindowConfig


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
    ) -> None:
        super().__init__()
        self._qss = qss
        self._buttons = buttons
        self._fonts, self._windows, self._body, self._toolbar = configs
        self._hidden_actions = {"shutdown"}  # 不渲染只回调的按钮

        self._logger = get_logger("GUI")

        # 基础窗口属性设置
        self.setWindowTitle(self._windows.title)
        self.resize(self._windows.width, self._windows.height)
        self.setMinimumSize(self._windows.min_width, self._windows.min_height)

        # 按钮事件映射表（按钮 ID -> 已包装的回调函数）
        self.action_map: dict[str, Callable] = {}

        # 仪表盘与文本处理器（纯 UI 组件，内部实例化）
        self._dashboard = DashboardWidget(self._fonts)
        self._text_handler: logging.Handler = TextHandler(self._dashboard, formatter)

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
            btn_id = f"btn_{key}"

            if key in self._hidden_actions:
                continue  # 直接跳过按钮的创建和布局添加

            btn = QPushButton(text)
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
        """拦截窗口关闭"""
        # 拦截原生关闭事件，用户应当点击任务栏按钮=
        event.ignore()
        self._handle_button("btn_shutdown")

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
