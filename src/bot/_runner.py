# src/bot/_runner.py
"""
Bot 后台运行模块（内部实现）

- 在独立的后台线程中安全地启动和管理 Bot 引擎
- 通过 Event 机制与主程序同步，等待环境初始化完成后再启动
"""

import asyncio
import threading
from collections.abc import Callable

from utils import get_logger

from ._core import BotEngine


class BotRunner:
    """负责在后台线程中安全地启动和管理 Bot 引擎"""

    def __init__(self, init_event: threading.Event, get_config_func: Callable) -> None:
        self._logger = get_logger()
        self._init_event = init_event
        self._get_config = get_config_func  # 传入一个获取配置的回调
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._engine: BotEngine | None = None

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

        self._logger.info("🤖 TelegramBot 正在后台启动...")

        # 手动创建 event_loop 并传给 BotEngine，用于跨线程 shutdown
        self._event_loop = asyncio.new_event_loop()
        try:
            self._engine = BotEngine(
                token=token, proxy=proxy, event_loop=self._event_loop
            )
            self._event_loop.run_until_complete(self._engine.run())
        finally:
            if self._event_loop and not self._event_loop.is_closed():
                # 取消所有剩余任务
                pending = [t for t in asyncio.all_tasks(self._event_loop)]
                for task in pending:
                    task.cancel()
                self._event_loop.close()

                self._logger.info("💤 所有任务已取消")
