from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class GlobalSettings(BaseSettings):
    app: str = 'dev'
    db_url: str = 'sqlite:///./dev.db'
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    secret_key: str     # 把这个写进环境变量，从环境变量中读
    token_expire_min: int = 30
    api_key: str = Field(..., min_length=3)     # deepseek
    dashscope_api_key: str = Field(..., min_length=3)   # embedding
    gaode_api_key: str = Field(..., min_length=3)   # 高德
    vision_model: str = "deepseek-v4-flash-vision-exp"  # 视觉模型
    tavily_api_key: str = Field(..., min_length=3)      # tavily

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8',extra='ignore')

# 全局实例，所有的环境变量都从这里走，其它地方就不用到处导入了
settings = GlobalSettings()