# # # # # -*- coding: utf-8 -*-
# # # # # @Time    : 2026/3/26 10:49
# # # # # @Author  : mcy
# # # # # @File    : backend_gemma3.py
# # # # import asyncio
# # # # import requests
# # # # import json
# # # # from fastapi import FastAPI
# # # # from fastapi.responses import StreamingResponse
# # # # from pydantic import BaseModel
# # # # from typing import List, Dict, Optional
# # # #
# # # # app = FastAPI()
# # # #
# # # # # Ollama 服务地址（默认端口 11434）
# # # # OLLAMA_URL = "http://localhost:11434/api/chat"
# # # #
# # # # # 默认模型名称（可修改为你拉取的模型，如 qwen2.5:7b）
# # # # DEFAULT_MODEL = "qwen2.5:7b"
# # # #
# # # # # 请求数据结构（与前端一致）
# # # # class ChatRequest(BaseModel):
# # # #     query: str
# # # #     sys_prompt: str = "You are a helpful assistant."
# # # #     history_len: int = 1
# # # #     history: List[Dict[str, str]] = []
# # # #     temperature: float = 0.5
# # # #     top_p: float = 0.5
# # # #     max_tokens: int = 1024
# # # #     stream: bool = True
# # # #
# # # # def build_ollama_messages(request: ChatRequest):
# # # #     """
# # # #     将前端传来的消息历史转换为 Ollama 的 messages 格式。
# # # #     Ollama 的消息格式：[{"role": "system", "content": ...}, {"role": "user", "content": ...}, ...]
# # # #     """
# # # #     messages = []
# # # #     # 添加系统提示
# # # #     if request.sys_prompt:
# # # #         messages.append({"role": "system", "content": request.sys_prompt})
# # # #     # 添加历史对话（保留最近 history_len 条）
# # # #     # 注意：前端 history 中包含 user 和 assistant 交替的消息，我们直接使用
# # # #     history = request.history[-request.history_len:] if request.history_len > 0 else []
# # # #     messages.extend(history)
# # # #     # 添加当前用户消息
# # # #     messages.append({"role": "user", "content": request.query})
# # # #     return messages
# # # #
# # # # def generate_non_stream(request: ChatRequest):
# # # #     """非流式调用 Ollama"""
# # # #     messages = build_ollama_messages(request)
# # # #     payload = {
# # # #         "model": DEFAULT_MODEL,
# # # #         "messages": messages,
# # # #         "stream": False,
# # # #         "options": {
# # # #             "temperature": request.temperature,
# # # #             "top_p": request.top_p,
# # # #             "num_predict": request.max_tokens  # Ollama 中使用 num_predict 控制生成长度
# # # #         }
# # # #     }
# # # #     response = requests.post(OLLAMA_URL, json=payload, timeout=60)
# # # #     response.raise_for_status()
# # # #     data = response.json()
# # # #     # Ollama 返回的格式：{"message": {"content": "..."}, ...}
# # # #     return data.get("message", {}).get("content", "")
# # # #
# # # # async def generate_stream(request: ChatRequest):
# # # #     """流式调用 Ollama"""
# # # #     messages = build_ollama_messages(request)
# # # #     payload = {
# # # #         "model": DEFAULT_MODEL,
# # # #         "messages": messages,
# # # #         "stream": True,
# # # #         "options": {
# # # #             "temperature": request.temperature,
# # # #             "top_p": request.top_p,
# # # #             "num_predict": request.max_tokens
# # # #         }
# # # #     }
# # # #     # 发送流式请求
# # # #     with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) as response:
# # # #         response.raise_for_status()
# # # #         for line in response.iter_lines():
# # # #             if line:
# # # #                 # Ollama 每行返回一个 JSON 对象
# # # #                 try:
# # # #                     chunk = json.loads(line)
# # # #                     if "message" in chunk and "content" in chunk["message"]:
# # # #                         content = chunk["message"]["content"]
# # # #                         yield content
# # # #                 except json.JSONDecodeError:
# # # #                     continue
# # # #         # 可选：最后可以加一个结束标记，但不需要
# # # #         await asyncio.sleep(0)
# # # #
# # # # @app.post("/chat")
# # # # async def chat(request: ChatRequest):
# # # #     if request.stream:
# # # #         return StreamingResponse(generate_stream(request), media_type="text/plain")
# # # #     else:
# # # #         response_text = generate_non_stream(request)
# # # #         return response_text
# # # #
# # # # @app.get("/")
# # # # def root():
# # # #     return {"status": "ok", "model": DEFAULT_MODEL, "backend": "ollama"}
# # # #
# # # #
# # # # #导入mcp工具
# # # #
# # # # -*- coding: utf-8 -*-
# # # # @Time    : 2026/3/26 10:49
# # # # @Author  : mcy
# # # # @File    : main.py (集成 MCP 文件系统工具，按需连接)
# # # import asyncio
# # # import json
# # # from contextlib import asynccontextmanager
# # # from typing import List, Dict, Optional, Any
# # #
# # # import httpx
# # # from fastapi import FastAPI
# # # from fastapi.responses import StreamingResponse
# # # from pydantic import BaseModel
# # # from mcp import ClientSession
# # # from mcp.client.sse import sse_client
# # #
# # # # ---------- 配置 ----------
# # # OLLAMA_URL = "http://localhost:11434/api/chat"
# # # DEFAULT_MODEL = "qwen2.5:7b"
# # # MCP_SERVER_URL = "http://127.0.0.1:8001/sse"   # FastMCP 默认 SSE 端点
# # #
# # # # ---------- 数据模型 ----------
# # # class ChatRequest(BaseModel):
# # #     query: str
# # #     sys_prompt: str = "You are a helpful assistant."
# # #     history_len: int = 1
# # #     history: List[Dict[str, str]] = []
# # #     temperature: float = 0.5
# # #     top_p: float = 0.5
# # #     max_tokens: int = 1024
# # #     stream: bool = True
# # #
# # # # ---------- 全局工具缓存 ----------
# # # mcp_tools: List[Dict[str, Any]] = []   # 存储 Ollama 格式的工具定义
# # #
# # # async def fetch_mcp_tools():
# # #     """临时连接 MCP 服务器，获取工具定义并转换为 Ollama 格式"""
# # #     tools = []
# # #     try:
# # #         async with sse_client(MCP_SERVER_URL) as streams:
# # #             async with ClientSession(*streams) as session:
# # #                 await session.initialize()
# # #                 result = await session.list_tools()
# # #                 for tool in result.tools:
# # #                     parameters = tool.inputSchema or {"type": "object", "properties": {}}
# # #                     tools.append({
# # #                         "type": "function",
# # #                         "function": {
# # #                             "name": tool.name,
# # #                             "description": tool.description or "",
# # #                             "parameters": parameters
# # #                         }
# # #                     })
# # #     except Exception as e:
# # #         print(f"[MCP] 获取工具列表失败: {e}")
# # #     return tools
# # #
# # # async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
# # #     """临时建立 MCP 连接，调用指定工具，返回结果字符串"""
# # #     try:
# # #         async with sse_client(MCP_SERVER_URL) as streams:
# # #             async with ClientSession(*streams) as session:
# # #                 await session.initialize()
# # #                 result = await session.call_tool(tool_name, arguments=arguments)
# # #                 # 提取文本内容
# # #                 texts = [c.text for c in result.content if hasattr(c, "text")]
# # #                 return "\n".join(texts) if texts else "工具执行成功，但没有返回内容"
# # #     except Exception as e:
# # #         return f"调用工具 {tool_name} 时出错: {str(e)}"
# # #
# # # # ---------- 应用生命周期 ----------
# # # @asynccontextmanager
# # # async def lifespan(app: FastAPI):
# # #     # 启动时获取工具列表并缓存
# # #     global mcp_tools
# # #     print("[MCP] 正在连接服务器获取工具列表...")
# # #     mcp_tools = await fetch_mcp_tools()
# # #     print(f"[MCP] 已加载 {len(mcp_tools)} 个工具: {[t['function']['name'] for t in mcp_tools]}")
# # #     yield
# # #
# # # app = FastAPI(lifespan=lifespan)
# # #
# # # # ---------- Ollama 调用辅助函数 ----------
# # # def build_messages(request: ChatRequest, extra_messages: List[Dict] = None):
# # #     """构建消息列表：系统提示 + 历史对话 + 当前用户消息 + 额外消息（工具调用结果等）"""
# # #     messages = []
# # #     if request.sys_prompt:
# # #         messages.append({"role": "system", "content": request.sys_prompt})
# # #     # 历史对话保留最近 history_len 条
# # #     history = request.history[-request.history_len:] if request.history_len > 0 else []
# # #     messages.extend(history)
# # #     # 当前用户消息
# # #     messages.append({"role": "user", "content": request.query})
# # #     if extra_messages:
# # #         messages.extend(extra_messages)
# # #     return messages
# # #
# # # async def complete_with_tools(request: ChatRequest, stream: bool = False):
# # #     """
# # #     核心逻辑：可能会进行多轮工具调用，最终返回 (final_text, stream_generator)
# # #     流式模式下，内部先完成所有工具调用，最后以生成器形式流式输出最终文本。
# # #     """
# # #     current_messages = build_messages(request)
# # #     max_iterations = 5
# # #
# # #     for _ in range(max_iterations):
# # #         # 调用 Ollama（非流式，便于检测 tool_calls）
# # #         payload = {
# # #             "model": DEFAULT_MODEL,
# # #             "messages": current_messages,
# # #             "stream": False,
# # #             "tools": mcp_tools if mcp_tools else None,
# # #             "options": {
# # #                 "temperature": request.temperature,
# # #                 "top_p": request.top_p,
# # #                 "num_predict": request.max_tokens
# # #             }
# # #         }
# # #         async with httpx.AsyncClient(timeout=60) as client:
# # #             resp = await client.post(OLLAMA_URL, json=payload)
# # #             resp.raise_for_status()
# # #             data = resp.json()
# # #             assistant_message = data.get("message", {})
# # #             content = assistant_message.get("content", "")
# # #             tool_calls = assistant_message.get("tool_calls", [])
# # #
# # #         # 将 assistant 消息加入历史
# # #         assistant_role_msg = {"role": "assistant", "content": content}
# # #         if tool_calls:
# # #             assistant_role_msg["tool_calls"] = tool_calls
# # #         current_messages.append(assistant_role_msg)
# # #
# # #         if not tool_calls:
# # #             # 没有工具调用，最终回答
# # #             final_text = content
# # #             if stream:
# # #                 async def stream_final():
# # #                     # 流式输出最终文本（按字符分块）
# # #                     for chunk in final_text:
# # #                         yield chunk
# # #                         await asyncio.sleep(0.01)
# # #                 return None, stream_final()
# # #             else:
# # #                 return final_text, None
# # #
# # #         # 有工具调用：依次执行每个工具，并将结果以 tool 角色消息添加
# # #         for tc in tool_calls:
# # #             tool_name = tc["function"]["name"]
# # #             raw_args = tc["function"]["arguments"]
# # #             # 兼容两种格式：直接 dict 或者 JSON 字符串
# # #             if isinstance(raw_args, str):
# # #                 arguments = json.loads(raw_args)
# # #             else:
# # #                 arguments = raw_args  # 已解析的 dict
# # #             tool_call_id = tc.get("id", "")  # 可能没有 id 字段
# # #             result_text = await call_mcp_tool(tool_name, arguments)
# # #             current_messages.append({
# # #                 "role": "tool",
# # #                 "tool_call_id": tool_call_id,
# # #                 "content": result_text
# # #             })
# # #         # 继续下一轮循环
# # #
# # #     # 超过最大迭代次数
# # #     error_msg = "工具调用循环次数过多，已终止。"
# # #     if stream:
# # #         async def stream_error():
# # #             yield error_msg
# # #         return None, stream_error()
# # #     else:
# # #         return error_msg, None
# # #
# # # # ---------- 路由 ----------
# # # @app.post("/chat")
# # # async def chat(request: ChatRequest):
# # #     if not mcp_tools:
# # #         print("[警告] MCP 工具未加载，将只进行纯对话。")
# # #
# # #     final_text, stream_gen = await complete_with_tools(request, stream=request.stream)
# # #     if request.stream and stream_gen:
# # #         return StreamingResponse(stream_gen, media_type="text/plain")
# # #     elif not request.stream and final_text is not None:
# # #         return {"response": final_text}
# # #     else:
# # #         return {"response": "处理出错"}
# # #
# # # @app.get("/")
# # # def root():
# # #     tool_names = [t["function"]["name"] for t in mcp_tools]
# # #     return {"status": "ok", "model": DEFAULT_MODEL, "backend": "ollama+mcp", "tools": tool_names}
# # import asyncio
# # import json
# # from contextlib import asynccontextmanager
# # from typing import List, Dict, Any, AsyncGenerator
# #
# # import httpx
# # from fastapi import FastAPI
# # from fastapi.responses import StreamingResponse
# # from pydantic import BaseModel
# # from mcp import ClientSession
# # from mcp.client.sse import sse_client
# #
# # # ========== 配置 ==========
# # OLLAMA_URL = "http://localhost:11434/api/chat"
# # DEFAULT_MODEL = "qwen2.5:7b"
# # MCP_SERVER_URL = "http://127.0.0.1:8001/sse"   # FastMCP 默认 SSE 端点
# #
# # # ========== Pydantic 请求模型 ==========
# # class ChatRequest(BaseModel):
# #     query: str
# #     sys_prompt: str = "You are a helpful assistant."
# #     history_len: int = 1
# #     history: List[Dict[str, str]] = []
# #     temperature: float = 0.5
# #     top_p: float = 0.5
# #     max_tokens: int = 1024
# #     stream: bool = True
# #
# # # ========== MCP 工具缓存 ==========
# # _tools_cache: List[Dict[str, Any]] = []   # Ollama 格式的函数定义
# #
# # # ========== MCP 辅助函数（复用连接）==========
# # async def _call_mcp(func):
# #     """
# #     通用 MCP 会话上下文管理器，自动连接、初始化，然后执行传入的异步函数。
# #     :param func: 异步函数，接收 (session) 参数，返回结果
# #     :return: 函数执行结果，若失败返回 None/错误信息（视调用上下文而定）
# #     """
# #     try:
# #         async with sse_client(MCP_SERVER_URL) as streams:
# #             async with ClientSession(*streams) as session:
# #                 await session.initialize()
# #                 return await func(session)
# #     except Exception as e:
# #         print(f"[MCP] 操作失败: {e}")
# #         return None
# #
# # async def fetch_mcp_tools() -> List[Dict[str, Any]]:
# #     """获取 MCP 服务器上的工具列表，并转换为 Ollama function-calling 格式"""
# #     async def _list(session):
# #         result = await session.list_tools()
# #         tools = []
# #         for tool in result.tools:
# #             tools.append({
# #                 "type": "function",
# #                 "function": {
# #                     "name": tool.name,
# #                     "description": tool.description or "",
# #                     "parameters": tool.inputSchema or {"type": "object", "properties": {}}
# #                 }
# #             })
# #         return tools
# #     tools = await _call_mcp(_list)
# #     return tools if tools is not None else []
# #
# # async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
# #     """调用 MCP 工具，返回结果字符串（文本或错误信息）"""
# #     async def _call(session):
# #         result = await session.call_tool(tool_name, arguments=arguments)
# #         # 提取所有 text 类型内容
# #         texts = [c.text for c in result.content if hasattr(c, "text")]
# #         return "\n".join(texts) if texts else "工具执行成功，但无文本返回"
# #     res = await _call_mcp(_call)
# #     return res if res is not None else f"调用工具 {tool_name} 失败"
# #
# # # ========== FastAPI 生命周期 ==========
# # @asynccontextmanager
# # async def lifespan(app: FastAPI):
# #     """启动时预加载 MCP 工具列表到缓存"""
# #     global _tools_cache
# #     print("[MCP] 正在获取工具列表...")
# #     _tools_cache = await fetch_mcp_tools()
# #     print(f"[MCP] 已加载 {len(_tools_cache)} 个工具")
# #     yield
# #
# # app = FastAPI(lifespan=lifespan)
# #
# # # ========== 聊天核心逻辑（支持工具调用循环）==========
# # async def complete_with_tools(request: ChatRequest):
# #     """
# #     处理多轮工具调用，最终返回最终回答文本。
# #     注意：即使 request.stream=True，也是内部先同步完成全部工具调用，再返回最终文本（流式输出仅用于最后一段）。
# #     返回: (final_text, stream_generator_or_None)
# #     """
# #     # 构建初始消息：system + history + current user
# #     messages = []
# #     if request.sys_prompt:
# #         messages.append({"role": "system", "content": request.sys_prompt})
# #     # 截取最近 history_len 条历史对话
# #     history = request.history[-request.history_len:] if request.history_len > 0 else []
# #     messages.extend(history)
# #     messages.append({"role": "user", "content": request.query})
# #
# #     max_iterations = 5   # 防止无限循环
# #
# #     for _ in range(max_iterations):
# #         # 请求 Ollama（非流式，以便解析 tool_calls）
# #         payload = {
# #             "model": DEFAULT_MODEL,
# #             "messages": messages,
# #             "stream": False,
# #             "tools": _tools_cache if _tools_cache else None,
# #             "options": {
# #                 "temperature": request.temperature,
# #                 "top_p": request.top_p,
# #                 "num_predict": request.max_tokens
# #             }
# #         }
# #         async with httpx.AsyncClient(timeout=60) as client:
# #             resp = await client.post(OLLAMA_URL, json=payload)
# #             resp.raise_for_status()
# #             data = resp.json()
# #             assistant = data.get("message", {})
# #             content = assistant.get("content", "")
# #             tool_calls = assistant.get("tool_calls", [])
# #
# #         # 记录 assistant 回复
# #         assistant_msg = {"role": "assistant", "content": content}
# #         if tool_calls:
# #             assistant_msg["tool_calls"] = tool_calls
# #         messages.append(assistant_msg)
# #
# #         # 无工具调用 -> 最终答案
# #         if not tool_calls:
# #             final_text = content
# #             if request.stream:
# #                 # 生成器：逐字符流式输出（模拟打字机效果）
# #                 async def streamer():
# #                     for ch in final_text:
# #                         yield ch
# #                         await asyncio.sleep(0.01)
# #                 return final_text, streamer()
# #             return final_text, None
# #
# #         # 有工具调用：按顺序执行每个工具，将结果以 tool 角色追加到消息列表
# #         for tc in tool_calls:
# #             tool_name = tc["function"]["name"]
# #             raw_args = tc["function"]["arguments"]
# #             args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args)
# #             tool_call_id = tc.get("id", "")
# #             result_text = await call_mcp_tool(tool_name, args)
# #             messages.append({
# #                 "role": "tool",
# #                 "tool_call_id": tool_call_id,
# #                 "content": result_text
# #             })
# #         # 继续下一轮循环，让模型看到工具调用结果
# #
# #     # 超过最大迭代次数
# #     error_msg = "工具调用循环次数过多，已终止。"
# #     if request.stream:
# #         async def error_stream():
# #             yield error_msg
# #         return error_msg, error_stream()
# #     return error_msg, None
# #
# # # ========== API 路由 ==========
# # @app.post("/chat")
# # async def chat(request: ChatRequest):
# #     """处理聊天请求，支持流式和非流式，自动使用 MCP 工具"""
# #     final_text, stream_gen = await complete_with_tools(request)
# #     if request.stream and stream_gen:
# #         return StreamingResponse(stream_gen, media_type="text/plain")
# #     elif not request.stream and final_text is not None:
# #         return {"response": final_text}
# #     else:
# #         return {"response": "处理请求时出错"}
# #
# # @app.get("/")
# # def root():
# #     """健康检查及当前配置信息"""
# #     return {
# #         "status": "ok",
# #         "model": DEFAULT_MODEL,
# #         "backend": "ollama + mcp",
# #         "tools": [t["function"]["name"] for t in _tools_cache]
# #     }
#
# import asyncio
# import json
# import uuid
# import os
# from contextlib import asynccontextmanager
# from typing import List, Dict, Any, Optional
#
# import httpx
# from fastapi import FastAPI,HTTPException
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# from mcp import ClientSession
# from mcp.client.sse import sse_client
# from databases import Database
#
# # ---------- 配置 ----------
# OLLAMA_URL = "http://localhost:11434/api/chat"
# DEFAULT_MODEL = "qwen2.5:7b"
# MCP_SERVER_URL = "http://127.0.0.1:8001/sse"
#
# # 数据库配置（使用环境变量存储密码，避免明文）
# # 请设置环境变量 MYSQL_PASSWORD，例如：set MYSQL_PASSWORD=your_password
# MYSQL_USER = "root"  # 修改为你的 MySQL 用户名
# MYSQL_HOST = "localhost"
# MYSQL_PORT = "3306"
# MYSQL_DB = "agenthistorl"
# MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "214216")  # 从环境变量读取，也可直接写
#
# DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
#
# # 如果要使用 SQLite 作为替代（无需密码），可以改为：
# # DATABASE_URL = "sqlite+aiosqlite:///./chat_history.db"
#
# database = Database(DATABASE_URL)
#
#
# # ---------- 数据模型 ----------
# class ChatRequest(BaseModel):
#     query: str
#     sys_prompt: str = "You are a helpful assistant."
#     history_len: int = 1
#     history: List[Dict[str, str]] = []
#     temperature: float = 0.5
#     top_p: float = 0.5
#     max_tokens: int = 1024
#     stream: bool = True
#     conversation_id: Optional[str] = None  # 会话标识，为空则自动生成
#
#
# # ---------- 全局工具缓存 ----------
# _tools_cache: List[Dict[str, Any]] = []
#
#
# # ---------- 数据库操作函数（已适配你的表名 agentmessages）----------
# async def save_message(conversation_id: str, role: str, content: str = None,
#                        tool_calls: List[Dict] = None, tool_call_id: str = None):
#     """
#     保存一条消息到 agentmessages 表
#     字段映射: conversation_id, role, content, tool_calls, tool_call_id
#     """
#     query = """
#             INSERT INTO agentmessages
#                 (conversation_id, role, content, tool_calls, tool_call_id)
#             VALUES (:conv_id, :role, :content, :tool_calls, :tool_call_id) \
#             """
#     await database.execute(query, values={
#         "conv_id": conversation_id,
#         "role": role,
#         "content": content,
#         "tool_calls": json.dumps(tool_calls) if tool_calls else None,
#         "tool_call_id": tool_call_id
#     })
#
#
# # ---------- MCP 集成 ----------
# async def _call_mcp(func):
#     """通用 MCP 会话上下文管理器"""
#     try:
#         async with sse_client(MCP_SERVER_URL) as streams:
#             async with ClientSession(*streams) as session:
#                 await session.initialize()
#                 return await func(session)
#     except Exception as e:
#         print(f"[MCP] 操作失败: {e}")
#         return None
#
#
# async def fetch_mcp_tools() -> List[Dict[str, Any]]:
#     async def _list(session):
#         result = await session.list_tools()
#         tools = []
#         for tool in result.tools:
#             tools.append({
#                 "type": "function",
#                 "function": {
#                     "name": tool.name,
#                     "description": tool.description or "",
#                     "parameters": tool.inputSchema or {"type": "object", "properties": {}}
#                 }
#             })
#         return tools
#
#     tools = await _call_mcp(_list)
#     return tools if tools is not None else []
#
#
# async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
#     async def _call(session):
#         result = await session.call_tool(tool_name, arguments=arguments)
#         texts = [c.text for c in result.content if hasattr(c, "text")]
#         return "\n".join(texts) if texts else "工具执行成功，但无文本返回"
#
#     res = await _call_mcp(_call)
#     return res if res is not None else f"调用工具 {tool_name} 失败"
#
#
# # ---------- 对话核心逻辑（带数据库记录）----------
# async def complete_with_tools(request: ChatRequest, conversation_id: str):
#     """
#     多轮工具调用，并在每个关键步骤将消息存入数据库
#     """
#     # 构建消息列表（用于 Ollama 上下文）
#     messages = []
#     if request.sys_prompt:
#         messages.append({"role": "system", "content": request.sys_prompt})
#         # 可选：将系统提示也存入数据库（作为单独消息）
#         # await save_message(conversation_id, "system", request.sys_prompt)
#     history = request.history[-request.history_len:] if request.history_len > 0 else []
#     messages.extend(history)
#     messages.append({"role": "user", "content": request.query})
#
#     # 保存用户消息（已带 conversation_id）
#     await save_message(conversation_id, "user", request.query)
#
#     max_iterations = 5
#     for _ in range(max_iterations):
#         payload = {
#             "model": DEFAULT_MODEL,
#             "messages": messages,
#             "stream": False,
#             "tools": _tools_cache if _tools_cache else None,
#             "options": {
#                 "temperature": request.temperature,
#                 "top_p": request.top_p,
#                 "num_predict": request.max_tokens
#             }
#         }
#         async with httpx.AsyncClient(timeout=60) as client:
#             resp = await client.post(OLLAMA_URL, json=payload)
#             resp.raise_for_status()
#             data = resp.json()
#             assistant = data.get("message", {})
#             content = assistant.get("content", "")
#             tool_calls = assistant.get("tool_calls", [])
#
#         # 保存 assistant 消息
#         await save_message(conversation_id, "assistant",
#                            content=content,
#                            tool_calls=tool_calls if tool_calls else None)
#
#         # 构建 assistant 消息并添加到上下文
#         assistant_msg = {"role": "assistant", "content": content}
#         if tool_calls:
#             assistant_msg["tool_calls"] = tool_calls
#         messages.append(assistant_msg)
#
#         if not tool_calls:
#             final_text = content
#             if request.stream:
#                 async def streamer():
#                     for ch in final_text:
#                         yield ch
#                         await asyncio.sleep(0.01)
#
#                 return final_text, streamer()
#             return final_text, None
#
#         # 处理工具调用
#         for tc in tool_calls:
#             tool_name = tc["function"]["name"]
#             raw_args = tc["function"]["arguments"]
#             args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args)
#             tool_call_id = tc.get("id", "")
#             result_text = await call_mcp_tool(tool_name, args)
#
#             # 保存 tool 消息
#             await save_message(conversation_id, "tool",
#                                content=result_text,
#                                tool_call_id=tool_call_id)
#
#             # 添加到上下文
#             messages.append({
#                 "role": "tool",
#                 "tool_call_id": tool_call_id,
#                 "content": result_text
#             })
#
#     error_msg = "工具调用循环次数过多，已终止。"
#     if request.stream:
#         async def error_stream():
#             yield error_msg
#
#         return error_msg, error_stream()
#     return error_msg, None
#
#
# # ---------- FastAPI 生命周期 ----------
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # 启动时：连接数据库 + 加载 MCP 工具
#     await database.connect()
#     print("[数据库] 连接成功")
#
#     global _tools_cache
#     print("[MCP] 正在获取工具列表...")
#     _tools_cache = await fetch_mcp_tools()
#     print(f"[MCP] 已加载 {len(_tools_cache)} 个工具")
#     yield
#     # 关闭时断开数据库
#     await database.disconnect()
#     print("[数据库] 连接已关闭")
#
#
# app = FastAPI(lifespan=lifespan)
#
#
# # ---------- API 路由 ----------
# @app.post("/chat")
# async def chat(request: ChatRequest):
#     # 生成或使用传入的会话 ID
#     conv_id = request.conversation_id or str(uuid.uuid4())
#     final_text, stream_gen = await complete_with_tools(request, conv_id)
#
#     response_data = {"conversation_id": conv_id}
#     if request.stream and stream_gen:
#         return StreamingResponse(stream_gen, media_type="text/plain")
#     elif not request.stream and final_text is not None:
#         response_data["response"] = final_text
#         return response_data
#     else:
#         response_data["response"] = "处理请求时出错"
#         return response_data
#
#
# # @app.get("/history/{conversation_id}")
# # async def get_conversation_history(conversation_id: str, limit: int = 50):
# #     """获取指定会话的历史消息（按时间升序）"""
# #     rows = await database.fetch_all(
# #         "SELECT role, content, tool_calls, tool_call_id, created_at FROM agentmessages "
# #         "WHERE conversation_id = :cid ORDER BY created_at LIMIT :limit",
# #         {"cid": conversation_id, "limit": limit}
# #     )
# #     return [dict(row) for row in rows]
#
# # ---------- 会话管理接口 ----------
# @app.get("/conversations")
# async def get_conversations(limit: int = 50, offset: int = 0):
#     query = """
#         SELECT conversation_id, MAX(created_at) as last_active
#         FROM agentmessages
#         GROUP BY conversation_id
#         ORDER BY last_active DESC
#         LIMIT :limit OFFSET :offset
#     """
#     rows = await database.fetch_all(query, {"limit": limit, "offset": offset})
#     result = []
#     for row in rows:
#         conv_id = row["conversation_id"]
#         last_active = row["last_active"]
#         preview_query = """
#             SELECT content FROM agentmessages
#             WHERE conversation_id = :conv_id AND role = 'user'
#             ORDER BY created_at ASC LIMIT 1
#         """
#         preview_row = await database.fetch_one(preview_query, {"conv_id": conv_id})
#         preview = preview_row["content"] if preview_row and preview_row["content"] else "空对话"
#         if len(preview) > 40:
#             preview = preview[:40] + "..."
#         result.append({
#             "conversation_id": conv_id,
#             "last_active": last_active.isoformat() if last_active else None,
#             "preview": preview
#         })
#     return result
#
#
# @app.get("/history/{conversation_id}")
# async def get_conversation_history(conversation_id: str, limit: int = 100):
#     query = """
#             SELECT id,conversation_id, role, content, tool_calls, tool_call_id, created_at
#             FROM agentmessages
#             WHERE conversation_id = :conv_id
#             ORDER BY created_at ASC
#             LIMIT :limit \
#             """
#     rows = await database.fetch_all(query, {"conv_id": conversation_id, "limit": limit})
#
#     result = []
#     for row in rows:
#         result.append({
#             "id": row["id"],# 🔑 必须包含这一行
#             "conversation_id": row["conversation_id"],
#             "role": row["role"],
#             "content": row["content"] or "",
#             "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else None,
#             "tool_call_id": row["tool_call_id"],
#             "created_at": row["created_at"].isoformat() if row["created_at"] else None
#         })
#     return result
#
# # ---------- 删除会话 ----------
# @app.delete("/conversation/{conversation_id}")
# async def delete_conversation(conversation_id: str):
#     """删除整个会话的所有消息"""
#     await database.execute(
#         "DELETE FROM agentmessages WHERE conversation_id = :conv_id",
#         {"conv_id": conversation_id}
#     )
#     return {"status": "deleted", "conversation_id": conversation_id}
#
# # ---------- 删除单条消息（同时删除该消息之后的所有消息，保持顺序完整性）----------
# @app.delete("/message/{message_id}")
# async def delete_message_and_following(message_id: int, conversation_id: str):
#     print(f"\n[删除请求] message_id={message_id}, conversation_id={conversation_id}")
#     # 先查询该消息
#     target = await database.fetch_one(
#         "SELECT id, role, content FROM agentmessages WHERE id = :id AND conversation_id = :conv_id",
#         {"id": message_id, "conv_id": conversation_id}
#     )
#     if not target:
#         print("❌ 未找到消息")
#         raise HTTPException(status_code=404, detail="Message not found")
#     print(f"📝 待删除起点: id={target['id']}, role={target['role']}, content={target['content'][:30]}")
#
#     # 删除 id >= message_id 的消息
#     result = await database.execute(
#         "DELETE FROM agentmessages WHERE conversation_id = :conv_id AND id >= :msg_id",
#         {"conv_id": conversation_id, "msg_id": message_id}
#     )
#     print(f"✅ 删除了 {result} 条消息")
#     return {"status": "deleted_following", "from_message_id": message_id}
# # ---------- 编辑用户消息并重新生成回答（实质：删除原用户消息及其后的回答，新增新用户消息并触发新回答）----------
# # 为了简化，我们复用删除接口 + 前端直接调用 /chat 接口。后端不需要额外接口，但前端需组合调用。
# # 因此后端只需要提供上面的删除接口即可。前端流程：
# # 1. 用户点击“重新提问”，前端获取原用户消息的 id 和 conversation_id
# # 2. 调用 DELETE /message/{message_id}?conversation_id=xxx 删除该消息及其后所有消息
# # 3. 然后将新的用户消息内容通过 /chat 接口发送（使用同一个 conversation_id）
#
# # ---------- 保存消息版本（用于保留多个回答版本）----------
# # 设计：在 agentmessages 表中增加字段 version_group_id (varchar) 来标记同一问题的不同回答版本，
# # 以及 version_index (int) 表示版本序号。但这样改动较大。更简单的做法：
# # 当前端需要重新生成时，不再删除旧消息，而是标记一条消息为“当前版本”，前端可以展示历史版本列表。
# # 考虑到复杂度，这里先不实现多版本切换功能，而是实现“重新提问”直接覆盖原消息及后续内容（等价于修改问题）。
#
#
# @app.get("/")
# def root():
#     return {
#         "status": "ok",
#         "model": DEFAULT_MODEL,
#         "backend": "ollama + mcp + mysql",
#         "tools": [t["function"]["name"] for t in _tools_cache]
#     }


