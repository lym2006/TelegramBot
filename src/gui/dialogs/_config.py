# src/gui/dialogs/_config.py
"""
GUI 配置修改弹窗模块（内部实现）

负责：
- 渲染多标签页的配置表单
- 提供获取修改后配置的接口
- 区分正常编辑模式和缺失引导模式
"""

from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLabel,
    QCheckBox,
    QScrollArea,
    QFrame,
)

from .._theme import COLORS, DIALOG_SIZES, SIZES
from ._base import BaseDialog

from utils.config import AppConfigData,AppSchema,ConfigValue

class ConfigMode(Enum):
    """配置弹窗的工作模式"""

    EDIT = auto()  # 正常编辑模式（用户主动点击“修改配置”）
    SETUP = auto()  # 缺失引导模式（检测到缺失配置，强制用户填写）


class ConfigDialog(BaseDialog):
    """配置面板弹窗"""

    def __init__(
        self,
        schema: AppSchema,
        current_config: AppConfigData,
        mode: ConfigMode = ConfigMode.EDIT,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent, title="修改配置")

        self._schema = schema       
        self._current = current_config
        self._mode = mode

        # 记录所有控件，格式: {("tab_title", "field_key"): widget}
        self._inputs: dict[tuple[str, str], QWidget] = {}

        # 引导模式下，禁止用户直接关闭弹窗
        if mode == ConfigMode.SETUP:
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self.setMinimumSize(DIALOG_SIZES.min_width, DIALOG_SIZES.min_height)
        self._build_ui()

    def _build_ui(self) -> None:
        """构建界面"""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(*([DIALOG_SIZES.input_padding_h] * 4))
        root_layout.setSpacing(SIZES.padding_between)

        # 1. 如果是引导模式，顶部加一句提示语
        if self._mode == ConfigMode.SETUP:
            tip_label = QLabel("检测到配置文件缺失或存在新增项，请完善以下配置后继续：")
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet(f"color: {COLORS.text_hover}")
            root_layout.addWidget(tip_label)

        # 2. 标签页容器
        tabs = QTabWidget()
        for tab_info in self._schema:
            tab_title:str=tab_info.title
            for tab in tab_info.fields:
                tab_widget = self._create_tab(tab)
                tabs.addTab(tab_widget, tab_info.fields)
        root_layout.addWidget(tabs)

        # 3. 底部按钮区
        root_layout.addLayout(self._build_bottom_buttons())

    def _create_tab(self, tab_info: dict) -> QWidget:
        """创建一个包含多个 Section 的 Tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # 让滚动区域背景透明，继承 Dialog 的背景
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(SIZES.padding_between * 2)

        for section in tab_info["sections"]:
            section_widget = self._create_section(section)
            main_layout.addWidget(section_widget)

        main_layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_section(self,sectin:)

    def _build_bottom_buttons(self) -> QHBoxLayout:
        """根据当前模式，动态构建底部按钮布局"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SIZES.padding_between)
        btn_layout.addStretch()  # 将按钮统一推向右侧

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
                btn_finish.setMinimumWidth(150)
                btn_finish.clicked.connect(self.accept)

                btn_layout.addWidget(btn_finish)

        return btn_layout