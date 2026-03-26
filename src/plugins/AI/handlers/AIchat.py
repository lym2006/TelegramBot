import json
import asyncio
import time
from aiogram import Router,Bot
from aiogram.types import Message
from aiogram.filters import Filter
from aiogram.enums import ChatType,ContentType

from ..glo import (
        rc,cupa,logger,user_session,session_guard,
        GROUP_TRIGGERS,
        get_name,makedata
    )
from ..services.html import mark,generate_html
from ..services.client import ChatClient
from ..services.black import get_black_list
from ..services.message import MessageEditor,MessageEditError,send_long_message

chat=Router()

class ChatFilter(Filter):
    async def __call__(self,message:Message)->bool:
        if message.content_type!=ContentType.TEXT:
            return False
        assert message.text
        if message.chat.type==ChatType.PRIVATE:
            is_command=message.text.startswith('/')
            return not is_command
        else:
            return any(keyword in message.text.lower() for keyword in GROUP_TRIGGERS)

@chat.message(ChatFilter())#AI对话
@session_guard
async def AIchat(message:Message,bot:Bot):
    user=get_name(message.chat.id)
    user_session[user]['md']=True
    city=message.text
    black_list=get_black_list()
    if user in black_list:
        return
    user_session[user]['current_think']=""
    user_session[user]['current_msg']=""
    user_session[user]['last_edit_time']=0
    chat_id=message.chat.id
    sent_msg=await message.answer("🤔 正在思考中")
    msg_id=sent_msg.message_id
    payload=makedata(city,user)
    editor=MessageEditor(bot)
    try:
        async with ChatClient() as client:
            async for data in client.stream_chat(payload):
                if "reasoning_content" in data and (content:=data["reasoning_content"]):
                    user_session[user]['current_think']+=content if not content.endswith('\n') else content[:-1]
                    current_think=user_session[user]['current_think']
                    current_time=asyncio.get_event_loop().time()
                    if current_time-user_session[user]['last_edit_time']>0.5:
                        try:
                            preview_think=current_think[-2000:] if len(current_think)>2000 else current_think
                            success=await editor.safe_edit(
                                    chat_id=chat_id,
                                    msg_id=msg_id,
                                    text=f"🤔 正在思考中\n{preview_think}"
                                )
                            if success:
                                user_session[user]['last_edit_time']=current_time
                        except MessageEditError as err:
                            if t:=err.wait_time>0:
                                tx=f"⚠️ 触发频控，等待 {t} 秒..."
                                message.answer(tx)
                                logger.warning(tx)
                if "content" in data and (content:=data["content"]):
                    user_session[user]['current_msg']+=content if not content.startswith('\n\n') else content[2:] 
    except Exception as e:
        if "错误码" in str(e):
            await message.answer("response错误")
            logger.error(str(e))
        else:
            await message.answer(f"流式请求错误")
            logger.error(f"❌ 流式请求异常: {e}")
    final_think=user_session[user]['current_think']
    if final_think:
        preview_think=final_think[-2000:] if len(final_think)>2000 else final_think
        final_display_text=f"✅ 思考完成\n{preview_think}"
        try:
            print(f"🚀 正在强制推送最终思考内容...")
            await bot.edit_message_text(final_display_text,chat_id=message.chat.id,message_id=msg_id)
        except Exception as e:
            await message.answer("推送错误")
            logger.error(f"最终推送失败: {e}")
    wrt=''
    msg=user_session[user]['current_msg']
    match message.chat.type:
        case ChatType.PRIVATE:
            wrt=f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n{city}\nAI:\n<think>\n{final_think}\n</think>\n{msg}\n'
        case ChatType.GROUP:
            grm=message.from_user
            assert grm,"用户不存在"
            wrt=f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n{grm.id}({grm.full_name}):{city}\nAI:\n<think>\n{final_think}\n</think>\n{msg}\n'
    open(cupa/f'{user}.txt','a',encoding='utf8').write(wrt)
    user_session[user]['message'].extend([rc("user",city),rc("assistant",msg)])
    print(msg)
    final_html=generate_html(msg)
    with open(cupa/f'{user}.html','w',encoding='utf-8') as a:
        a.write(final_html)
    mark(user,str(cupa/f'{user}.html'))
    if len(msg)>4000:
        await send_long_message(message,msg)
    else:
        await message.reply(msg)