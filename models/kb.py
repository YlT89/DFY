from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone



class KB(SQLModel, table=True):
    # 1. 标准主键（自增ID）
    id: Optional[int] = Field(default=None, primary_key=True)

    # 2. 库的名称（普通字段）
    name: str = Field(index=True, description="知识库名称")


    create_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
