# ==========================
# 全局变量与配置
# ==========================

import asyncio
import logging
from typing import Dict
from pathlib import Path
from aiogram.types import Message

logger=logging.getLogger("Bot.Plugins.AI")
cupa=Path.cwd()/'src/plugins/AI/record'
user_session:Dict[str,Dict]={}

# ==========================
# 工具函数
# ==========================

def makedata(thisinput,user):#构造数据
    return user_session[user]['message']+[rc('user',thisinput)]

def get_name(msg:Message):
    id=msg.chat.id
    return f"g_{abs(id)}_{getattr(getattr(msg,'from_user',None),'id','unknown')}" if id<0 else f"u_{id}"

# ==========================
# 装饰器与中间件
# ==========================

import copy
import functools
from .config import ini,GROUP_TRIGGERS

rc=lambda role,content:{"role":role,"content":content}

def ensure_user_session(session:dict,default:dict):
    def ensure_user_session(func):
        @functools.wraps(func)
        async def wrapper(message:Message,*args,**kwargs):
            user=user=get_name(message)
            if user not in session:
                session[user]=copy.deepcopy(default)
                print(f"🆕 [Decorator] 已为 {user} 初始化会话")
            return await func(message,*args,**kwargs)
        return wrapper
    return ensure_user_session

# 实例化装饰器
session_guard=ensure_user_session(
    user_session,
    {
        'message':ini.copy(),
        'md':False
    }
)