# src/plugins/AI/services/_render/__init__.py
"""
AI 视觉渲染组件（内部实现）

- HTML 渲染
- 页面截图与裁剪
"""

from ._renderer import render_html
from ._screenshot import screenshot

__all__ = [
    # HTML 渲染
    "render_html",
    # 页面截图与裁剪
    "screenshot",
]
