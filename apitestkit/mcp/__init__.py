"""
MCP工具协议包 - Agent/MCP集成接口

提供标准化的工具调用接口，供Agent或MCP服务器使用。
"""

from apitestkit.mcp.tool_protocol import (
    MCPToolProtocol,
    ToolResponse,
    ToolStatus,
    mcp_tool,
    get_mcp_protocol,
    list_mcp_tools,
    call_mcp_tool,
)

__all__ = [
    'MCPToolProtocol',
    'ToolResponse',
    'ToolStatus',
    'mcp_tool',
    'get_mcp_protocol',
    'list_mcp_tools',
    'call_mcp_tool',
]