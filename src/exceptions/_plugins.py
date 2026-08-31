# src/exceptions/_plugins.py
"""插件异常（内部实现）"""

from ._base import BotError

# ==================== 总插件异常 ====================


class PluginsError(BotError):
    """插件异常基类"""


class PluginsMissingError(PluginsError):
    """未注册插件"""


# ==================== AI 插件异常 ====================


class AIError(PluginsError):
    """AI 插件异常基类"""


class AITaskStoppedError(AIError):
    """AI 任务被意外中断或停止时触发的异常"""
