from db.session import get_db
from models import ChatMessage
from sqlmodel import select

db = next(get_db())
records = db.exec(
    select(ChatMessage).order_by(ChatMessage.create_time.desc()).limit(3)
).all()

for r in records:
    print(f"[{r.role_type}] 长度={len(r.content)}")
    print(r.content)
    print("---")