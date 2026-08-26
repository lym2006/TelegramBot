# src/utils/_root_dir.py
"""
项目根目录解析工具（内部实现）

提供：
- 通过特征文件向上遍历定位项目根目录
- 全局缓存的 ROOT_DIR 常量
"""

from pathlib import Path

from .logger import get_logger

logger = get_logger("Bot.RootDir")

# 定义项目根目录的特征文件（按优先级排序）
_ROOT_MARKERS = (".git", "pyproject.toml")


def _get_project_root() -> Path:
    """
    获取项目根目录

    从当前文件所在目录开始，逐级向上查找包含特征文件的目录
    """
    # 确保从源码目录开始，避免 __pycache__ 干扰
    current = Path(__file__).resolve().parent

    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in _ROOT_MARKERS):
            return parent

    # 兜底策略：如果找不到特征文件，默认返回当前文件向上三级 (utils -> src -> root)
    fallback = current.parent.parent.parent
    logger.warning(
        f"⚠️ 未找到项目特征文件 {_ROOT_MARKERS}，已降级使用兜底路径: {fallback}"
    )
    return fallback


# 模块加载时立即解析并缓存根目录
ROOT_DIR = _get_project_root()
