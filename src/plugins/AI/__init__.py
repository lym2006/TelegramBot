from aiogram import Router

from .handlers import auth,balance,history,identity,AIchat

routers=[
    auth.auth,
    #balance.balance,
    history.history,
    identity.identity,
    AIchat.chat
]

router=Router()

for r in routers:
    router.include_router(r)

__all__=["router"]