# src/gui/controllers/_settings.py
"""
GUI 控制器修改配置模块（内部实现）

- 显示当前配置
- 修改与保存
"""

import copy
import os
import tempfile
from pathlib import Path

import tomlkit
from PySide6.QtCore import QTimer

from utils.config import AppConfigData, AppSchema

from ..dialogs import NotChangedDialog, SettingsDialog
from ..mediator import gui_bridge
from ._base import BaseController


class SettingsController(BaseController):
    """配置控制器"""

    # ==================== 契约声明 ====================

    LOGGER_NAME = "GUI.Op.Settings"
    BTN_KEY = "setting"

    # ==================== 业务逻辑实现 ====================

    def _execute(self) -> None:
        """打开配置面板"""
        self.logger.info("正在打开配置面板...")

        data = gui_bridge.get_data()
        if data is not None:
            # 数据已初始化，打开弹窗
            self._schema, self._config = data
            self._show_dialog()
        else:
            # 数据未就绪，启动 QTimer 监听
            self.logger.info("配置尚未加载，正在等待后台注入...")
            self._start_waiting_timer()

    def _start_waiting_timer(self) -> None:
        """启动定时器监测配置是否注入"""
        self._wait_timer = QTimer(self.gui)
        self._wait_timer.setInterval(100)  # 每 100ms 检查一次
        self._wait_timer.timeout.connect(self._check_config_ready)
        self._wait_timer.start()

    def _check_config_ready(self) -> None:
        """检查配置是否就绪（数据非空 + 完整性校验）"""
        data = gui_bridge.get_data()
        if data is None:
            return

        schema, config = data
        if not self._is_config_complete(schema, config):
            self.logger.debug("配置尚未完全加载，继续等待...")
            return

        self._wait_timer.stop()
        self._schema = schema
        self._config = config
        self.logger.info("后台配置已注入，正在打开配置面板")
        self._show_dialog()

    def _is_config_complete(self, schema: AppSchema, config: AppConfigData) -> bool:
        """检查 config 是否包含 schema 定义的所有 namespace 和 key"""
        for tab in schema:
            ns = tab.namespace
            ns_config = config.get(ns)
            if ns_config is None:
                return False
            for field in tab.fields:
                if field.key not in ns_config:
                    return False
        return True

    def _compare_configs(
        self,
        schema: AppSchema,
        original_config: AppConfigData,
        ui_modified: AppConfigData,
    ) -> AppConfigData:
        """通过 TOML 往返消除 tomlkit 类型差异，直接比对数据"""
        # 深拷贝现有配置，在其上应用 UI 修改
        tmp_path:str| None = None
        merged = copy.deepcopy(original_config)
        for ns, fields in ui_modified.items():
            ns_config = merged.get(ns)
            if ns_config is None:
                ns_config = merged[ns] = {}
            for key, value in fields.items():
                if value is not None:
                    ns_config[key] = value

        # 写入临时文件再读取
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".toml")
            os.close(fd)

            with open(tmp_path, "w", encoding="utf-8") as f:
                tomlkit.dump(
                    original_config,
                    f,
                )
            with open(tmp_path, encoding="utf-8") as f:
                original = tomlkit.load(f)

            with open(tmp_path, "w", encoding="utf-8") as f:
                tomlkit.dump(merged, f)
            with open(tmp_path, encoding="utf-8") as f:
                modified = tomlkit.load(f)

            changes = {}
            for tab in schema:
                ns = tab.namespace
                ns_changes = {}
                for field in tab.fields:
                    ori = original.get(ns, {}).get(field.key)
                    mod = modified.get(ns, {}).get(field.key)
                    if ori != mod:
                        ns_changes[field.key] = mod
                if ns_changes:
                    changes[ns] = ns_changes

            return changes
        except Exception as e:
            self.logger.send_error("配置比对过程出错", e)
            return {}
        finally:
            if tmp_path is not None:
                Path(tmp_path).unlink(missing_ok=True)

    def _show_dialog(self) -> None:
        """真正执行弹窗的逻辑"""
        schema = self._schema
        config = self._config

        dialog = SettingsDialog(
            schema=schema,
            current_config=config,
            parent=self.gui,
        )

        if dialog.exec() == dialog.DialogCode.Accepted:
            new_config = dialog.get_modified_config()

            changes = self._compare_configs(schema, config, new_config)

            if not changes:
                self.logger.info("用户未修改任何配置")
                NotChangedDialog.show(parent=self.gui)
                return

            # 有修改，更新缓存，发信号
            gui_bridge.inject_data(schema, changes)
            self.logger.info("内存配置已更新，正在触发热重载...")
            gui_bridge.request_reload.emit()

        else:
            self.logger.info("用户取消了配置修改")
