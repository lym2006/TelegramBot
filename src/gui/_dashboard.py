# src/utils/gui/_dashboard.py
"""
GUI 仪表盘模块（内部实现）

提供：
- 线程安全的日志重定向机制
- 支持自定义字体的仪表盘组件
"""

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor
from PySide6.QtWidgets import QTextEdit

from utils.exception import (
    DashboardWriteError,
    FontError,
    FontFamilyError,
    FontLoadError,
    FontMissingError,
    FontRegisterError,
)
from utils.logger import FORMATTER

from ._theme import (
    EMOJI_FONT_PATH,
    FONT_PATH,
    FONT_SIZE,
)

FontType = tuple[QFont, str, str]


# ==================== 1. 线程安全信号桥 ====================
class _LogSignal(QObject):
    """
    日志信号桥接器

    通过 Signal/Slot 机制，将后台线程的日志安全地排队到主线程渲染
    """

    log_received = Signal(str)


# ==================== 2. 日志处理器 ====================
class TextHandler(logging.Handler):
    """
    自定义日志处理器

    将 logging 输出重定向到 DashboardWidget
    使用 Qt 的 Signal/Slot 机制保证线程安全
    """

    def __init__(self, widget: "DashboardWidget") -> None:
        super().__init__()
        self._widget = widget

        # 创建信号桥接器并连接到 UI 更新方法
        self._signal = _LogSignal()
        self._signal.log_received.connect(self._append_text)

        # 设置默认日志格式
        self.setFormatter(FORMATTER)

    def emit(self, record: logging.LogRecord) -> None:
        """当日志产生时，格式化后通过信号发送到主线程

        日志记录对象包含日志级别、消息、时间等元数据
        """
        try:
            # 将日志记录格式化为字符串，并追加换行符
            msg: str = self.format(record) + "\n"
            # 发射信号，Qt 事件循环会自动将此调用排队到主线程执行
            self._signal.log_received.emit(msg)

        except Exception as e:
            raise DashboardWriteError(f"❌ GUI 日志格式化或发送失败: {e}") from e

    @Slot(str)
    def _append_text(self, msg: str) -> None:
        """
        在主线程中实际写入文本框

        由 Signal/Slot 机制自动调度到主线程执行
        """
        try:
            # 1. 移动光标到文本末尾
            cursor = self._widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            # 2. 插入日志文本
            cursor.insertText(msg)

            # 3. 自动滚动到底部，确保最新日志可见
            scrollbar = self._widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            raise DashboardWriteError(f"❌ GUI 写入日志出错: {e}\n") from e


# ==================== 3. 仪表盘组件 ====================
class DashboardWidget(QTextEdit):
    """
    仪表盘组件

    封装只读文本框 + 自定义字体加载
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # 1. 基础属性设置
        self.setReadOnly(True)
        self.setObjectName("dashboard")  # 用于 QSS 选择器 #dashboard

        # 2. 加载并应用自定义字体
        self.setFont(self._load_font(FONT_PATH)[0])

        # 3. 加载 Emoji 字体作为回退
        self._load_font(EMOJI_FONT_PATH, silent=True)

    def _load_font(self, font_path: Path, silent: bool = False) -> FontType:
        """加载自定义字体文件到 Qt 字体数据库"""

        # 1. 将失败兜底逻辑打包成内部闭包
        def _handle_failure(exc: Exception) -> FontType:
            if silent:
                return self._get_fallback_font()
            raise exc

        # 2. 检查文件是否存在
        if not font_path.exists():
            return _handle_failure(FontMissingError(f"🚨 字体文件不存在: {font_path}"))

        try:
            # 3. 尝试加载字体
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id == -1:
                return _handle_failure(
                    FontLoadError(f"❌ Qt 无法加载字体文件: {font_path}")
                )

            # 4. 获取字体家族名
            families = QFontDatabase.applicationFontFamilies(font_id)
            if not families:
                return _handle_failure(
                    FontFamilyError(f"❌ 字体文件无法获取家族名: {font_path}")
                )

            return QFont(families[0], FONT_SIZE), str(font_path), families[0]

        except FontError:
            # 业务异常直接向上抛
            raise

        except Exception as e:
            # 未知异常包装为注册异常
            err = FontRegisterError(f"注册字体失败 [{font_path}]: {e}")
            err.__cause__ = e  # 手动绑定底层堆栈（等同于 raise ... from e）
            return _handle_failure(err)

    @staticmethod
    def _get_fallback_font() -> FontType:
        """获取系统默认的等宽兜底字体"""
        fallback = QFont("Consolas", FONT_SIZE)
        fallback.setStyleHint(QFont.StyleHint.Monospace)
        return fallback, "系统默认", "Consolas"
