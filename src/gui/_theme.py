# src/gui/_theme.py
"""
GUI 主题模块（内部实现）

- 窗口布局配置
- Design Tokens（颜色、排版、尺寸）
"""

from dataclasses import dataclass
from pathlib import Path

from utils import ROOT_DIR

# ==================== 1. 窗口配置 ====================


@dataclass(frozen=True)
class WindowConfig:
    """窗口基础属性配置"""

    title: str = "Bot Manager"  # 窗口标题
    width: int = 1200  # 窗口默认宽度(px)
    height: int = 600  # 窗口默认高度(px)
    min_width: int = 600  # 窗口最小宽度(px)
    min_height: int = 300  # 窗口最小高度(px)


# ==================== 2. 全局/Reset ====================


@dataclass(frozen=True)
class GlobalConfig:
    """
    全局基础配置

    仅存放整个 App 共享的“视觉基因”
    """

    border_radius: int = 4  # 全局默认圆角(px)


# ==================== 3. 字体配置 ====================


@dataclass(frozen=True)
class FontConfig:
    """字体配置"""

    font_path: Path = ROOT_DIR / "assets/font.ttf"  # 主字体路径
    emoji_path: Path = ROOT_DIR / "assets/seguiemj.ttf"  # emoji 字体路径
    font_size: int = 11  # 全局字体大小(px)


# ==================== 4. Body（主窗口/中央容器） ====================


@dataclass(frozen=True)
class BodyConfig:
    """主窗口与中央容器配置"""

    bg: str = "#1E1E1E"  # 背景色
    color: str = "#D4D4D4"  # 文字色
    hover_color: str = "#FFFFFF"  # 悬停文字色
    selection_bg: str = "#264F78"  # 选中背景色
    padding: int = 8  # 仪表盘内边距(px)


# ==================== 5. Toolbar（顶部工具栏） ====================


@dataclass(frozen=True)
class ToolbarConfig:
    """工具栏配置"""

    bg: str = "#2D2D2D"  # 背景色
    height: int = 50  # 高度(px)
    padding_v: int = 8  # 垂直内边距(px)
    padding_h: int = 10  # 水平内边距(px)
    border_width: int = 1  # 底部分割线宽度(px)
    border_color: str = "#444444"  # 底部分割线颜色


# ==================== 6. Button（按钮） ====================


@dataclass(frozen=True)
class ButtonConfig:
    """按钮配置"""

    bg: str = "#3C3C3C"  # 默认背景色
    hover_bg: str = "#505050"  # 悬停背景色
    pressed_bg: str = "#2A2A2A"  # 按下背景色
    min_width: int = 100  # 最小宽度(px)
    height: int = 32  # 高度(px)
    padding_v: int = 6  # 垂直内边距(px)
    padding_h: int = 16  # 水平内边距(px)


# ==================== 7. Button Danger（危险按钮） ====================


@dataclass(frozen=True)
class ButtonDangerConfig:
    """危险操作按钮配置"""

    bg: str = "#D32F2F"  # 背景色
    hover_bg: str = "#B71C1C"  # 悬停色
    pressed_bg: str = "#9A0007"  # 按下色


# ==================== 8. Scrollbar（滚动条） ====================


@dataclass(frozen=True)
class ScrollbarConfig:
    """滚动条配置"""

    bg: str = "#1E1E1E"  # 轨道背景色
    handle_bg: str = "#555555"  # 滑块背景色
    handle_hover_bg: str = "#777777"  # 滑块悬停色
    width: int = 10  # 宽度(px)
    min_handle_height: int = 20  # 滑块最小高度(px)
    margin: int = 0  # 外边距(px)（清除默认间隙）
    arrow_height: int = 0  # 箭头高度(px)（隐藏默认箭头）


# ==================== 9. Dialog（弹窗） ====================


@dataclass(frozen=True)
class SettingsDialogConfig:
    """配置编辑弹窗专属配置"""

    min_width: int = 450  # 最小宽度(px)
    min_height: int = 350  # 最小高度(px)
    tab_min_width: int = 80  # 标签页标题最小宽度(px)
    tab_padding_v: int = 6  # 标签页垂直内边距(px)
    tab_padding_h: int = 16  # 标签页水平内边距(px)
    tab_spacing: int = 12  # 标签页内部控件间距
    tab_bg: str = "#2D2D2D"  # 标签页背景色
    input_padding_v: int = 6  # 输入框垂直内边距(px)
    input_padding_h: int = 8  # 输入框水平内边距(px)
    border_width: int = 1  # 边框宽度(px)
    border_color: str = "#444444"  # 边框色
    finish_btn_min_width: int = 150  # “完成”按钮最小宽度(px)


@dataclass(frozen=True)
class ShutdownDialogConfig:
    """退出拦截弹窗专属配置"""

    width: int = 300  # 宽度(px)
    height: int = 80  # 高度(px)
    icon_size: int = 24  # 加载动画尺寸(px)
    message: str = "正在安全退出，请稍候..."  # 提示文案


# ==================== 10. 实例化配置 ====================

# 在模块级别实例化，供外部导入使用
WINDOW = WindowConfig()
FONT = FontConfig()
GLOBAL = GlobalConfig()
BODY = BodyConfig()
TOOLBAR = ToolbarConfig()
BTN = ButtonConfig()
BTN_DANGER = ButtonDangerConfig()
SCROLLBAR = ScrollbarConfig()
SETTINGS_DIALOG = SettingsDialogConfig()
SHUTDOWN_DIALOG = ShutdownDialogConfig()

# ==================== 11. 按钮列表 ====================

TOOLBAR_BUTTONS = [
    ("修改配置", "setting"),
    ("查看日志", "log"),
    ("检查更新", "update"),
    ("清空仪表盘", "clear"),
]
