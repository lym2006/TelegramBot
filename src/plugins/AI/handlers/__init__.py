# src/plugins/AI/handlers/__init__.py
"""
AI 路由注册中心

- 用于聚合所有子模块路由的工厂函数
"""

from aiogram import Router

from . import _ai_chat, _auth, _history

# , _identity

__all__ = ["get_router"]


def get_router() -> Router:
    """组装并返回包含所有 AI 业务路由的总路由"""
    router = Router()

    # 注册所有子路由（顺序即优先级）
    # 确保 ai_chat 是最后一个注册
    routers = [
        _auth.auth,
        _history.history,
        # _identity.identity,
        _ai_chat.ai_chat,
    ]
    for r in routers:
        router.include_router(r)

    return router
