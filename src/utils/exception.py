# src/utils/exception.py
"""
全局自定义异常

集中管理项目中所有的业务异常，避免循环导入问题
"""

from typing import Any


# ==================== 1. 全局异常基类 ====================
class BotError(Exception):
    """Bot 自定义异常基类"""


# ==================== 2. 配置系统异常 ====================
class ConfigError(BotError):
    """配置系统异常基类"""


class ConfigMissingError(ConfigError):
    """配置文件缺失异常"""


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
        type_name = expected_type.__name__ if expected_type else "未知"
        super().__init__(
            f"配置错误: '{key_path}' 期望 {type_name}"
            f"{'，当前值为 None（未填写）' if actual_value is None else f'，实际类型为 {type(actual_value).__name__}'}"
        )


# ==================== 3. 网络与 API 异常 ====================
class NetworkError(BotError):
    """网络请求异常基类"""


class HTTPStatusError(NetworkError):
    """HTTP 状态码异常"""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class RequestTimeoutError(NetworkError):
    """请求超时异常"""


class ConnectionFailedError(NetworkError):
    """连接失败异常"""


# ==================== 4. GUI 异常 ====================
class GUIError(BotError):
    """GUI 异常基类"""


class DashboardWriteError(GUIError):
    """仪表盘写入异常"""


class ButtonRegisterError(GUIError):
    """按钮注册异常"""


# ==================== 4.1 GUI 异常 ====================
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


# ==================== 5. AI 插件异常 ====================
class AIError(BotError):
    """AI 插件异常基类"""


class AITaskStoppedError(AIError):
    """AI 任务被意外中断或停止时触发的异常"""
