import time
import asyncio
from aiogram import Bot,Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession

from .utils import setup_logger,LoggingMiddleware,register_routers
from .utils.config_loader import proxy,token

dp=Dispatcher()

async def main():
    logger=setup_logger()
    dp.update.outer_middleware(LoggingMiddleware())

    @dp.message(Command("start"))
    async def command_start_handler(message:Message) -> None:
        await message.answer(
            "你好，我是基于aiogram开发的机器人Fool\n"
            "你可以输入\"/help\"获取功能列表，现在与我开始对话吧~"
        )

    @dp.message(Command('time'))
    async def now_time(message:Message):
        await message.answer(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
    
    register_routers(dp)
    session=AiohttpSession(proxy=proxy)
    bot=Bot(token=token,session=session)
    logger.info("🚀 机器人启动成功")
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())