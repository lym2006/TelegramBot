# src/plugins/AI/browser/__init__.py
"""
AI 浏览器门面

- AI 全局浏览器单例
"""

from ._manager import browser_manager

__all__ = ["browser_manager"]
