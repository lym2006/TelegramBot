# src/gui/core/_signals.py
"""
GUI 核心信号桥模块（内部实现）

负责：
- 定义 GUI 与 Bot 之间的通信协议
- 提供全局单例，避免循环导入
"""

from PySide6.QtCore import QObject, Signal


class GUIBridge(QObject):
    """GUI 与 Bot 之间的通信桥梁"""

    # === 关闭流程相关信号 ===

    # 1. 用户点击了窗口的 X，拦截器捕获到关闭意图
    # 用途：通知 dialogs 模块弹出确认框
    close_intercepted: Signal = Signal()

    # 2. 用户在确认框中点击了"确认"，同意退出
    # 用途：通知 bot.py 开始执行全局资源清理
    shutdown_confirmed: Signal = Signal()

    # === 业务交互相关信号 ===

    # 3. 用户在配置弹窗中点击了"保存"
    # 参数 config_path: 配置文件的路径
    config_reloaded: Signal = Signal(str)


# 全局单例实例化
gui_bridge: GUIBridge = GUIBridge()
