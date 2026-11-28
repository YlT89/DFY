import streamlit as st
import requests
import json
import time
import os
import base64


if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# 本地跑的时候，指向 DFY 后端的 8001 端口
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

# 拉取历史消息
if 'messages' not in st.session_state:
    st.session_state.messages = []

    # 一刷新，就悄悄去后台要历史记录
    try:
        resp = requests.get(f"{API_BASE_URL}/api/history/historical")
        if resp.status_code == 200:
            history_data = resp.json()
            for msg in history_data:
                # 把历史数据按 Streamlit 的格式塞进 session_state
                st.session_state.messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "image_url": msg.get("image_url")  # 兼容之前的图片
                })
    except Exception as e:
        print(f"拉取历史记录失败: {e}")

# 必须有这一段，要把 session_state 里的消息显示出来！
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("image_url"):
            st.image(message["image_url"])
        st.markdown(message["content"])

# 装修页面（可以理解为给屋里添置家具），必须放最前面
st.set_page_config(page_title="AI 知识库助手", page_icon="🤖")
st.title("🤖 我的专属 AI 知识库")

# 侧边栏配置
with st.sidebar:
    mode = st.radio("选择对话模式", ["普通对话（支持识图）", "知识库问答（RAG）"])
    st.header("⚙️ 个人 AI 终端")
    kb_id = st.number_input("当前知识库 ID", min_value=1, value=1)
    st.info("💡 私人专属助手，无需 Token。")
    st.header("📷 识图模式")
    uploaded_files = st.file_uploader(
        "上传图片",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"img_uploader_{st.session_state.uploader_key}"  # <- 核心：加上动态 key
    )
    image_urls = []
    if uploaded_files:
        for file in uploaded_files:
            img_bytes = file.read()
            base64_str = base64.b64encode(img_bytes).decode("utf-8")
            image_urls.append(f"data:{file.type};base64,{base64_str}")

    # 下面保留你的文件上传框
    st.divider()
    st.subheader('📁 上传知识库文档')

    # 1、文件上传组件
    uploaded_file = st.file_uploader('选择 txt / pdf 文件', type=['txt', 'pdf'])

    # 2、上传按钮
    if st.button('开始上传并解析', width="stretch"):
        if not uploaded_file:
            st.warning('选个文件呗伙计...')
        else:
            # 准备发给后端的 multipart
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/octet-stream')}

            # 3、发给 FastAPI
            with st.spinner('文件上传中...'):
                try:
                    res = requests.post(
                        url = f"{API_BASE_URL}/api/kb/{kb_id}/upload",
                        files=files,
                        timeout=10
                    )
                    if res.status_code != 200:
                        st.error(f"上传失败，状态码: {res.status_code}")
                        st.write(f"后端返回类型: {type(res)}")  # 看看它到底是个啥
                        st.stop()
                    task_data = res.json()
                    task_id = task_data.get('task_id')
                    if not task_id:
                        st.error(f"后端没返回 task_id: {task_data}")
                        st.stop()
                    st.success('上传成功了~ 稍等后台正在处理...')

                    # 4、轮询查询进度（放进一个状态圈里）
                    with st.status('AI 正在拼命切分和向量化...', expanded=True) as status:
                        while True:
                            try:
                                # 调用时后端状态查询窗口（确保路径一致）
                                status_res = requests.get(
                                    url = f"{API_BASE_URL}/api/kb/{kb_id}/task/{task_id}/status",
                                    timeout=5
                                )
                                if status_res.status_code != 200:
                                    status.update(label='查询状态失败', state='error')
                                    st.error(f"查询失败: {status_res.text}")
                                    break
                                state = status_res.json().get('status')

                                if state == 'SUCCESS':
                                    st.write('弄完了，来聊天吧~')
                                    status.update(label='解析完成', state='complete', expanded=False)
                                    break
                                elif state == 'FAILURE':
                                    st.write('吆喝失败了，去看看后端日志')
                                    status.update(label='解析失败', state='error')
                                    break
                                else:
                                    # 状态是 'STARTED' 或者 'PENDING' 等，继续等
                                    status.update(label=f'AI 正在处理中... (当前状态: {state})', state='running')
                                    time.sleep(3)   # 间隔三秒查询一次
                            except requests.exceptions.RequestException as req_err:
                                    status.update(label='网络请求异常', state='error')
                                    st.error(f'查询进度网络断开: {req_err}')
                                    break

                except Exception as e:
                    st.error(f'上传请求报错: {e}')