###################最终版-1
import asyncio, json, uuid, os
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from mcp import ClientSession
from mcp.client.sse import sse_client
from databases import Database

# ---------- 配置 ----------
OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:7b"
MCP_SERVER_URL = "http://127.0.0.1:8001/sse"

MYSQL_USER, MYSQL_PASSWORD = "root", os.getenv("MYSQL_PASSWORD", "214216")
DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@localhost:3306/agenthistorl"
database = Database(DATABASE_URL)

# ---------- 数据模型 ----------
class ChatRequest(BaseModel):
    query: str
    sys_prompt: str = "You are a helpful assistant."
    history_len: int = 1
    history: List[Dict[str, str]] = []
    temperature: float = 0.5
    top_p: float = 0.5
    max_tokens: int = 1024
    stream: bool = True
    conversation_id: Optional[str] = None

_tools_cache: List[Dict[str, Any]] = []

# ---------- 数据库操作 ----------
async def save_message(conv_id: str, role: str, content: str = None, tool_calls: List[Dict] = None, tool_call_id: str = None):
    await database.execute(
        "INSERT INTO agentmessages (conversation_id, role, content, tool_calls, tool_call_id) VALUES (:conv_id, :role, :content, :tool_calls, :tool_call_id)",
        {"conv_id": conv_id, "role": role, "content": content, "tool_calls": json.dumps(tool_calls) if tool_calls else None, "tool_call_id": tool_call_id}
    )

