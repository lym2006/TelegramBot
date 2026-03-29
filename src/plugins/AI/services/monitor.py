import logging
from typing import cast
from aiogram import Bot
from aiogram.types import Message

from ..glo import user_session,TaskQueue,TaskItem
from ..services.message import MessageEditor
from .. services.worker import worker_loop

logger=logging.getLogger("Bot.Plugins.AI.Monitor")


async def monitor_loop(
    user:str,
    bot:Bot,
    editor:MessageEditor
):
    session=user_session[user]
    queue:TaskQueue=session['queue']
    while True:
        if queue.size>0:
            task=await queue.get_front_task()
            task=cast(TaskItem,task)
            await editor.safe_edit(
                chat_id=task.message.chat.id,
                msg_id=task.status_id,
                text="🧠 开始思考"
            )
            await worker_loop(task,user,bot,editor)
        else:
            session['is_active']=False
            session.pop('queue',None)
            logger.info(f"{user} 队列处理完成")
            break