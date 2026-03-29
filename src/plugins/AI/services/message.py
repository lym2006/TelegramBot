import re
import logging
import asyncio
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from ..glo import user_session,makedata
from ..services.client import ChatClient

logger=logging.getLogger("Bot.Plugins.AI.Message")

class MessageEditError(Exception):
    def __init__(self,msg:str,wait_time:int=0):
        super().__init__(msg)
        self.wait_time=wait_time

class MessageEditor:
    def __init__(self,bot:Bot):
        self.bot=bot
        self.last_edit_time=0
    async def safe_edit(self,chat_id:int,msg_id:int,text:str):
        current_time=asyncio.get_event_loop().time()
        if current_time-self.last_edit_time<2.5:
            return False
        try:
            await self.bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=msg_id
                )
            self.last_edit_time=current_time
            return True
        except TelegramBadRequest as e:
            error_str=str(e).lower()
            if "message is not modified" in error_str:
                return False
            elif any(w in error_str for w in ["flood control exceeded","too many requests"]):
                match=re.search(r"retry after (\d+)",str(e))
                wait_time=int(match.group(1))+1 if match else 5
                raise MessageEditError("tg频控",wait_time)
            else:
                raise MessageEditError(str(e))
            
async def send_long_message(message:Message,text):
    total_len=len(text)
    for i in range(0,total_len,4000):
        chunk=text[i:i+4000]
        try:
            await message.reply(chunk)
        except Exception as e:
            logger.error(f"发送失败: {e}")
        if total_len>4000*5:
            await asyncio.sleep(1)

'''async def handle_ai_message(city:str,user:str):
    session=user_session[user]
    session.update({
        'md':True,
        'current_think':"",
        'current_msg':"",
    })
    payload=makedata(city,user)
    try:
        async with ChatClient() as client:
            async for data in client.stream_chat(payload):

                logger.debug(f"🔍 流式返回的原始数据: {data}") 

                if "reasoning_content" in data and (content:=data["reasoning_content"]):
                    if content.endswith('\n'):
                        content=content[:-1]
                    session['current_think']+=content
                    yield "think",session['current_think']
                if "content" in data and (content:=data["content"]):
                    if content.startswith('\n\n'):
                        content=content[2:]
                    session['current_msg']+=content
                    yield "chunk",content
            final_msg=session['current_msg']
            final_think=session['current_think']
            yield "final",(final_msg,final_think)
    except Exception as e:
        logger.error(f"❌ 流式请求异常: {e}",exc_info=True)
        yield "error",str(e)'''