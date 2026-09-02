# src/bot/_core.py
"""
Bot 启动引擎模块（内部实现）

- 注册中间件和路由
- 启动带有自动重连机制的异步轮询
- 安全关闭机器人
"""

import asyncio
import shutil
import threading

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential

from gui.mediator import gui_bridge
from utils import get_logger, register_shutdown
from utils.lifecycle import shutdown_all
from utils.middleware import LoggingMiddleware
from utils.plugins_register import register_routers
from utils.ssl import SSLUnverifiedSession

logger = get_logger()

# 内部常量
_RECONNECT_TIMEOUT = 60  # 最大重连超时时间
_MIN_RETRY_DELAY = 1  # 最小重连等待时间
_MAX_RETRY_DELAY = 10  # 最大重连等待时间
_TEMP_DIR = "data/ai_records/temp"  # AI 临时记录存放目录


class BotEngine:
    """Bot 核心引擎：封装启动、重连与优雅关闭逻辑"""

    def __init__(
        self,
        token: str,
        proxy: str,
        event_loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self.session = SSLUnverifiedSession(proxy=proxy)
        self.bot = Bot(token=token, session=self.session)
        self.dispatcher = Dispatcher()
        self._cleanup_task: asyncio.Task | None = None
        self._is_shutting_down = threading.Event()  # 防重入锁
        self._event_loop: asyncio.AbstractEventLoop | None = (
            event_loop  # 用于跨线程调度 shutdown
        )

        # 注册中间件和路由
        self.dispatcher.update.outer_middleware(LoggingMiddleware())
        register_routers(self.dispatcher)

        # 注册清理钩子
        register_shutdown(self._close_session, "关闭 Bot 网络会话")
        register_shutdown(
            lambda: shutil.rmtree(_TEMP_DIR, ignore_errors=True), "清理临时目录"
        )

        # 初始化时监听全局退出指令
        gui_bridge.request_shutdown.connect(self._on_request_shutdown)

    async def run(self) -> None:
        """对外暴露的启动入口"""
        logger.info("机器人连接成功，开始轮询更新...")

        # 注册清理任务和关闭钩子
        from plugins.AI.services import cleanup_loop

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        register_shutdown(self._cancel_cleanup, "结束后台清理任务")

        await self._start_polling()

    def stop(self) -> None:
        """对外暴露的停止入口"""
        logger.info("正在执行热重载...")
        try:
            _ = self.dispatcher.stop_polling()
            logger.info("Telegram 轮询已安全停止")
        except Exception as e:
            logger.send_error("停止轮询时发生异常", e)

    def _on_request_shutdown(self) -> None:
        """收到退出指令，启动清理流程"""
        if self._is_shutting_down.is_set():
            return
        self._is_shutting_down.set()

        logger.info("收到退出指令，开始执行全局资源清理...")

        # 跨线程安全调度：如果有 event_loop 则用 run_coroutine_threadsafe
        if self._event_loop:
            asyncio.run_coroutine_threadsafe(self._do_shutdown(), self._event_loop)
        else:
            asyncio.run(self._do_shutdown())

    async def _do_shutdown(self) -> None:
        """执行清理，并通知 GUI"""
        try:
            # 执行所有注册的钩子（逆序清理）"
            await shutdown_all()
        except Exception as e:
            logger.send_error("清理过程发生错误", e)
        finally:
            # 通知 GUI 退出
            gui_bridge.shutdown_completed_event.set()

    async def _cancel_cleanup(self) -> None:
        """取消后台清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _close_session(self) -> None:
        """关闭网络会话"""
        await self.bot.session.close()

    @retry(
        retry=retry_if_exception_type(TelegramNetworkError),
        stop=stop_after_delay(_RECONNECT_TIMEOUT),
        wait=wait_exponential(min=_MIN_RETRY_DELAY, max=_MAX_RETRY_DELAY),
        before_sleep=lambda retry_state: logger.warning(
            f"机器人断开连接，准备第 {retry_state.attempt_number} 次重连..."
        ),
        reraise=True,
    )
    async def _start_polling(self) -> None:
        """内部轮询方法"""
        await self.dispatcher.start_polling(self.bot)
