# src/bot/_core.py
"""
Bot 核心引擎模块（内部实现）

负责：
- 注册中间件和路由
- 启动带有自动重连机制的异步轮询
- 安全关闭机器人
"""

import asyncio
import shutil

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential

from plugins.AI.services import cleanup_loop
from utils.logger import get_logger
from utils.middlewares import LoggingMiddleware
from utils.plugins_register import register_routers
from utils.ssl import SSLUnverifiedSession

logger = get_logger("Bot")


class BotEngine:
    """Bot 核心引擎：封装启动、重连与优雅关闭逻辑"""

    # 1. 配置常量
    RECONNECT_TIMEOUT = 60
    MIN_RETRY_DELAY = 1
    MAX_RETRY_DELAY = 10
    TEMP_DIR = "data/ai_records/temp"

    def __init__(self, token: str, proxy: str) -> None:
        self.session = SSLUnverifiedSession(proxy=proxy)
        self.bot = Bot(token=token, session=self.session)
        self.dispatcher = Dispatcher()
        self._cleanup_task: asyncio.Task | None = None

        # 注册中间件和路由
        self.dispatcher.update.outer_middleware(LoggingMiddleware())
        register_routers(self.dispatcher)

    async def run(self) -> None:
        """对外暴露的启动入口"""
        logger.info("🎉 机器人连接成功，开始轮询更新...")
        self._cleanup_task = asyncio.create_task(cleanup_loop())

        try:
            await self._start_polling()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("👋 收到中断信号，正在安全关闭机器人...")
        except Exception as e:
            logger.error(f"❌ 发生未预期的错误: {e}")
        finally:
            await self._shutdown()

    async def _shutdown(self) -> None:
        """优雅关闭：清理任务 + 关闭网络会话"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        shutil.rmtree(self.TEMP_DIR, ignore_errors=True)

        await self.bot.session.close()
        logger.info("💤 机器人已关闭")

    @retry(
        retry=retry_if_exception_type(TelegramNetworkError),
        stop=stop_after_delay(RECONNECT_TIMEOUT),
        wait=wait_exponential(min=MIN_RETRY_DELAY, max=MAX_RETRY_DELAY),
        before_sleep=lambda retry_state: logger.warning(
            f"🚨 机器人断开连接，准备第 {retry_state.attempt_number - 1} 次重连..."
        ),
        reraise=True,
    )
    async def _start_polling(self) -> None:
        """内部轮询方法"""
        await self.dispatcher.start_polling(self.bot)
