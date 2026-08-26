# src/gui/_theme.py
"""
GUI 主题模块（内部实现）

提供：
- 窗口布局配置
- 颜色配置
- 按钮配置
- 字体配置
- QSS 全局样式表（自动注入颜色配置）
"""

from dataclasses import dataclass

from utils import ROOT_DIR


# ==================== 1. 窗口配置 ====================
@dataclass(frozen=True)
class WindowConfig:
    """窗口基础属性配置"""

    title: str = "Bot Manager"  # 窗口标题
    width: int = 1200  # 窗口默认宽度
    height: int = 600  # 窗口默认高度
    min_width: int = 600  # 窗口最小宽度
    min_height: int = 300  # 窗口最小高度


# ==================== 2. 颜色配置 ====================
@dataclass(frozen=True)
class ColorPalette:
    """全局颜色调色板"""

    bg: str = "#1E1E1E"  # 主背景色
    text: str = "#D4D4D4"  # 主文字色
    text_hover: str = "#FFFFFF"  # 悬停时的文字色
    toolbar_bg: str = "#2D2D2D"  # 工具栏背景色
    btn_bg: str = "#3C3C3C"  # 按钮默认背景色
    btn_hover: str = "#505050"  # 按钮悬停背景色
    btn_pressed: str = "#2A2A2A"  # 按钮按下背景色
    danger: str = "#D32F2F"  # 危险操作按钮颜色（清空仪表盘）
    danger_hover: str = "#B71C1C"  # 危险按钮悬停色
    danger_pressed: str = "#9A0007"  # 危险按钮按下色
    border: str = "#444444"  # 边框颜色
    selection_bg: str = "#264F78"  # 文本选中背景色
    scrollbar: str = "#555555"  # 滚动条背景色
    scrollbar_hover: str = "#777777"  # 滚动条悬停色


# ==================== 3. 布局与尺寸 ====================
@dataclass(frozen=True)
class SizeConfig:
    """全局尺寸与布局配置"""

    padding_x: int = 10  # 水平边距
    padding_y: int = 10  # 垂直边距
    padding_between: int = 8  # 控件之间的间距
    btn_min_width: int = 100  # 按钮最小宽度
    btn_height: int = 32  # 按钮高度
    toolbar_height: int = 50  # 工具栏高度
    border_radius: int = 4  # 按钮圆角
    btn_padding_v: int = 6  # 按钮垂直内边距
    btn_padding_h: int = 16  # 按钮水平内边距
    dashboard_padding: int = 8  # 仪表盘内边距
    scrollbar_width: int = 10  # 滚动条宽度
    scrollbar_min_height: int = 20  # 滚动条滑块最小高度
    border_width: int = 1  # 边框宽度
    scrollbar_margin: int = 0  # 滚动条外边距（清除默认间隙）
    scrollbar_arrow_height: int = 0  # 滚动条箭头高度（隐藏默认箭头）
    toolbar_padding_v: int = 8  # 工具栏垂直内边距
    toolbar_padding_h: int = 10  # 工具栏水平内边距


# ==================== 4. 弹窗尺寸配置 ====================
@dataclass(frozen=True)
class DialogSizeConfig:
    """弹窗专属尺寸配置"""

    min_width: int = 450  # 配置弹窗最小宽度
    min_height: int = 350  # 配置弹窗最小高度
    tab_min_width: int = 80  # 标签页标题最小宽度
    input_padding_v: int = 6  # 输入框垂直内边距
    input_padding_h: int = 8  # 输入框水平内边距


# ==================== 5. 按钮配置列表 ====================
TOOLBAR_BUTTONS = [
    ("修改配置", "config"),
    ("查看日志", "log"),
    ("检查更新", "update"),
    ("清空仪表盘", "clear"),
]

# ==================== 6. 字体配置 ====================
FONT_PATH = ROOT_DIR / "assets/font.ttf"
EMOJI_FONT_PATH = ROOT_DIR / "assets/seguiemj.ttf"
FONT_SIZE = 11

