# src/exceptions/__init__.py
"""
自定义异常门面

- 所有自定义异常
"""

from ._base import BotError
from ._config import (
    ConfigAttrError,
    ConfigError,
    ConfigInputError,
    ConfigMissingError,
    ConfigOutputError,
    ConfigParseError,
    ConfigTemplateMissingError,
)
from ._gui import (
    DashboardWriteError,
    FontError,
    FontFamilyError,
    FontLoadError,
    FontMissingError,
    FontRegisterError,
    GUIError,
)
from ._network import (
    ConnectionFailedError,
    HTTPStatusError,
    NetworkError,
    RequestTimeoutError,
)
from ._plugins import AIError, AITaskStoppedError, PluginsMissingError

__all__ = [
    # 基类
    "BotError",
    # 配置系统
    "ConfigError",
    "ConfigMissingError",
    "ConfigTemplateMissingError",
    "ConfigInputError",
    "ConfigOutputError",
    "ConfigParseError",
    "ConfigAttrError",
    # 网络与 API
    "NetworkError",
    "HTTPStatusError",
    "RequestTimeoutError",
    "ConnectionFailedError",
    # GUI
    "GUIError",
    "DashboardWriteError",
    "FontError",
    "FontMissingError",
    "FontLoadError",
    "FontRegisterError",
    "FontFamilyError",
    # 插件
    "PluginsMissingError",
    "AIError",
    "AITaskStoppedError",
]
