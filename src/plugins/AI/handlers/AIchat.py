import logging
import asyncio
from aiogram import Router,Bot
from aiogram.types import Message
from aiogram.filters import Filter
from aiogram.enums import ChatType,ContentType

from ..glo import (
        session_guard,user_session,active_tasks,
        GROUP_TRIGGERS,get_name,TaskItem
    )
from ..services.monitor import monitor_loop
from ..services.black import get_black_list
from ..services.message import MessageEditor

chat=Router()
logger=logging.getLogger("Bot.Plugins.AI")

class ChatFilter(Filter):
    async def __call__(self,message:Message)->bool:
        if message.content_type!=ContentType.TEXT:
            return False
        assert message.text
        if message.chat.type==ChatType.PRIVATE:
            is_command=message.text.startswith('/')
            return not is_command
        #elif message.chat.type in [ChatType.GROUP,ChatType.SUPERGROUP]:
            #return any(keyword in message.text.lower() for keyword in GROUP_TRIGGERS)
        else:
            return False

@chat.message(ChatFilter())#AI对话
@session_guard
async def AIchat(message:Message,bot:Bot):
    user=get_name(message)
    editor=MessageEditor(bot)
    black_list=get_black_list()
    if user in black_list:
        return
    session=user_session[user]
    queue=session['queue']
    session['md']=True
    task=TaskItem(message)
    if queue.size==0 and not session['is_active']:
        sent=await message.reply("🤔 正在思考中")
    else:
        sent=await message.reply("⏳ 请等待排队")
    task.status_id=sent.message_id
    await queue.add_task(task)
    print(f"用户 {user} 新任务入队，当前长度: {queue.size}")
    if not session['is_active']:
        session['is_active']=True
        monitor_task=asyncio.create_task(monitor_loop(user,bot,editor))
        active_tasks.add(monitor_task)
        monitor_task.add_done_callback(active_tasks.discard)