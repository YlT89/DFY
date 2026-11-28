from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    question: str = Field(...)
    image_urls: Optional[List[str]] = []  # ← 接收多图列表