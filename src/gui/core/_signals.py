# src/gui/core/_signals.py
"""
GUI 核心信号桥模块（内部实现）

- 定义 GUI 与 Bot 之间的通信协议
- 提供全局单例，避免循环导入
"""

import threading

from PySide6.QtCore import QObject, Signal


class GUIBridge(QObject):
    """GUI 与 Bot 之间的通信桥梁"""

    # === 关闭流程相关信号 ===

    # 用户点击确认，GUI 请求退出，Bot 收到后开始清理
    request_shutdown: Signal = Signal()

    # Bot 清理完，设置为 set，Controller 中监测事件状态
    shutdown_completed_event = threading.Event()

    # === 业务交互相关信号 ===

    # 用户在配置弹窗中点击了"保存"
    # 参数: 完整的配置字典
    config_updated: Signal = Signal(object)

    # 通知底层热加载
    request_reload: Signal = Signal()

    # 补全后台数据回灌的通信契约
    # 参数: UI渲染契约(Schema) + 真实配置数据(Config)
    real_config_loaded: Signal = Signal(object, object)


# 全局单例实例化
gui_bridge: GUIBridge = GUIBridge()
