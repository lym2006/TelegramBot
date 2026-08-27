# src/utils/__init__.py
"""
通用工具门面

提供：
- 基础网络客户端
- 全局根目录路径
- 版本检查工具
"""

from ._base_client import BaseClient
from ._check_version import check_updates
from ._root_dir import ROOT_DIR

__all__ = [
    # 网络与基础设施
    "BaseClient",
    # 全局路径
    "ROOT_DIR",
    # 版本检查
    "check_updates",
]
