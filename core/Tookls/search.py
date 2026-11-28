from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from core.config import settings
import json

# 1. 实例化 LangChain 官方封装好的 Tavily 工具
# 它会自动读取环境变量 TAVILY_API_KEY，或者我们手动传进去
# max_results=3 表示每次只返回前 3 个网页的结果，防止上下文太长
tavily_search = TavilySearchResults(
    max_results=3,
    tavily_api_key=settings.tavily_api_key
)

@tool
def tavily_tool(loc: str) -> str:
    """当你不知道最新的知识，或者需要查询实时新闻、最新版本信息时，使用这个搜索工具。"""
    try:
        # 直接调用 LangChain 封装好的工具，它会自动帮你处理 HTTP 请求和 JSON 解析
        results = tavily_search.invoke(loc)

        # 它返回的本身就是干净的列表/字符串，直接转成字符串给大模型就行
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"搜索失败，错误信息: {str(e)}"