# src/utils/__init__.py
"""
通用工具门面

- 网络客户端、日志、配置、生命周期管理
"""

from ._base_client import BaseClient
from ._check_version import check_updates
from ._root_dir import ROOT_DIR
from .config import get_attr
from .lifecycle import register_shutdown
from .logger import get_logger

__all__ = [
    # 全局路径
    "ROOT_DIR",
    # 基础设施
    "BaseClient",
    "check_updates",
    "get_attr",
    "get_logger",
    # 生命周期
    "register_shutdown",
]
