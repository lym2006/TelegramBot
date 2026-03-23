from typing import Dict,Callable,Any,Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message,TelegramObject,Update
from aiogram.enums import ChatType

from .logger_setup import setup_logger

class LoggingMiddleware(BaseMiddleware):#用于记录日志
    def __init__(self):
        self.logger=setup_logger()
    async def __call__(
        self,
        handler: Callable[[TelegramObject,Dict[str,Any]],Awaitable[Any]],
        event:TelegramObject,
        data:Dict[str, Any]
    ):
        log_msg=''
        if isinstance(event,Update):
            message=event.message if hasattr(event,'message') else None
            if isinstance(message,Message):
                content_type=message.content_type
                user_info=f"{message.chat.id} ({message.chat.full_name})"
                if message.chat.type==ChatType.GROUP:
                    group_info=user_info
                    user=message.from_user
                    assert user,'用户为空'
                    user_info=f"{user.id} ({user.full_name})"
                    log_msg+=f"群组 {group_info} | "
                log_msg+=(
                    f"用户 {user_info} 发送文本: {message.text}"
                    if content_type=="text"
                    else f"用户 {user_info} 发送 {content_type} 类型消息"
                )
        if log_msg:
            self.logger.info(log_msg)
        return await handler(event, data)