# ==================== 7. 实例化配置 ====================
# 在模块级别实例化，供外部导入使用
WINDOW_CONFIG = WindowConfig()
DIALOG_SIZES = DialogSizeConfig()
COLORS = ColorPalette()
SIZES = SizeConfig()

# ==================== 8. QSS 全局样式表 ====================
# 使用了 f-string，花括号必须双写 {{ }}
# 所有的颜色、尺寸、圆角等全部从上方字典动态注入
GLOBAL_QSS = f"""
/* 主窗口背景 */
QMainWindow {{
    background-color: {COLORS.bg};
}}

/* 中央容器 */
QWidget#centralWidget {{
    background-color: {COLORS.bg};
}}

/* 顶部工具栏 */
QWidget#toolbar {{
    background-color: {COLORS.toolbar_bg};
    border-bottom: {SIZES.border_width}px solid {COLORS.border};
}}

/* 按钮基础样式 */
QPushButton {{
    background-color: {COLORS.btn_bg};
    color: {COLORS.text};
    border: none;
    border-radius: {SIZES.border_radius}px;
    padding: {SIZES.btn_padding_v}px {SIZES.btn_padding_h}px;
    font-weight: bold;
    min-width: {SIZES.btn_min_width}px;
    min-height: {SIZES.btn_height}px;
}}

/* 按钮悬停 */
QPushButton:hover {{
    background-color: {COLORS.btn_hover};
    color: {COLORS.text_hover};
}}

/* 按钮按下 */
QPushButton:pressed {{
    background-color: {COLORS.btn_pressed};
}}

/* 清空仪表盘按钮 - 红色警示 */
QPushButton#btn_clear {{
    background-color: {COLORS.danger};
}}

QPushButton#btn_clear:hover {{
    background-color: {COLORS.danger_hover};
}}

QPushButton#btn_clear:pressed {{
    background-color: {COLORS.danger_pressed};
}}

/* 仪表盘文本区域 */
QTextEdit#dashboard {{
    background-color: {COLORS.bg};
    color: {COLORS.text};
    border: none;
    padding: {SIZES.dashboard_padding}px;
    selection-background-color: {COLORS.selection_bg};
    selection-color: {COLORS.text_hover};
}}

/* 垂直滚动条美化 */
QScrollBar:vertical {{
    background: {COLORS.bg};
    width: {SIZES.scrollbar_width}px;
    border: none;
    margin: {SIZES.scrollbar_margin}px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS.scrollbar};
    border-radius: {SIZES.scrollbar_width // 2}px;
    min-height: {SIZES.scrollbar_min_height}px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS.scrollbar_hover};
}}

/* 隐藏滚动条默认的上下箭头按钮 */
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: {SIZES.scrollbar_arrow_height}px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}
"""

# ==================== 9. 弹窗专属样式 ====================
DIALOG_QSS = f"""
/* 弹窗整体背景 */
QDialog {{
    background-color: {COLORS.bg};
}}

/* 弹窗标签页容器 */
QTabWidget::pane {{
    border: {SIZES.border_width}px solid {COLORS.border};
    background-color: {COLORS.bg};
}}

/* 标签页标题栏 */
QTabBar::tab {{
    background-color: {COLORS.toolbar_bg};
    color: {COLORS.text};
    padding: {SIZES.btn_padding_v}px {SIZES.btn_padding_h}px;
    min-width: 80px;
    border-top-left-radius: {SIZES.border_radius}px;
    border-top-right-radius: {SIZES.border_radius}px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS.bg};
    color: {COLORS.text_hover};
}}

/* 弹窗表单标签 */
QLabel {{
    color: {COLORS.text};
}}

/* 弹窗输入框 */
QLineEdit {{
    background-color: {COLORS.toolbar_bg};
    color: {COLORS.text};
    border: {SIZES.border_width}px solid {COLORS.border};
    border-radius: {SIZES.border_radius}px;
    padding: {SIZES.btn_padding_v}px;
}}

QLineEdit:focus {{
    border: {SIZES.border_width}px solid {COLORS.selection_bg};
}}
"""
