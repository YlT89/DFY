from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from db.session import get_db

from models.chat import ChatMessage

history_router = APIRouter(prefix="/history", tags=["历史对话"])

@history_router.get('/historical')
def get_chat_history(db: Session = Depends(get_db)):
    # 按时间正序拿最近 20 条，防止上下文爆炸
    # 注意：按时间降序查20条，然后反转一下，保证顺序是从旧到新
    messages = db.query(ChatMessage).order_by(ChatMessage.id.desc()).limit(21).all()
    messages.reverse()

    return [{'role': msg.role_type, 'content': msg.content, 'image_url': msg.image_url} for msg in messages]