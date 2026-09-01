# src/utils/lifecycle.py
"""
程序生命周期管理工具

- 进程级平滑重启
- 统一管理所有底层资源的初始化与优雅关闭
"""

import inspect
import os
import sys
from typing import Any

from .logger import get_logger

logger = get_logger("Lifecycle")

# ==================== 1. 自动重启 ====================


def restart_bot() -> None:
    """
    平滑重启 Bot

    使用当前 Python 解释器重新执行当前的启动脚本，完美兼容各种运行环境
    """
    logger.info("🔄 正在应用新配置并重启 Bot...")
    try:
        python = sys.executable
        script = sys.argv[0]
        # 替换当前进程，实现无缝重启
        os.execv(python, [python, script] + sys.argv[1:])
    except Exception as e:
        logger.send_error("❌ 自动重启失败，请手动重启程序", e)


# ==================== 2. 注册和清理资源 ====================

_shutdown_hooks: list[tuple[Any, str]] = []


def register_shutdown(hook: Any, desc: str) -> None:
    """
    注册一个关闭钩子

    任何模块都可以把自己的清理函数塞到这里
    """
    if desc:
        logger.info(f"📌 注册关闭钩子: {desc}")
    _shutdown_hooks.append((hook, desc))


async def shutdown_all() -> None:
    """逆序执行所有的钩子（后注册的先关闭，保证依赖关系）"""
    logger.info("🛑 正在执行全局生命周期清理...")
    # 逆序遍历
    for hook, desc in reversed(_shutdown_hooks):
        try:
            logger.info(f"⏳ 正在执行: {desc}")
            if inspect.iscoroutinefunction(hook):
                await hook()
            else:
                hook()
            logger.info(f"✅ 已完成：{desc}")
        except Exception as e:
            logger.send_error("⚠️ 关闭钩子执行异常", e)
    logger.info("✅ 全局生命周期清理完毕")
