# ==========================
# 全局变量与配置
# ==========================

import asyncio
from collections import deque
from typing import Dict,Deque
from pathlib import Path
from aiogram.types import Message
from typing import Optional

# --- 基础配置 ---
cupa=Path.cwd()/'src/plugins/AI/record'

# --- 核心数据结构 ---

class TaskItem:
    def __init__(self,message:Message):
        self.message=message
        self.status_id:int=0

class TaskQueue:
    def __init__(self):
        self._queue:Deque[TaskItem]=deque()
        self._lock=asyncio.Lock()
    async def add_task(self,task:TaskItem):
        async with self._lock:
            self._queue.append(task)
    async def get_front_task(self)->Optional[TaskItem]:
        async with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None
    @property
    def size(self):
        return len(self._queue)

# --- 全局状态容器 ---
user_session:Dict[str,Dict]={}
active_tasks=set()

# ==========================
# 工具函数
# ==========================

rc=lambda role,content:{"role":role,"content":content}

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
        'md':False,
        'is_active':False,
        'queue':TaskQueue(),
        'monitor_event':asyncio.Event(),
        'worker_running':False
    }
)