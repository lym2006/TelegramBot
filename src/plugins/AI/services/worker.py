import asyncio
import time
import logging
from aiogram import Bot
from aiogram.enums import ChatType,ParseMode
from aiogram.exceptions import TelegramRetryAfter

from ..glo import rc,cupa,user_session,TaskItem,makedata
from ..services.message import MessageEditor,send_long_message,MessageEditError#,handle_ai_message
from ..services.html import mark,generate_html
from ..services.client import ChatClient

logger=logging.getLogger("Bot.Plugins.AI.Worker")

async def worker_loop(
    task:TaskItem,
    user:str,
    bot:Bot,
    editor:MessageEditor
):
    message=task.message
    chat_id=message.chat.id
    status_id=task.status_id
    city=message.text
    draft_id=int(time.time_ns()%2**63)
    user_session[user]['current_think']=""
    user_session[user]['current_msg']=""
    user_session[user]['last_draft_time']=0
    payload=makedata(city,user)
    #editor=MessageEditor(bot)
    try:
        async with ChatClient() as client:
            async for data in client.stream_chat(payload):
                if "reasoning_content" in data and (content:=data["reasoning_content"]):
                    user_session[user]['current_think']+=content if not content.endswith('\n') else content[:-1]
                    current_think=user_session[user]['current_think']
                    current_time=asyncio.get_event_loop().time()
                    if current_time-user_session[user]['last_draft_time']>1.2:
                        try:
                            preview_think=current_think[-2000:] if len(current_think)>2000 else current_think
                            success=await bot.send_message_draft(
                                    chat_id=chat_id,
                                    draft_id=draft_id,
                                    text=f"🤔 正在思考中\n{preview_think}",
                                    
                                )
                            if success:
                                user_session[user]['last_draft_time']=current_time
                        except TelegramRetryAfter as err:
                            if (t:=err.retry_after)>0:
                                tx=f"⚠️ 触发频控，等待 {t} 秒..."
                                logger.warning(tx)
                                await asyncio.sleep(t)
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
            await bot.send_message_draft(
                chat_id=chat_id,
                draft_id=draft_id,
                text=final_display_text
            )
            await asyncio.sleep(1)
            await bot.send_message_draft(
                chat_id=chat_id,
                draft_id=draft_id,
                text="清除草稿"
            )
            await editor.safe_edit(
                chat_id=chat_id,
                msg_id=status_id,
                text=final_display_text
            )
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
    html_body,final_html=generate_html(msg)
    with open(cupa/f'{user}.html','w',encoding='utf-8') as a:
        a.write(final_html)
    mark(user,str(cupa/f'{user}.html'))
    if len(msg)>4000:
        try:
            await send_long_message(message,html_body,ParseMode.HTML)
        except:
            await send_long_message(message,html_body,None)
    else:
        try:
            await message.reply(html_body,parse_mode=ParseMode.HTML)
        except:
            await message.reply(msg)