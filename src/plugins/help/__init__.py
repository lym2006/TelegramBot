# src/plugins/help/__init__.py
"""
帮助指令插件

- /help 命令的路由处理
"""

from ._help import router

__all__ = ["router"]
