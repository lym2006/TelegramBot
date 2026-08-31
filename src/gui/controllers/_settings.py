# src/gui/controllers/_settings.py
"""
GUI 控制器修改配置模块（内部实现）

- 显示当前配置
- 修改与保存
"""

from utils.config import AppConfigData, AppSchema

from ..core import gui_bridge
from ..dialogs import SettingsDialog
from ._base import BaseController


class SettingsController(BaseController):
    """配置控制器"""

    # ==================== 契约声明 ====================
    LOGGER_NAME = "GUI.Op.Settings"
    BTN_KEY = "setting"

    # ==================== 数据注入 ====================

    def __init__(
        self,
        schema: AppSchema,
        current_config: AppConfigData,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._schema = schema
        self._current_config = current_config

    # ==================== 状态刷新（供 AppController 调用）====================

    def update_data(self, schema: AppSchema, current_config: AppConfigData) -> None:
        """当后台真实配置加载完成后，由 AppController 调用此方法刷新内存数据"""
        self._schema = schema
        self._current_config = current_config
        self.logger.info("✅ SettingsController 已刷新真实配置")

    # ==================== 业务逻辑实现 ====================
    def _execute(self) -> None:
        """打开配置面板"""
        self.logger.info("⚙️ 正在打开配置面板...")

        # 1. 极其丝滑地组装数据并弹出弹窗
        dialog = SettingsDialog(
            schema=self._schema,  # 获取表单结构
            current_config=self._current_config,  # 获取当前配置
            parent=self.gui,  # 绑定父窗口
        )

        # 2. 阻塞等待用户操作
        if dialog.exec() == dialog.DialogCode.Accepted:
            # 3. 用户点击了“保存”，拿回新数据
            new_config = dialog.get_modified_config()

            # 4. 发射信号并传出数据
            self.logger.info("💾 正在保存配置...")
            gui_bridge.config_updated.emit(new_config)
        else:
            # 用户点击了“取消”，极其冷酷地放弃所有修改
            self.logger.info("❌ 用户取消了配置修改")
