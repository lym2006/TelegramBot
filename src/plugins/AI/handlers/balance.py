import logging
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.client import WalletClient

balance=Router()
logger=logging.getLogger("Bot.Plugins.AI.Balance")

@balance.message(Command('balance'))#查询余额
async def check_balance(message:Message):
    try:
        async with WalletClient() as client:
            resp=await client.get("/subject/profile/peek")
        available=resp.json()['data']['financialInfo']['available']
        used=resp.json()['data']['financialInfo']['used']
        available=float(available)/1e12
        used=float(used)/1e12
        report_lines=[
            "💰账户余额",
            f"有效额度：{available:.4f}",
            f"已用额度：{used:.4f}",
            f"更新时间：{datetime.now().strftime('%m-%d %H:%M')}"
        ]
        await message.answer("\n".join(report_lines))
    except Exception as e:
        logger.error(f"查询失败\n{str(e)}")
        await message.answer(f"查询失败")