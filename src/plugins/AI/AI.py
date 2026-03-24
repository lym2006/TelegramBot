import time
import json
import logging
import asyncio
from datetime import datetime

from aiogram import Bot,Router
from aiogram.types import Message,FSInputFile,User
from aiogram.filters import Command,StateFilter,Filter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode,ChatType,ContentType
from aiogram.exceptions import TelegramBadRequest

from .func import rc,ini,client,cupa
from .func import mark,generate_html,send_long_message,ensure_user_session,get_black_list,save_black_list

'''file = open(cupa/'personality.txt','r',encoding = 'utf-8')
per = file.read()
file.close()'''     #人设
user_session={}     #用户状态
router=Router()
logger=logging.getLogger("Bot.Plugins.AI")
session_guard=ensure_user_session(
    user_session,
    {
        'message':ini.copy(),
        'md':False
    }
)

#############################################################################################################################################################

@router.message(Command('off'))#关闭对话
async def turn_off(message:Message):
    user=str(message.chat.id)
    black_list=get_black_list()
    if user not in black_list:
        black_list.append(user)
        save_black_list(black_list)
        await message.answer(f"成功将用户{user}写入黑名单")
    else:
        await message.answer(f"用户{user}已存在黑名单内")

@router.message(Command('on'))#开启对话
async def turn_on(message:Message):
    user=str(message.chat.id)
    black_list=get_black_list()
    if user in black_list:
        black_list.remove(user)
        save_black_list(black_list)
        await message.answer(f"成功将用户{user}移除黑名单")
    else:
        await message.answer(f"用户{user}不存在黑名单内")

#############################################################################################################################################################

@router.message(Command('md'))#发送markdown
@session_guard
async def send_markdown(message:Message):
    user=str(message.chat.id)
    if user_session[user]['md']:
        await message.answer_photo(FSInputFile(cupa/f'{user}.png'))
    else:
        await message.answer("没有对话")

#############################################################################################################################################################

@router.message(Command('history'))#对话历史
@session_guard
async def show_history(message:Message):
    user=str(message.chat.id)
    messageList=user_session[user]['message'][-30:]#只显示最近的30条，有需求查本地记录
    print(messageList)
    await message.answer(str([{v['role']: v['content']} for v in messageList]))
 
@router.message(Command('clear'))#清空历史
@session_guard
async def clear_history(message:Message):
    user=str(message.chat.id)
    if user_session[user]['message']==ini:
        await message.answer("没有对话")
    else:
        user_session[user]['message']=ini.copy()
        await message.answer("记忆清除成功")

#############################################################################################################################################################

@router.message(Command('balance'))#查询余额
async def check_balance(message:Message):
    try:
        resp=await client.get("/user/info")
        report_lines=[
            "💰账户余额",
            f"总额：{resp.json()['data']['totalBalance']}",
            f"充值余额：{resp.json()['data']['chargeBalance']}",
            f"状态：{resp.json()['data']['status']}",
            f"更新时间：{datetime.now().strftime('%m-%d %H:%M')}"
        ]
        await message.answer("\n".join(report_lines))
    except Exception as e:
        logger.error(f"查询失败\n{str(e)}")
        await message.answer(f"查询失败")

#############################################################################################################################################################

class Chg(StatesGroup):
    name=State()
    identity=State()

def makemention(user:User):
    user_name=user.username or user.full_name
    mention_link=f"[{user_name}](tg://user?id={user.id})"
    return mention_link

@router.message(Command('change'))
async def input_name(message:Message,state:FSMContext):
    await message.answer("请输入新身份的名字")
    await state.set_state(Chg.name)

@router.message(StateFilter(Chg.name))
async def input_identity(message:Message,state:FSMContext):
    await state.update_data(name=message.text)
    await message.answer("请输入新身份的描述")
    await state.set_state(Chg.identity)

@router.message(StateFilter(Chg.identity))
@session_guard
async def changesetting(message:Message,state:FSMContext):
    tmp=await state.get_data()
    name=tmp['name']
    identity=message.text
    user=str(message.chat.id)
    user_session[user]['message'].append(rc("system",f"更改你的身份，你现在是{identity}，名字叫{name}"))
    assert message.from_user,'用户为空'
    await message.answer(f"{makemention(message.from_user)}，你的机器人「{name}」已准备好，可以开始对话。",parse_mode=ParseMode.MARKDOWN_V2)
    await state.clear()

