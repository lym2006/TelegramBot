import copy
import logging
import functools
from typing import Dict
from pathlib import Path
from aiogram.types import Message

from .config import ini,GROUP_TRIGGERS

logger=logging.getLogger("Bot.Plugins.AI")
rc=lambda role,content:{"role":role,"content":content}
cupa=Path.cwd()/'src/plugins/AI/record'
user_session:Dict[str,Dict]={}

def makedata(thisinput,user):#构造数据
    return user_session[user]['message']+[rc('user',thisinput)]

def get_name(chat_id:int):
    return f"g_{abs(chat_id)}" if chat_id<0 else f"u_{chat_id}"

def ensure_user_session(session:dict,default:dict):
    def ensure_user_session(func):
        @functools.wraps(func)
        async def wrapper(message:Message,*args,**kwargs):
            user=user=get_name(message.chat.id)
            if user not in session:
                session[user]=copy.deepcopy(default)
                print(f"🆕 [Decorator] 已为 {user} 初始化会话")
            return await func(message,*args,**kwargs)
        return wrapper
    return ensure_user_session

session_guard=ensure_user_session(
    user_session,
    {
        'message':ini.copy(),
        'md':False
    }
)