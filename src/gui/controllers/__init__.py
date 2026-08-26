# src/gui/controllers/__init__.py
"""
GUI 控制器门面模块

负责：
- 统一导入所有业务控制器，并打包供上层组装
"""

from ._config import ConfigController
from ._dashboard import DashboardController
from ._shutdown import ShutdownController
from ._system import LogsController, UpdateController

__all__ = [
    "DashboardController",
    "ConfigController",
    "LogsController",
    "UpdateController",
    "ShutdownController",
]

# 把所有 Controller 类收集到一个元组里
ALL_CONTROLLERS = tuple(globals()[name] for name in __all__)