#############################################################################################################################################################

class Sys(StatesGroup):
    input=State()

@router.message(Command('system'))
async def pre_system(message:Message,state:FSMContext):
    await message.answer("你想以system身份输入什么内容")
    await state.set_state(Sys.input)

@router.message(StateFilter(Sys.input))
@session_guard
async def post_to_system(message:Message,state:FSMContext):
    if not message.text:
        await message.answer("请重新输入文本")
        return
    user=str(message.chat.id)
    msg=message.text
    user_session[user]['message'].append(rc('system',msg))
    await message.answer("成功输入")
    await state.clear()

#############################################################################################################################################################

def makedata(thisinput,user):#构造数据
    return user_session[user]['message']+[rc('user',thisinput)]

class ChatFilter(Filter):
    async def __call__(self,message:Message)->bool:
        if message.content_type!=ContentType.TEXT:
            return False
        assert message.text
        if message.chat.type==ChatType.PRIVATE:
            is_command=message.text.startswith('/')
            return not is_command
        is_mention='@fool' in message.text.lower()
        return is_mention

@router.message(ChatFilter())#AI对话
@session_guard
async def AIchat(message:Message,bot:Bot):
    user=str(message.chat.id)
    user_session[user]['md']=True
    city=message.text
    black_list=get_black_list()
    if user in black_list:
        return
    user_session[user]['current_think']=""
    chat_id=message.chat.id
    sent_msg=await message.answer("🤔 正在思考中")
    msg_id=sent_msg.message_id
    payload={
        "model":"Pro/deepseek-ai/DeepSeek-R1",
        "messages":makedata(thisinput=city,user=user),
        "stream":True,
        "temperature":0.7,
    }
    try:
        async with client.stream("POST","/chat/completions",json=payload) as response:
            if (code:=response.status_code)!=200:
                await message.answer('错误码'+str(code))
                return
            user_session[user]['current_msg']=""
            user_session[user]['last_edit_time']=0
            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    try:
                        data=json.loads(chunk[6:])
                        data=data["choices"][0]["delta"]
                        if content:=data.get("content"):
                            user_session[user]['current_msg']+=content if not content.startswith('\n\n') else content[2:]
                        elif content:=data.get("reasoning_content"):
                            user_session[user]['current_think']+=content if not content.endswith('\n') else content[:-1]
                            current_think=user_session[user]['current_think']
                            current_time=time.time()
                            if current_time-user_session[user]['last_edit_time']>0.8:
                                preview_think=current_think[-2000:] if len(current_think)>2000 else current_think
                                edit_text=f"🤔 正在思考中\n{preview_think}"
                                try:
                                    await bot.edit_message_text(edit_text,chat_id=chat_id,message_id=msg_id)
                                    user_session[user]['last_edit_time']=current_time
                                except TelegramBadRequest as e:
                                    if "message is not modified" in str(e):
                                        pass
                                    elif "rate limit" in str(e):
                                        await asyncio.sleep(1)
                                    else:
                                        logger.error(f"编辑消息失败: {e}")
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"解析数据块出错: {e}\nchunk: {chunk}")
                        continue
    except Exception as e:
        logger.error(f"❌ 流式请求异常: {e}")
        await message.answer(f"❌ 流式请求异常")
    final_think=user_session[user]['current_think']
    if final_think:
        preview_think=final_think[-2000:] if len(final_think)>2000 else final_think
        final_display_text=f"✅ 思考完成\n{preview_think}"
        try:
            print(f"🚀 正在强制推送最终思考内容...")
            await bot.edit_message_text(final_display_text,chat_id=message.chat.id,message_id=msg_id)
        except Exception as e:
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
    final_html=generate_html(msg,user)
    with open(cupa/f'{user}.html','w',encoding='utf-8') as a:
        a.write(final_html)
    mark(user,str(cupa/f'{user}.html'))
    if len(msg)>4000:
        await send_long_message(message,msg)
    else:
        await message.reply(msg)