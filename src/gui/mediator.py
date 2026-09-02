# src/gui/mediator.py
"""
GUI 中介者模块

- 定义 GUI 与 Bot 之间的通信协议（Signal）
- 提供跨线程状态同步屏障（Event）
- 提供全局共享数据的安全注入与获取方法
"""

import copy
import threading

from PySide6.QtCore import QObject, Signal

from utils.config import AppConfigData, AppSchema


class GUIBridge(QObject):
    """GUI 与 Bot 之间的通信桥梁"""

    # 锁死对象属性结构，防止外部意外挂载临时变量污染全局状态
    __slots__ = ("_schema", "_config")

    # ==================== 关闭流程相关信号 ====================

    # 用户点击确认，GUI 请求退出，Bot 收到后开始清理
    request_shutdown: Signal = Signal()

    # Bot 清理完，设置为 set，Controller 中监测事件状态
    shutdown_completed_event = threading.Event()

    # ==================== 业务交互相关信号 ====================

    # ==================== 配置数据相关信号 ====================

    # 用于外部判断数据是否准备就绪
    # is_ready: bool = False

    # 配置成功注入，通知等待中的进程
    data_ready = Signal()

    # 配置修改完成，通知底层热加载
    request_reload: Signal = Signal()

    # 全局私有状态
    _schema: AppSchema
    _config: AppConfigData

    # 只读属性（供外部读取）
    @property
    def schema(self) -> AppSchema:
        """外部获取 schema"""
        return self._schema

    @property
    def config(self) -> AppConfigData:
        """外部获取 config"""
        return self._config

    # ==================== 状态写入方法 ====================

    def set_data(self, schema: AppSchema, config: AppConfigData) -> None:
        """首次注入完整数据"""
        self._schema = schema
        self._config = copy.deepcopy(config)

        # 注入成功，自动广播
        # self.is_ready = True
        self.data_ready.emit()

    def update_config(self, changes: AppConfigData) -> None:
        """增量合并配置到现有缓存"""
        for ns, fields in changes.items():
            # 获取子字典的内存引用，直接修改即可同步到全局缓存
            ns_ref = self._config.get(ns)
            if ns_ref is None:
                ns_ref = self._config[ns] = {}
            for key, value in fields.items():
                if value is not None:
                    ns_ref[key] = value

        # 更新成功，自动广播
        self.request_reload.emit()


# 全局单例实例化
gui_bridge: GUIBridge = GUIBridge()
