# src/gui/dialogs/_settings.py
"""
GUI 配置修改弹窗模块（内部实现）

- 渲染多标签页的配置表单
- 提供获取修改后配置的接口
- 区分正常编辑模式和缺失引导模式
"""

from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from utils.config.models import (
    AppConfigData,
    AppSchema,
    FieldSchema,
    TabData,
    TabSchema,
)

from .._qss import build_settings_dialog_qss
from .._theme import GLOBAL
from .._theme import SETTINGS_DIALOG as DIALOG
from ._base import BaseDialog


class ConfigMode(Enum):
    """配置弹窗的工作模式"""

    EDIT = auto()  # 正常编辑模式（用户主动点击“修改配置”）
    SETUP = auto()  # 缺失引导模式（检测到缺失配置，强制用户填写）


class SettingsDialog(BaseDialog):
    """配置面板弹窗"""

    def __init__(
        self,
        schema: AppSchema,
        current_config: AppConfigData,
        mode: ConfigMode = ConfigMode.EDIT,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent, title="修改配置")

        # 加载QSS
        self.setStyleSheet(build_settings_dialog_qss())

        self._schema = schema
        self._current = current_config
        self._mode = mode

        # 记录所有输入控件，格式: {"field_key": widget}
        self._inputs: dict[str, QLineEdit] = {}

        # 引导模式下，禁止用户直接关闭弹窗
        if mode == ConfigMode.SETUP:
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self.setMinimumSize(DIALOG.min_width, DIALOG.min_height)
        self._build_ui()

    def get_modified_config(self) -> AppConfigData:
        """从所有输入控件中提取修改后的配置字典"""
        modified: AppConfigData = {}
        for tab in self._schema:
            tab_data: TabData = {}
            for field in tab.fields:
                widget = self._inputs.get(field.key)
                if widget:
                    tab_data[field.key] = widget.text().strip()
            modified[tab.namespace] = tab_data
        return modified

    def _build_ui(self) -> None:
        """构建界面"""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            *([DIALOG.input_padding_h, DIALOG.input_padding_v] * 2)
        )
        root_layout.setSpacing(DIALOG.tab_spacing)

        # 如果是引导模式，顶部加一句提示语
        if self._mode == ConfigMode.SETUP:
            tip_label = QLabel(
                "🔍 检测到配置文件缺失或存在新增项，请完善以下配置后继续："
            )
            tip_label.setWordWrap(True)
            root_layout.addWidget(tip_label)

        # 标签页容器
        tabs = QTabWidget()
        for tab_schema in self._schema:
            tab_widget = self._create_tab(tab_schema)
            tabs.addTab(tab_widget, tab_schema.title)

        root_layout.addWidget(tabs)

        # 底部按钮区
        root_layout.addLayout(self._build_bottom_buttons())

    def _create_tab(self, tab_schema: TabSchema) -> QWidget:
        """创建一个包含多个字段的 Tab"""
        # 创建滚动区域（当表单字段太多时，允许上下滑动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # 使用调色板强制背景透明
        palette = scroll.palette()
        palette.setBrush(scroll.backgroundRole(), Qt.GlobalColor.transparent)
        scroll.setPalette(palette)

        # 关闭自动填充背景
        scroll.setAutoFillBackground(False)

        # 创建内容容器（装载表单控件）
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(DIALOG.tab_spacing)

        for field in tab_schema.fields:
            field_widget = self._create_field(field, tab_schema.namespace)
            main_layout.addWidget(field_widget)

        main_layout.addStretch()  # 把按钮推到上方

        scroll.setWidget(container)
        return scroll

    def _create_field(self, field: FieldSchema, namespace: str) -> QWidget:
        """根据字段类型渲染对应的表单控件"""
        # 创建容器并绑定表单布局
        container = QWidget()
        form = QFormLayout(container)
        form.setSpacing(GLOBAL.border_radius)

        # 获取当前配置中的值
        current_value = self._current.get(namespace, {}).get(field.key, field.default)

        # 渲染输入框并填入提取到的值
        input_widget = QLineEdit(str(current_value))
        input_widget.setPlaceholderText(field.desc)

        # 记录控件引用（外部点击“保存”时，通过字典找到输入框并获取文本）
        self._inputs[field.key] = input_widget

        # 将“标题”和“输入框”组装成一行
        form.addRow(QLabel(field.label), input_widget)

        return container

    def _build_bottom_buttons(self) -> QHBoxLayout:
        """根据当前模式，动态构建底部按钮布局"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(GLOBAL.border_radius)
        btn_layout.addStretch()  # 把按钮推到右侧

        match self._mode:
            case ConfigMode.EDIT:
                # 正常模式：取消 + 保存
                btn_cancel = QPushButton("取消")
                btn_cancel.clicked.connect(self.reject)

                btn_save = QPushButton("保存")
                btn_save.setObjectName("btn_primary")  # 绑定 QSS 主按钮样式
                btn_save.clicked.connect(self.accept)

                btn_layout.addWidget(btn_cancel)
                btn_layout.addWidget(btn_save)
            case ConfigMode.SETUP:
                # 引导模式：完成并保存
                btn_finish = QPushButton("完成并保存")
                btn_finish.setObjectName("btn_primary")
                btn_finish.setMinimumWidth(DIALOG.finish_btn_min_width)
                btn_finish.clicked.connect(self.accept)

                btn_layout.addWidget(btn_finish)

        return btn_layout
