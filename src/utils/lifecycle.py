# src/utils/lifecycle.py
"""
程序生命周期管理工具

负责：
- 进程级环境控制
- 进程级平滑重启
"""

import ctypes
import os
import sys

from .logger import get_logger

logger = get_logger("Bot.Lifecycle")


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
        logger.error(f"❌ 自动重启失败，请手动重启程序: {e}")


# ==================== 2. 隐藏控制台 ====================
def hide_console() -> None:
    """
    隐藏 Windows 平台原生控制台

    在程序启动初期调用，实现纯 GUI 启动体验
    """
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass  # 忽略隐藏失败
