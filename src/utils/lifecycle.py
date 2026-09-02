# src/utils/lifecycle.py
"""
程序生命周期管理工具

- 进程级平滑重启
- 统一管理所有底层资源的初始化与优雅关闭
"""

import inspect
from collections.abc import Callable
from typing import Any

from gui.mediator import gui_bridge

from .logger import get_logger

logger = get_logger("Lifecycle")

# ==================== 1. 自动热重启 ====================


def restart_bot(reload_callback: Callable[[], None]) -> None:
    """热重载新配置"""
    logger.info("正在应用新配置...")

    try:
        from .config import save_config, set_config

        # 1. 从中介者那里拿到最新的配置
        new_config = gui_bridge.config

        # 2. 刷新全局配置并持久化到文件
        set_config(new_config)
        save_config(new_config)

        # 3. 回调重载函数
        reload_callback()
        logger.info("热重载成功，引擎已刷新")

    except Exception as e:
        logger.send_error("热重载失败，请检查配置", e)


# ==================== 2. 注册和清理资源 ====================

_shutdown_hooks: list[tuple[Any, str]] = []


def register_shutdown(hook: Any, desc: str) -> None:
    """
    注册一个关闭钩子

    任何模块都可以把自己的清理函数塞到这里
    """
    if desc:
        logger.info(f"注册关闭钩子: {desc}")
    _shutdown_hooks.append((hook, desc))


async def shutdown_all() -> None:
    """逆序执行所有的钩子（后注册的先关闭，保证依赖关系）"""
    logger.info("正在执行全局生命周期清理...")
    # 逆序遍历
    for hook, desc in reversed(_shutdown_hooks):
        try:
            logger.info(f"正在执行: {desc}")
            if inspect.iscoroutinefunction(hook):
                await hook()
            else:
                hook()
            logger.info(f"已完成：{desc}")
        except Exception as e:
            logger.send_error("关闭钩子执行异常", e)
    logger.info("全局生命周期清理完毕")
