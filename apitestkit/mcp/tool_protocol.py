"""
MCP工具协议层 - Agent/MCP集成接口

提供标准化的工具调用接口，供Agent使用。
所有工具返回统一的响应格式，便于Agent理解和处理。
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json


class ToolStatus(Enum):
    """工具执行状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # 部分成功（如断言部分失败）


@dataclass
class ToolResponse:
    """
    标准化工具响应格式
    
    所有MCP工具必须返回此格式，确保Agent能够统一处理。
    """
    success: bool                          # 是否完全成功
    status: str                            # SUCCESS/FAILURE/PARTIAL
    tool_name: str                         # 调用的工具名
    message: str                           # 人类可读的消息
    data: Optional[Dict[str, Any]] = None  # 工具返回的数据
    error: Optional[str] = None            # 错误信息（如果失败）
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolResponse':
        return cls(**data)


def mcp_tool(name: str, description: str = "", category: str = "general"):
    """
    MCP工具装饰器 - 用于注册工具函数
    
    用法:
        @mcp_tool(name="http_get", description="发送GET请求", category="http")
        def http_get_tool(url: str, **kwargs) -> ToolResponse:
            ...
    """
    def decorator(func: Callable) -> Callable:
        func._mcp_tool_meta = {
            "name": name,
            "description": description,
            "category": category,
        }
        return func
    return decorator


