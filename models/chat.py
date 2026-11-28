from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone


class ChatMessage(SQLModel, table=True):
    __tablename__ = 'chat_message'

    id: Optional[int] = Field(default=None, primary_key=True)

    role_type: str   # 改成role_type 或者 msg_role（聊天接口的除了发给大模型的其它都改），然后删库（dev.db）重建，因为容易和SQL起冲突
    content: str

    create_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    image_url: Optional[str] = Field(default=None)      # 存完整 data URI
