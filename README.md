# 🤖 DFY AI 中转站 (个人智能终端)

一个基于 **FastAPI + Streamlit + LangChain** 的个人全栈 AI 工具，支持多模态图片识别、工具调用（联网搜索/天气）、多轮对话记忆以及基于 Docker 的容器化部署。

## ✨ 核心特性

- **全栈分离架构**：Streamlit 负责前端交互，FastAPI 负责后端 API 与逻辑，通过 Docker Compose 一键拉起。
- **原生 SSE 流式输出**：后端使用 `StreamingResponse`，前端手写 SSE 解析器，实现丝滑的 Typewriter 打字机效果。
- **LangChain Agent 工具调用**：接入 Tavily 搜索 API 与天气插件，大模型可自主决策是否联网检索。
- **多模态图片解析**：支持单次上传多张图片，转换为 Base64 后交由 Vision 模型统一解析。
- **JWT 鉴权与历史回填**：刷新前端不丢失历史记录，后端数据库同步 `chat_message`，前端依靠 Token 无感拉取记录。
- **System Prompt 硬隔离**：系统人设焊死在 `system` 角色，避免历史记录污染。

## 🛠️ 技术栈

- **后端**：Python 3.12, FastAPI, SQLModel, Pydantic v2
- **前端**：Streamlit
- **AI 编排**：LangChain, LangChain-OpenAI (DeepSeek)
- **部署**：Docker, Docker Compose
- **其他**：Tavily Search, JWT Auth

## 🚀 快速启动

1. 克隆项目：
   ```bash
   git clone https://github.com/your_username/DFY-AI.git
   cd DFY-AI
配置环境变量：

cp .env.example .env
# 编辑 .env 文件，填入你的 DEEPSEEK_API_KEY 和 TAVILY_API_KEY
启动容器：

docker-compose up -d --build
访问前端： 浏览器打开 http://localhost:8501

📂 目录结构
DFY/
├── core/           # 核心配置与安全鉴权
├── crud/           # 数据库操作
├── models/         # SQLModel 实体
├── routers/        # FastAPI 路由 (chat, kb, history)
├── schemas/        # Pydantic 校验模型
├── ui.py           # Streamlit 前端主入口
├── main.py         # FastAPI 后端主入口
├── docker-compose.yml
└── .env.example
⚠️ 注意事项
本项目仅供个人学习与接单演示使用，请勿将 API Key 直接硬编码在源码中。