# ---------- MCP 辅助 ----------
async def _call_mcp(func):
    try:
        async with sse_client(MCP_SERVER_URL) as streams, ClientSession(*streams) as session:
            await session.initialize()
            return await func(session)
    except Exception as e:
        print(f"[MCP] 失败: {e}")
        return None

async def fetch_mcp_tools():
    tools = await _call_mcp(lambda s: s.list_tools())
    if not tools: return []
    return [{"type": "function", "function": {"name": t.name, "description": t.description or "", "parameters": t.inputSchema or {"type": "object", "properties": {}}}} for t in tools.tools]

async def call_mcp_tool(name: str, args: dict) -> str:
    res = await _call_mcp(lambda s: s.call_tool(name, arguments=args))
    texts = [c.text for c in res.content if hasattr(c, "text")] if res else []
    return "\n".join(texts) if texts else "工具执行成功"

# ---------- 核心对话（自动记录工具调用）----------
async def complete_with_tools(req: ChatRequest, conv_id: str):
    messages = []
    if req.sys_prompt:
        messages.append({"role": "system", "content": req.sys_prompt})
    messages.extend(req.history[-req.history_len:] if req.history_len else [])
    messages.append({"role": "user", "content": req.query})
    await save_message(conv_id, "user", req.query)

    for _ in range(5):
        payload = {
            "model": DEFAULT_MODEL, "messages": messages, "stream": False,
            "tools": _tools_cache or None,
            "options": {"temperature": req.temperature, "top_p": req.top_p, "num_predict": req.max_tokens}
        }
        async with httpx.AsyncClient(timeout=60) as client:
            data = (await client.post(OLLAMA_URL, json=payload)).json()
            assistant = data.get("message", {})
            content, tool_calls = assistant.get("content", ""), assistant.get("tool_calls", [])

        await save_message(conv_id, "assistant", content, tool_calls)
        assistant_msg = {"role": "assistant", "content": content}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            final = content
            if req.stream:
                async def gen():
                    for ch in final:
                        yield ch
                        await asyncio.sleep(0.01)
                return final, gen()
            return final, None

        for tc in tool_calls:
            args = tc["function"]["arguments"]
            if isinstance(args, str): args = json.loads(args)
            result = await call_mcp_tool(tc["function"]["name"], args)
            await save_message(conv_id, "tool", result, tool_call_id=tc.get("id", ""))
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result})

    error = "工具调用次数过多，已终止。"
    return error, (lambda: (yield error))() if req.stream else error

