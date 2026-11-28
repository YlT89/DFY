from core.exceptions import register_exception_handlers
from routers import api_v2
from core.middlewares import register_middlewares
import time
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from db.session import engine
from fastapi import Response
from fastapi_offline import FastAPIOffline   # 下载本地Swagger页面
from models import ChatMessage, KB



@asynccontextmanager
async def lifespan(app: FastAPIOffline):

    SQLModel.metadata.create_all(engine)
    print("✅ 数据库表已就绪")
    yield
    print("服务关闭")


# 2. 把 lifespan 传给 FastAPI
app = FastAPIOffline(
    title="FastAPI + SQLModel综合项目",
    version="1.0",
    lifespan=lifespan
)

# 文件传输国内那个CDN节点老有，BUG所以换成自己本地的

@app.get('/')
def index():
    return {"Hello": "World"}

@app.get('/stream')
def stream():
    def generate():
        for i in range(3):
            yield f"data chunk {i}\n"
            time.sleep(0.1) # 模拟一点点延迟，不能加太长免得测试卡住
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204) # 返回 204 No Content

app.include_router(api_v2)


register_exception_handlers(app)


register_middlewares(app)


# uvicorn main:app --reload

# 启动苦力，加上 --pool=solo 解决 Windows 兼容问题
# celery -A core.RAG.celery_app.celery_app worker --loglevel=info --pool=solo


# 前端页面
# streamlit run ui.py

# 重启 frontend 容器
# docker compose restart frontend