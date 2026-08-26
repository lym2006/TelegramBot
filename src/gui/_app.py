# src/utils/gui/_app.py
"""
GUI 主窗口模块（内部实现）

提供：
- BotGUI 窗口类定义
- 界面布局构建
- 按钮事件分发
- 日志接入
"""

from collections.abc import Callable
from logging import Handler
from typing import Protocol

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.exception import ButtonRegisterError

from ._dashboard import DashboardWidget, TextHandler
from ._theme import SIZES, TOOLBAR_BUTTONS, WINDOW_CONFIG


def create_bot_gui() -> "BotGUI":
    """创建 BotGUI 实例"""
    return BotGUI()


# 定义一个拦截器协议
class _CloseInterceptorProtocol(Protocol):
    """窗口关闭拦截器协议（内部使用）"""

    def handle(self, event: QCloseEvent) -> None: ...


class BotGUI(QMainWindow):
    """Bot 专用可视化窗口"""

    # ==================== 1. 初始化 ====================
    def __init__(self) -> None:
        super().__init__()

        # 基础窗口属性设置
        self.setWindowTitle(WINDOW_CONFIG.title)
        self.resize(WINDOW_CONFIG.width, WINDOW_CONFIG.height)
        self.setMinimumSize(WINDOW_CONFIG.min_width, WINDOW_CONFIG.min_height)

        # 按钮事件映射表（按钮 ID -> 已包装的回调函数）
        self._action_map: dict[str, Callable] = {}

        # 仪表盘与文本处理器（纯 UI 组件，内部实例化）
        self.dashboard = DashboardWidget()
        self.text_handler: Handler = TextHandler(self.dashboard)

        # 窗口关闭拦截器（注入窗口关闭拦截器时使用）
        self._close_interceptor: _CloseInterceptorProtocol

        # 构建纯 UI 界面
        self._build_ui()

    # ==================== 2. 界面构建 ====================
    def _build_ui(self) -> None:
        """构建界面布局"""
        # 1. 中央容器
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        # 2. 主布局（垂直排列，工具栏在上，仪表盘在下）
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(
            SIZES.padding_x,
            SIZES.padding_y,
            SIZES.padding_x,
            SIZES.padding_y,
        )
        main_layout.setSpacing(SIZES.padding_between)

        # 3. 顶部工具栏
        self._build_toolbar(main_layout)

        # 4. 仪表盘区域
        main_layout.addWidget(self.dashboard)

    def _build_toolbar(self, parent_layout: QVBoxLayout) -> None:
        """构建顶部工具栏"""
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")  # 用于 QSS 选择器 #toolbar
        toolbar.setFixedHeight(SIZES.toolbar_height)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(
            SIZES.toolbar_padding_h,
            SIZES.toolbar_padding_v,
            SIZES.toolbar_padding_h,
            SIZES.toolbar_padding_v,
        )
        toolbar_layout.setSpacing(SIZES.padding_between)

        # 遍历配置列表，动态生成按钮
        for text, key in TOOLBAR_BUTTONS:
            btn = QPushButton(text)
            btn_id = f"btn_{key}"
            btn.setObjectName(btn_id)  # 用于 QSS 选择器 QPushButton#btn_key

            # 统一绑定点击事件
            btn.clicked.connect(
                lambda checked=False, bid=btn_id: self._handle_button(bid)
            )

            # 将按钮保存为实例属性（方便后续单独操作）
            setattr(self, btn_id, btn)
            toolbar_layout.addWidget(btn)

        # 把按钮推到左侧，右侧留白
        toolbar_layout.addStretch()
        parent_layout.addWidget(toolbar)

    # ==================== 3. 事件注册与分发 ====================
    def _handle_button(self, btn_id: str) -> None:
        """内部按钮分发器"""
        action = self._action_map.get(btn_id)
        if action:
            action()
        else:
            raise ButtonRegisterError(f"未注册的按钮: {btn_id}") from None

    def register_action(self, btn_id: str, callback: Callable) -> None:
        """供门面注入按钮回调"""
        self._action_map[btn_id] = callback

    # ==================== 4. 生命周期 ====================

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """触发事件拦截"""
        self._close_interceptor.handle(event)
