

from .chat import ChatMessage
from .kb import KB

# 统一在这里重建，确保所有类都已加载完毕

ChatMessage.model_rebuild()
KB.model_rebuild()