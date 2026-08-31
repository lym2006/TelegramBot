# src/exceptions/_gui.py
"""GUI 异常（内部实现）"""

from ._base import BotError


class GUIError(BotError):
    """GUI 异常基类"""


class DashboardWriteError(GUIError):
    """仪表盘写入异常"""


# ==================== 字体异常 ====================


class FontError(GUIError):
    """字体异常基类"""


class FontMissingError(FontError):
    """字体文件缺失异常"""


class FontLoadError(FontError):
    """字体文件加载异常"""


class FontRegisterError(FontError):
    """字体文件注册异常"""


class FontFamilyError(FontError):
    """字体家族名获取异常"""
