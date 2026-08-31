# src/exceptions/_config.py
"""配置系统异常（内部实现）"""

from typing import Any

from ._base import BotError


class ConfigError(BotError):
    """配置系统异常基类"""


class ConfigMissingError(ConfigError):
    """配置文件缺失异常（可恢复）"""


class ConfigTemplateMissingError(ConfigError):
    """配置模板缺失异常（致命：缺失 example.toml，程序无法继续执行）"""


class ConfigInputError(ConfigError):
    """配置文件读取异常"""


class ConfigOutputError(ConfigError):
    """配置文件写入异常"""


class ConfigParseError(ConfigError):
    """配置文件解析异常"""


class ConfigAttrError(ConfigError):
    """配置取值异常：类型不匹配或键不存在"""

    def __init__(
        self, key_path: str, expected_type: type, actual_value: Any = None
    ) -> None:
        self.key_path = key_path
        self.expected_type = expected_type
        self.actual_value = actual_value
        super().__init__()
