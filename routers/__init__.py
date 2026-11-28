from fastapi import APIRouter
from .chat_routers import chat_router
from .kb_router import kb_router
from .history_router import history_router


api_v2 = APIRouter(prefix='/api')
api_v2.include_router(chat_router)
api_v2.include_router(kb_router)
api_v2.include_router(history_router)
