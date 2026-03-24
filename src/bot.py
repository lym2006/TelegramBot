import asyncio
from aiogram import Bot,Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from .utils import setup_logger,register_routers,LoggingMiddleware

logger=setup_logger()

async def main():
    #初始化日志
    logger.info("🤖 TelegramBot 正在启动...")

    #导入配置
    from .utils import CONFIG

    #初始化 Bot
    session=AiohttpSession(proxy=CONFIG['network']['proxy'])
    bot=Bot(token=CONFIG['api_keys']['telegram_token'],session=session)

    #注册插件和中间件
    dp=Dispatcher()
    dp.update.outer_middleware(LoggingMiddleware())
    register_routers(dp,CONFIG)

    #⚪️神启动！
    logger.info("🚀 机器人启动成功")
    try:
        logger.info("🚀 开始轮询更新...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在关闭...")
    finally:
        await bot.session.close()
        logger.info("💤 机器人已关闭")

if __name__=="__main__":
    asyncio.run(main())