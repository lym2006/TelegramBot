# src/bot/_runner.py
"""
Bot 运行模块（内部实现）？？？和main的名字有点冲突

负责：
？？？
"""

import asyncio
import threading
from collections.abc import Callable

from utils.logger import get_logger


class BotRunner:
    """负责在后台线程中安全地启动和管理 Bot 引擎"""

    def __init__(self, init_event: threading.Event, get_config_func: Callable) -> None:
        self._logger = get_logger("Bot")
        self._init_event = init_event
        self._get_config = get_config_func  # 传入一个获取配置的回调

    def start(self) -> None:
        """启动后台 Bot 线程"""
        thread = threading.Thread(target=self._run_bot, daemon=True)
        thread.start()

    def _run_bot(self) -> None:
        """后台线程执行逻辑"""
        self._logger.info("⏳ Bot 线程已启动，等待环境初始化完成...")

        # 挂起等待初始化完成
        self._init_event.wait()

        # 获取最新配置
        proxy, token = self._get_config()

        from bot import BotEngine

        self._logger.info("🤖 TelegramBot 正在后台启动...")
        asyncio.run(BotEngine(token=token, proxy=proxy).run())
