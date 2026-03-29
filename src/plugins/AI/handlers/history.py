from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message,FSInputFile

from ..glo import ini,cupa,user_session,session_guard,get_name

history=Router()

@history.message(Command('history'))#对话历史
@session_guard
async def show_history(message:Message):
    user=get_name(message)
    messageList=user_session[user]['message'][-30:]#只显示最近的30条，有需求查本地记录
    print(messageList)
    await message.answer(str([{v['role']: v['content']} for v in messageList]))

@history.message(Command('clear'))#清空历史
@session_guard
async def clear_history(message:Message):
    user=get_name(message)
    user_session[user]['message']=ini.copy()
    await message.answer("记忆清除成功")

@history.message(Command('md'))#发送markdown
@session_guard
async def send_markdown(message:Message):
    user=get_name(message)
    if user_session[user]['md']:
        await message.answer_photo(FSInputFile(cupa/f'{user}.png'))
    else:
        await message.answer("没有对话")