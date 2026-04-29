# import os
# from mcp.server.fastmcp import FastMCP
#
# # 初始化 MCP 服务，名称为 "FileSystem"
# mcp = FastMCP("FileSystem")
#
# # 定义一个工具：获取桌面文件列表
# @mcp.tool()
# def get_desktop_files() -> list:
#     """获取当前用户的桌面文件列表"""
#     return os.listdir(os.path.expanduser("~/Desktop"))
#
# # 定义另一个工具：基础数学运算
# @mcp.tool()
# def calculator(a: float, b: float, operator: str) -> float:
#     """
#     执行基础数学运算（支持 + - * /）
#     Args:
#         operator: 运算符，必须是 '+', '-', '*', '/' 之一
#     """
#     if operator == '+':
#         return a + b
#     elif operator == '-':
#         return a - b
#     elif operator == '*':
#         return a * b
#     elif operator == '/':
#         return a / b
#     else:
#         raise ValueError("无效运算符")
#
# # if __name__ == "__main__":
# #     # 使用标准输入输出（stdio）通信，这是 MCP 客户端要求的传输方式
# #     mcp.run(transport='stdio')
#
# if __name__ == "__main__":
#     # 将 transport 改为 'sse'，并指定端口（例如 8001）
#     # mcp.run(transport='sse', host='127.0.0.1', port=8000)
#     mcp.run(transport='streamable-http')


import os
from mcp.server.fastmcp import FastMCP

# 在创建实例时指定 host 和 port
mcp = FastMCP("FileSystem", host="127.0.0.1", port=8001)

@mcp.tool()
def get_desktop_files() -> list:
    """获取当前用户的桌面文件列表"""
    return os.listdir(os.path.expanduser("~/Desktop"))

@mcp.tool()
def calculator(a: float, b: float, operator: str) -> float:
    if operator == '+':
        return a + b
    elif operator == '-':
        return a - b
    elif operator == '*':
        return a * b
    elif operator == '/':
        return a / b
    else:
        raise ValueError("无效运算符")

if __name__ == "__main__":
    # 只需要指定 transport，不再传递 host/port
    mcp.run(transport='sse')