# 初始化聊天记录
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []   # 次元口袋，页面不关消息不丢

# 渲染历史信息（翻旧账，把以前的回忆拿出来）
for msg in st.session_state['chat_history']:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        # 如果历史记录里有图片，也可以在这里渲染
        if msg.get('image_base64'):
            img = msg['image_base64']
            if img.startswith('data:'):
                st.image(img, width=200)
            else:
                st.image(base64.b64decode(img), width=200)


# 聊天输入框
if question := st.chat_input('请输入你想问的问题...'):   # :=（海象运算符）如果回车消息就存起来，然后执行下面的代码

    # 1、展示用户问题
    st.session_state['chat_history'].append({"role": "user", "content": question,"image_urls": image_urls})
    with st.chat_message("user"):
        st.markdown(question)
        # 循环展示所有上传的图片
        for url in image_urls:
            # 把 data:image/xxx;base64,xxx 解码显示
            img_base64_data = url.split(",") [1]
            st.image(base64.b64decode(img_base64_data), width=200)


    # 2. 调用后端流式接口
    with st.chat_message("assistant"):

        response_placeholder = st.empty()
        full_response = ""


        # 动态路由
        if mode == "普通对话（支持识图）":
            url = f"{API_BASE_URL}/api/chat/ask"  # 对应 chat_routers.py
            data = {
                "question": question,
                "image_urls": image_urls  # 直接把列表传给后端
            }
        else:
            url = f"{API_BASE_URL}/api/kb/{kb_id}/chat"  # 对应 kb_router.py
            data = {
                "question": question
            }


        try:
            # 使用无代理 session，防止被本地科学上网软件截断流
            session = requests.Session()
            session.trust_env = False

            with session.post(url, json=data, stream=True, timeout=(5, 120)) as r:
                if r.status_code != 200:
                    st.error(f"请求失败: {r.status_code} - {r.text}")
                else:
                    # 按照 SSE 标准格式解析
                    for line in r.iter_lines():
                        if not line:
                            continue
                        decoded_line = line.decode('utf-8')
                        if not decoded_line.startswith("data: "):
                            continue

                        raw = decoded_line[6:]

                        if raw == "[DONE]":
                            break

                        if raw.startswith("[ERROR]"):
                            try:
                                err_data = json.loads(raw[7:])
                                st.error(f"后端错误：{err_data.get('error', raw)}")
                            except Exception:
                                st.error(raw)
                            break

                        # 解析 JSON
                        try:
                            data = json.loads(raw)
                            # 兼容后端的报错格式
                            if 'error' in data:
                                content = f"\n\n[后端开小差了，请查看后台日志]"
                                print(f"后台真实报错: {data['error']}")
                            else:
                                content = data.get("content", "")
                        except json.JSONDecodeError:
                            # 兼容旧格式（万一有漏网的）
                            content = raw.replace("\\n", "\n")

                        full_response += content

                        # 打字机效果
                        response_placeholder.markdown(full_response + " ▌")
                        time.sleep(0.01)

                    # 最终渲染
                    response_placeholder.markdown(full_response)
                    st.session_state['chat_history'].append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"连接后端失败: {e}")
            print(f"\n[UI ERROR] {e}\n")

        st.session_state.uploader_key += 1
        st.rerun()  # 强制页面瞬间刷新，清空左侧图片框