class MCPToolProtocol:
    """
    MCP工具协议处理器
    
    负责：
    1. 注册和管理所有可用工具
    2. 统一工具调用入口
    3. 标准化响应格式
    4. 工具发现和文档生成
    """
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._categories: Dict[str, List[str]] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具（不在此处导入ApiAdapter，延迟到工具执行时导入）"""
        # HTTP工具
        self.register(self._create_http_get_tool())
        self.register(self._create_http_post_tool())
        self.register(self._create_http_put_tool())
        self.register(self._create_http_delete_tool())

        # 断言工具
        self.register(self._create_assertion_tool())

        # 配置工具（每个工具单独创建）
        self.register(self._create_config_get_tool())
        self.register(self._create_config_set_tool())

        # 数据存储工具
        self.register(self._create_data_save_tool())
        self.register(self._create_data_get_tool())
    
    def register(self, tool: Callable):
        """注册工具"""
        meta = getattr(tool, '_mcp_tool_meta', None)
        if meta:
            tool_name = meta['name']
            category = meta['category']
            self._tools[tool_name] = tool
            if category not in self._categories:
                self._categories[category] = []
            if tool_name not in self._categories[category]:
                self._categories[category].append(tool_name)
    
    def call(self, tool_name: str, **kwargs) -> ToolResponse:
        """
        调用工具 - 统一入口
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            ToolResponse: 标准化响应
        """
        if tool_name not in self._tools:
            return ToolResponse(
                success=False,
                status=ToolStatus.FAILURE.value,
                tool_name=tool_name,
                message=f"未知工具: {tool_name}",
                error=f"可用工具: {list(self._tools.keys())}"
            )
        
        tool = self._tools[tool_name]
        try:
            result = tool(**kwargs)
            if isinstance(result, ToolResponse):
                return result
            # 如果返回的不是ToolResponse，包装它
            return ToolResponse(
                success=True,
                status=ToolStatus.SUCCESS.value,
                tool_name=tool_name,
                message="执行成功",
                data={"result": result}
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                status=ToolStatus.FAILURE.value,
                tool_name=tool_name,
                message=f"工具执行失败: {str(e)}",
                error=str(e)
            )
    
    def list_tools(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        列出可用工具
        
        Args:
            category: 可选，按分类过滤
            
        Returns:
            工具列表和分类信息
        """
        if category:
            tool_names = self._categories.get(category, [])
            tools = {name: self._tools[name] for name in tool_names}
        else:
            tools = self._tools
        
        result = {}
        for name, tool in tools.items():
            meta = getattr(tool, '_mcp_tool_meta', {})
            result[name] = {
                "name": name,
                "description": meta.get('description', ''),
                "category": meta.get('category', 'general'),
            }
        return result
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的完整schema描述（用于Agent工具调用）"""
        if tool_name not in self._tools:
            return None
        tool = self._tools[tool_name]
        meta = getattr(tool, '_mcp_tool_meta', {})
        # TODO: 未来可以通过inspect签名自动生成schema
        return {
            "name": tool_name,
            "description": meta.get('description', ''),
            "category": meta.get('category', 'general'),
        }
    
    # ========== 内置工具实现 ==========
    
    def _create_http_get_tool(self):
        """创建HTTP GET工具"""
        @mcp_tool(name="http_get", description="发送HTTP GET请求", category="http")
        def http_get_tool(
            url: str,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = 30,
            **kwargs
        ) -> ToolResponse:
            try:
                from apitestkit import ApiAdapter
                adapter = ApiAdapter()
                if params:
                    adapter.params(params)
                if headers:
                    adapter.headers(headers)
                adapter.get(url)
                adapter.send()
                response = adapter.get_response()
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="http_get",
                    message="GET请求成功",
                    data={
                        "status_code": response.status_code,
                        "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                        "headers": dict(response.headers),
                    }
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="http_get",
                    message=f"GET请求失败: {str(e)}",
                    error=str(e)
                )
        return http_get_tool
    
    def _create_http_post_tool(self):
        """创建HTTP POST工具"""
        @mcp_tool(name="http_post", description="发送HTTP POST请求", category="http")
        def http_post_tool(
            url: str,
            json_data: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = 30,
            **kwargs
        ) -> ToolResponse:
            try:
                from apitestkit import ApiAdapter
                adapter = ApiAdapter()
                if json_data:
                    adapter.json(json_data)
                if data:
                    adapter.body(data)
                if headers:
                    adapter.headers(headers)
                adapter.post(url)
                adapter.send()
                response = adapter.get_response()
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="http_post",
                    message="POST请求成功",
                    data={
                        "status_code": response.status_code,
                        "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                        "headers": dict(response.headers),
                    }
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="http_post",
                    message=f"POST请求失败: {str(e)}",
                    error=str(e)
                )
        return http_post_tool
    
    def _create_http_put_tool(self):
        """创建HTTP PUT工具"""
        @mcp_tool(name="http_put", description="发送HTTP PUT请求", category="http")
        def http_put_tool(
            url: str,
            json_data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = 30,
            **kwargs
        ) -> ToolResponse:
            try:
                from apitestkit import ApiAdapter
                adapter = ApiAdapter()
                if json_data:
                    adapter.json(json_data)
                if headers:
                    adapter.headers(headers)
                adapter.put(url)
                adapter.send()
                response = adapter.get_response()
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="http_put",
                    message="PUT请求成功",
                    data={
                        "status_code": response.status_code,
                        "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                        "headers": dict(response.headers),
                    }
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="http_put",
                    message=f"PUT请求失败: {str(e)}",
                    error=str(e)
                )
        return http_put_tool
    
    def _create_http_delete_tool(self):
        """创建HTTP DELETE工具"""
        @mcp_tool(name="http_delete", description="发送HTTP DELETE请求", category="http")
        def http_delete_tool(
            url: str,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = 30,
            **kwargs
        ) -> ToolResponse:
            try:
                from apitestkit import ApiAdapter
                adapter = ApiAdapter()
                if headers:
                    adapter.headers(headers)
                adapter.delete(url)
                adapter.send()
                response = adapter.get_response()
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="http_delete",
                    message="DELETE请求成功",
                    data={
                        "status_code": response.status_code,
                        "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                        "headers": dict(response.headers),
                    }
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="http_delete",
                    message=f"DELETE请求失败: {str(e)}",
                    error=str(e)
                )
        return http_delete_tool
    
    def _create_assertion_tool(self):
        """创建断言工具"""
        @mcp_tool(name="assert", description="执行断言验证", category="assertion")
        def assert_tool(
            actual: Any,
            expected: Any,
            assertion_type: str = "equals",
            message: Optional[str] = None,
            **kwargs
        ) -> ToolResponse:
            """
            执行断言

            Args:
                actual: 实际值
                expected: 期望值
                assertion_type: 断言类型 (equals/not_equals/contains/startswith/endswith/greater/less/is_none/is_not_none)
                message: 自定义消息
            """
            try:
                # 直接进行断言比较（不依赖ResponseAssertion，因为它是针对响应的）
                if assertion_type == "equals":
                    assert actual == expected, message or f"{actual} == {expected}"
                elif assertion_type == "not_equals":
                    assert actual != expected, message or f"{actual} != {expected}"
                elif assertion_type == "contains":
                    assert str(expected) in str(actual), message or f"'{expected}' in '{actual}'"
                elif assertion_type == "startswith":
                    assert str(actual).startswith(str(expected)), message or f"'{actual}' starts with '{expected}'"
                elif assertion_type == "endswith":
                    assert str(actual).endswith(str(expected)), message or f"'{actual}' ends with '{expected}'"
                elif assertion_type == "greater":
                    assert actual > expected, message or f"{actual} > {expected}"
                elif assertion_type == "less":
                    assert actual < expected, message or f"{actual} < {expected}"
                elif assertion_type == "is_none":
                    assert actual is None, message or f"{actual} is None"
                elif assertion_type == "is_not_none":
                    assert actual is not None, message or f"{actual} is not None"
                else:
                    return ToolResponse(
                        success=False,
                        status=ToolStatus.FAILURE.value,
                        tool_name="assert",
                        message=f"未知断言类型: {assertion_type}",
                        error=f"支持的类型: equals, not_equals, contains, startswith, endswith, greater, less, is_none, is_not_none"
                    )

                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="assert",
                    message=f"断言成功: {assertion_type}",
                    data={
                        "assertion_type": assertion_type,
                        "actual": actual,
                        "expected": expected,
                    }
                )
            except AssertionError as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="assert",
                    message=f"断言失败: {str(e)}",
                    error=str(e),
                    data={
                        "assertion_type": assertion_type,
                        "actual": actual,
                        "expected": expected,
                    }
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="assert",
                    message=f"断言执行异常: {str(e)}",
                    error=str(e),
                    data={
                        "assertion_type": assertion_type,
                        "actual": actual,
                        "expected": expected,
                    }
                )
        return assert_tool
    
    def _create_config_get_tool(self):
        """创建配置获取工具"""
        @mcp_tool(name="config_get", description="获取配置值", category="config")
        def config_get_tool(key: str, default: Any = None, **kwargs) -> ToolResponse:
            try:
                from apitestkit.core.config import config_manager
                value = config_manager.get(key, default)
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="config_get",
                    message=f"获取配置: {key}",
                    data={"key": key, "value": value}
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="config_get",
                    message=f"获取配置失败: {str(e)}",
                    error=str(e)
                )
        return config_get_tool

    def _create_config_set_tool(self):
        """创建配置设置工具"""
        @mcp_tool(name="config_set", description="设置配置值", category="config")
        def config_set_tool(key: str, value: Any, **kwargs) -> ToolResponse:
            try:
                from apitestkit.core.config import config_manager
                config_manager.set(key, value)
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="config_set",
                    message=f"设置配置: {key} = {value}",
                    data={"key": key, "value": value}
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="config_set",
                    message=f"设置配置失败: {str(e)}",
                    error=str(e)
                )
        return config_set_tool

    def _create_data_save_tool(self):
        """创建数据保存工具"""
        @mcp_tool(name="data_save", description="保存数据到存储（内存）", category="data")
        def data_save_tool(key: str, value: Any, scope: str = "test", **kwargs) -> ToolResponse:
            try:
                _mcp_data_store[key] = value
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="data_save",
                    message=f"数据已保存: {key}",
                    data={"key": key, "scope": scope}
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="data_save",
                    message=f"保存数据失败: {str(e)}",
                    error=str(e)
                )
        return data_save_tool

    def _create_data_get_tool(self):
        """创建数据获取工具"""
        @mcp_tool(name="data_get", description="从存储获取数据（内存）", category="data")
        def data_get_tool(key: str, scope: str = "test", default: Any = None, **kwargs) -> ToolResponse:
            try:
                value = _mcp_data_store.get(key, default)
                return ToolResponse(
                    success=True,
                    status=ToolStatus.SUCCESS.value,
                    tool_name="data_get",
                    message=f"获取数据: {key}",
                    data={"key": key, "value": value, "scope": scope}
                )
            except Exception as e:
                return ToolResponse(
                    success=False,
                    status=ToolStatus.FAILURE.value,
                    tool_name="data_get",
                    message=f"获取数据失败: {str(e)}",
                    error=str(e)
                )
        return data_get_tool


# MCP全局内存存储（供data_save/data_get工具使用）
_mcp_data_store: Dict[str, Any] = {}

# 全局单例
_mcp_protocol = None


def get_mcp_protocol() -> MCPToolProtocol:
    """获取MCP协议处理器单例"""
    global _mcp_protocol
    if _mcp_protocol is None:
        _mcp_protocol = MCPToolProtocol()
    return _mcp_protocol


def list_mcp_tools(category: Optional[str] = None) -> Dict[str, Any]:
    """列出所有MCP工具（便捷函数）"""
    return get_mcp_protocol().list_tools(category)


def call_mcp_tool(tool_name: str, **kwargs) -> ToolResponse:
    """调用MCP工具（便捷函数）"""
    return get_mcp_protocol().call(tool_name, **kwargs)