# ---------- 生命周期 ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    print("[数据库] 连接成功")
    global _tools_cache
    print("[MCP] 获取工具...")
    _tools_cache = await fetch_mcp_tools()
    print(f"[MCP] 加载 {len(_tools_cache)} 个工具")
    yield
    await database.disconnect()
    print("[数据库] 断开")

app = FastAPI(lifespan=lifespan)

# ---------- API 路由 ----------
@app.post("/chat")
async def chat(req: ChatRequest):
    conv_id = req.conversation_id or str(uuid.uuid4())
    final, gen = await complete_with_tools(req, conv_id)
    if req.stream and gen:
        return StreamingResponse(gen, media_type="text/plain")
    return {"response": final, "conversation_id": conv_id} if not req.stream else {"conversation_id": conv_id}

@app.get("/conversations")
async def list_conversations(limit: int = 50, offset: int = 0):
    rows = await database.fetch_all("SELECT conversation_id, MAX(created_at) as last_active FROM agentmessages GROUP BY conversation_id ORDER BY last_active DESC LIMIT :limit OFFSET :offset", {"limit": limit, "offset": offset})
    result = []
    for row in rows:
        prev = await database.fetch_one("SELECT content FROM agentmessages WHERE conversation_id = :cid AND role='user' ORDER BY created_at LIMIT 1", {"cid": row["conversation_id"]})
        preview = prev["content"][:40] + "..." if prev and prev["content"] else "空对话"
        result.append({"conversation_id": row["conversation_id"], "last_active": row["last_active"].isoformat() if row["last_active"] else None, "preview": preview})
    return result

