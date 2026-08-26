# src/bot.py
"""
TelegramBot 主程序入口

负责：
- 初始化运行环境
- 加载配置与版本检查
- 注册中间件与路由
- 启动带有自动重连机制的异步轮询
"""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential

from plugins.AI.services import cleanup_loop
from utils import check_updates
from utils.exception import ConfigError, ConfigInputError, ConfigMissingError
from utils.init_files import init_project_files
from utils.logger import get_logger
from utils.middlewares import LoggingMiddleware
from utils.plugins_register import register_routers

# 初始化日志（必须最先执行，确保后续配置加载时可用）
logger = get_logger("Bot")


# ==================== 1. 核心启动与重连逻辑 ====================
@retry(
    retry=retry_if_exception_type(TelegramNetworkError),
    stop=stop_after_delay(60),
    wait=wait_exponential(multiplier=1, max=10, min=1),
    before_sleep=lambda retry_state: logger.warning(
        f"🚨 机器人断开连接，准备第 {retry_state.attempt_number - 1} 次重连..."
    ),
    reraise=True,
)
async def _start_bot(dispatcher: Dispatcher, bot: Bot) -> None:
    """启动机器人并开始轮询，遇到网络异常时自动触发重连"""
    await dispatcher.start_polling(bot)


# ==================== 2. 主程序入口 ====================
async def main() -> None:
    """主程序入口，负责初始化环境、配置组件并启动机器人"""
    # 1. 基础环境初始化
    logger.info("🤖 TelegramBot 正在启动...")
    init_project_files()

    # 2. 加载配置并注入全局单例（必须在注册日志器之后导入）
    try:
        from utils.config import (
            ensure_config,
            get_attr,
            load_config,
            set_config,
        )

        # 检查配置文件，缺失则抛出 ConfigError
        ensure_config()

        # 读取并注入全局单例
        if not (config_data := load_config()):
            raise ConfigInputError("配置文件内容为空或已损坏")

        set_config(config_data)

        proxy = get_attr("global.proxy", str)
        if (token := get_attr("global.telegram_token", str)) is None:
            raise ConfigMissingError("❌ 配置文件中缺少必要的 Telegram Token")

    except ConfigError as e:
        logger.error(f"⚠️ 配置异常\n{e}")
        logger.info("🖥️ 正在打开 GUI 配置面板...")
        # TODO:GUI
        return

    # 3. 版本检查
    if not await check_updates():
        # TODO:提示
        pass

    # 4. 初始化核心组件
    from utils.ssl import SSLUnverifiedSession

    session = SSLUnverifiedSession(proxy=proxy)
    bot = Bot(token=token, session=session)

    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(LoggingMiddleware())
    register_routers(dispatcher)

    # 5. 启动后台清理任务
    cleanup_task = asyncio.create_task(cleanup_loop())

    # 6. 启动机器人并处理异常
    logger.info("🎉 机器人连接成功，开始轮询更新...")
    try:
        await _start_bot(dispatcher, bot)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("👋 收到中断信号，正在安全关闭机器人...")
    except Exception as e:
        logger.error(f"❌ 发生未预期的错误: {e}")
    finally:
        # 安全取消后台清理任务
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # 关闭网络会话
        await bot.session.close()
        logger.info("💤 机器人已关闭")


# ==================== 3. 脚本直接运行入口 ====================
if __name__ == "__main__":
    asyncio.run(main())
