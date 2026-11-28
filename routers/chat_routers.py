from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session ,select
import tiktoken
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
import json
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback

# 导入项目内的依赖
from db.session import get_db
from models.chat import ChatMessage
from schemas.chat_schemas import ChatRequest
from core.config import settings
from core.Tookls.weather import get_weather
from core.Tookls.search import tavily_tool

with open("prompts.txt", "r", encoding="utf-8") as f:
    PERSONA_PROMPT = f.read()


def truncate_messages(messages: list, max_tokens: int = 30000):
    """从最老的消息开始删，直到总 Token 数小于限制（兼容 dict / 对象 / 多模态 content）"""
    encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(m):
        c = m['content'] if isinstance(m, dict) else m.content
        if isinstance(c, list):
            return sum(
                len(encoding.encode(part.get('text', '')))
                for part in c
                if part.get('type') == 'text'
            )
        return len(encoding.encode(c or ""))

    total_tokens = sum(count_tokens(m) for m in messages)
    while total_tokens > max_tokens and len(messages) > 1:
        removed = messages.pop(1)
        total_tokens -= count_tokens(removed)
    return messages



chat_router = APIRouter(prefix="/chat", tags=["AI 对话"])


@chat_router.post("/ask")
async def chat_with_ai(
        req: ChatRequest,
        db: Session = Depends(get_db),
):
    # 2、先查历史记录（此时数据库里还没有当前问题）
    history_records = db.exec(
        select(ChatMessage)
        .order_by(ChatMessage.create_time.desc())
        .limit(51)
    ).all()
    history_records.reverse()

    # 构建基础 messages
    current_time = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    messages = [{"role": "system", "content": f"{PERSONA_PROMPT}\n\n当前北京时间：{current_time}"}]
    for msg in history_records:
        if msg.image_url:
            messages.append({
                'role': msg.role_type,
                'content': [
                    {'type': 'text', 'text': msg.content or ""},
                    {'type': 'image_url', 'image_url': {'url': msg.image_url}}
                ]
            })
        else:
            messages.append({'role': msg.role_type, 'content': msg.content or ""})

    # 3、带图分支：走多模态
    if req.image_urls:
        client = ChatOpenAI(
            model=settings.vision_model,  # 这里用小写，匹配你的 config.py
            api_key=settings.api_key,
            base_url="https://api.deepseek.com",
            streaming=True,
        )

        # 构造发给大模型的多模态输入
        user_content = [{"type": "text", "text": req.question}]

        # 遍历前端传来的图片列表，全部塞进去
        for url in req.image_urls:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": url}
            })

        # 拼接到对话历史中
        messages.append({"role": "user", "content": user_content})

        # 存数据库（数据库字段只支持存一个字符串，这里先存第一张图或者留空）
        save_img_url = req.image_urls[0] if req.image_urls else None
        db.add(ChatMessage(
            role_type="user",
            content=req.question,
            image_url=save_img_url
        ))
        db.commit()

        messages = truncate_messages(messages, max_tokens=24000)

        async def vision_stream_generator():
            full_ai_responses = ""
            try:
                async for chunk in client.astream(messages):
                    if chunk.content:
                        full_ai_responses += chunk.content
                        payload = json.dumps({"content": chunk.content}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                err = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: [ERROR] {err}\n\n"
                yield "data: [DONE]\n\n"

            finally:
                if full_ai_responses:
                    ai_msg = ChatMessage(role_type="assistant", content=full_ai_responses)
                    db.add(ai_msg)
                    db.commit()

        return StreamingResponse(vision_stream_generator(), media_type="text/event-stream")

    else:
        # ---- 纯文本分支 ----
        client = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.api_key,
            base_url="https://api.deepseek.com"
        )

        # 4、绑定工具（纯文本分支：走 Agent）
        tools = [get_weather, tavily_tool]

        system_prompt = PERSONA_PROMPT  # 直接用从 prompts.txt 读进来的

        # 5、定义提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ('system',system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")  # 工具调用的草稿纸(提前留个工具的位置）
        ])

        # 6、创建 Agent
        agent = create_tool_calling_agent(client, tools, prompt)

        chat_history = []
        for msg in history_records:
            if msg.role_type == "user":
                chat_history.append(HumanMessage(content=msg.content or ""))
            else:
                chat_history.append(AIMessage(content=msg.content or ""))
        chat_history = truncate_messages(chat_history, max_tokens=30000)

        # 10、如果ai判断需要工具
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            return_intermediate_steps=True,  # 允许获取工具步骤
            handle_parsing_errors=True,  # 大模型输出格式不对时，不崩溃，继续处理
            max_iterations=3,
        )

        # 11、现在再去把当前问题存入数据库
        user_msg = ChatMessage(
            role_type="user",
            content=req.question
        )
        db.add(user_msg)
        db.commit()

        # 12、定义异步生成器（负责流式返回，并在最后把 AI 回答存入数据库）
        async def stream_generator():
            full_ai_response = ""  # 用来收集 AI 完整回答的缓冲器

            try:
                # 遍历大模型返回的流式数据包(核心：使用 astream 替代 ainvoke）
                async for event in agent_executor.astream({
                    'input': req.question,
                    'chat_history': chat_history,
                }):
                    # langchain 的 Agent 流式输出会返回不同的事件类型
                    if 'actions' in event:
                        payload = json.dumps({"content": "用工具呢等会..."}, ensure_ascii=False)
                        yield f'data: {payload}\n\n'
                    elif 'steps' in event:
                        # 工具执行结果
                        for step in event['steps']:
                            observation = getattr(step, 'observation', '')
                            payload = json.dumps({"content": f"出结果了：{observation}"}, ensure_ascii=False)
                            yield f'data: {payload}\n\n'     # 注意别下标去访问

                    elif 'output' in event:
                        # 大模型开始润色了
                        content = event['output']
                        full_ai_response += content
                        payload = json.dumps({"content": content}, ensure_ascii=False)
                        yield f'data: {payload}\n\n'

                yield 'data: [DONE]\n\n'


            except Exception as e:

                print("\n" + "=" * 50)  # 1
                print(f"💥 捕获到致命错误: {str(e)}")   # 2
                traceback.print_exc()   # 在后台生成详细的报错数据
                print("=" * 50 + "\n")  # 3

                err = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: [err] {err}\n\n"
                yield "data: [DONE]\n\n"
                # full_ai_response = "抱歉，生成回复时出错了。"
                full_ai_response = f"系统报错了: {str(e)}"

            finally:
                # 13、核心：无论流式是否报错，结束时都把 AI 的完整回答存入数据库
                if full_ai_response:
                    ai_msg = ChatMessage(
                        role_type="assistant",
                        content=full_ai_response
                    )
                    db.add(ai_msg)
                    db.commit()

        # 14、返回流式响应
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