@app.get("/history/{conversation_id}")
async def get_history(conversation_id: str, limit: int = 100):
    rows = await database.fetch_all("SELECT id, conversation_id, role, content, tool_calls, tool_call_id, created_at FROM agentmessages WHERE conversation_id = :cid ORDER BY created_at ASC LIMIT :limit", {"cid": conversation_id, "limit": limit})
    return [{"id": r["id"], "conversation_id": r["conversation_id"], "role": r["role"], "content": r["content"] or "", "tool_calls": json.loads(r["tool_calls"]) if r["tool_calls"] else None, "tool_call_id": r["tool_call_id"], "created_at": r["created_at"].isoformat() if r["created_at"] else None} for r in rows]

@app.delete("/conversation/{conversation_id}")
async def del_conversation(conversation_id: str):
    await database.execute("DELETE FROM agentmessages WHERE conversation_id = :cid", {"cid": conversation_id})
    return {"status": "deleted"}

@app.delete("/message/{message_id}")
async def del_message_and_following(message_id: int, conversation_id: str):
    target = await database.fetch_one("SELECT id FROM agentmessages WHERE id = :id AND conversation_id = :cid", {"id": message_id, "cid": conversation_id})
    if not target:
        raise HTTPException(404, "消息不存在")
    await database.execute("DELETE FROM agentmessages WHERE conversation_id = :cid AND id >= :mid", {"cid": conversation_id, "mid": message_id})
    return {"status": "deleted_following"}

@app.get("/")
def root():
    return {"status": "ok", "model": DEFAULT_MODEL, "tools": [t["function"]["name"] for t in _tools_cache]}