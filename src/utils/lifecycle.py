# src/utils/lifecycle.py
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
