"""
APA工具注册中心

提供工具注册、执行、发现功能。
每个工具都有标准化接口，大模型可发现和调用。
"""

from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from apitestkit.mcp import ToolResponse, ToolStatus


@dataclass
class ApaTool:
    """
    APA工具定义

    Attributes:
        name: 工具唯一名称
        description: 人类可读的描述（给大模型看）
        parameters: 参数schema描述
        execute: 执行函数
        category: 工具分类 (http/assert/data/config/auth)
        examples: 用法示例
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    execute: Callable[..., ToolResponse]
    category: str = "general"
    examples: list = field(default_factory=list)

    def to_schema(self) -> Dict[str, Any]:
        """生成大模型工具调用schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "examples": self.examples,
        }


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, ApaTool] = {}

    def register(self, tool: ApaTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ApaTool]:
        return self._tools.get(name)

    def list_all(self) -> Dict[str, Dict[str, Any]]:
        return {name: tool.to_schema() for name, tool in self._tools.items()}

    def list_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        return {
            name: tool.to_schema()
            for name, tool in self._tools.items()
            if tool.category == category
        }

    @property
    def tools(self) -> Dict[str, ApaTool]:
        return self._tools


# 全局工具注册表
_registry = ToolRegistry()


def apa_tools() -> ToolRegistry:
    """获取工具注册表（懒加载，模块导入时触发注册）"""
    return _registry


def register_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    category: str = "general",
    examples: list = None,
):
    """
    装饰器：注册APA工具

    用法:
        @register_tool(
            name="my_tool",
            description="做某事",
            parameters={"arg1": {"type": "string", "required": True}},
            category="custom"
        )
        def my_tool_impl(**kwargs) -> ToolResponse:
            ...
    """
    def decorator(func: Callable) -> Callable:
        tool = ApaTool(
            name=name,
            description=description,
            parameters=parameters,
            execute=func,
            category=category,
            examples=examples or [],
        )
        _registry.register(tool)
        return func
    return decorator


def list_apa_tools(category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """列出所有APA工具"""
    if category:
        return _registry.list_by_category(category)
    return _registry.list_all()


def get_apa_tool(name: str) -> Optional[ApaTool]:
    """获取指定工具"""
    return _registry.get(name)


# ========== 内置APA工具 ==========

def _init_builtin_tools():
    """初始化内置APA工具"""

    # ---- HTTP 工具 ----

    @register_tool(
        name="http_get",
        description="发送HTTP GET请求，用于查询/获取数据",
        parameters={
            "url": {"type": "string", "required": True, "description": "请求URL"},
            "params": {"type": "object", "required": False, "description": "URL查询参数"},
            "headers": {"type": "object", "required": False, "description": "自定义请求头"},
            "timeout": {"type": "integer", "required": False, "default": 30, "description": "超时秒数"},
        },
        category="http",
        examples=["http_get(url='{{base_url}}/users/1')", "http_get(url='/users', params={'page': 1})"]
    )
    def http_get(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        return call_mcp_tool("http_get", **kwargs)

    @register_tool(
        name="http_post",
        description="发送HTTP POST请求，用于创建资源、登录、提交表单等",
        parameters={
            "url": {"type": "string", "required": True, "description": "请求URL"},
            "json_data": {"type": "object", "required": False, "description": "JSON请求体"},
            "data": {"type": "object", "required": False, "description": "表单数据"},
            "headers": {"type": "object", "required": False, "description": "自定义请求头"},
            "timeout": {"type": "integer", "required": False, "default": 30},
        },
        category="http",
        examples=["http_post(url='/login', json_data={'username': 'test', 'password': '123'})"]
    )
    def http_post(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        return call_mcp_tool("http_post", **kwargs)

    @register_tool(
        name="http_put",
        description="发送HTTP PUT请求，用于完整更新资源",
        parameters={
            "url": {"type": "string", "required": True},
            "json_data": {"type": "object", "required": False},
            "headers": {"type": "object", "required": False},
            "timeout": {"type": "integer", "required": False, "default": 30},
        },
        category="http",
    )
    def http_put(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        return call_mcp_tool("http_put", **kwargs)

    @register_tool(
        name="http_delete",
        description="发送HTTP DELETE请求，用于删除资源",
        parameters={
            "url": {"type": "string", "required": True},
            "headers": {"type": "object", "required": False},
            "timeout": {"type": "integer", "required": False, "default": 30},
        },
        category="http",
    )
    def http_delete(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        return call_mcp_tool("http_delete", **kwargs)

    # ---- 断言工具 ----

    @register_tool(
        name="assert_eq",
        description="断言两个值相等",
        parameters={
            "actual": {"type": "any", "required": True, "description": "实际值"},
            "expected": {"type": "any", "required": True, "description": "期望值"},
            "message": {"type": "string", "required": False, "description": "自定义失败消息"},
        },
        category="assert",
        examples=["assert_eq(actual=200, expected=200)", "assert_eq(actual='{{status_code}}', expected=200)"]
    )
    def assert_eq(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        # 从session中解析变量
        actual = kwargs.get("actual")
        expected = kwargs.get("expected")
        # 变量替换在调用层处理
        return call_mcp_tool("assert", assertion_type="equals", actual=actual, expected=expected, message=kwargs.get("message"))

    @register_tool(
        name="assert_status_code",
        description="断言HTTP响应状态码",
        parameters={
            "status_code": {"type": "integer", "required": True, "description": "期望的状态码"},
            "actual_code": {"type": "any", "required": False, "description": "实际状态码（从上次响应获取）"},
        },
        category="assert",
    )
    def assert_status_code(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        expected = kwargs.get("status_code")
        actual = kwargs.get("actual_code")
        if actual is None:
            actual = "{{status_code}}"  # 占位，由session解析
        return call_mcp_tool("assert", assertion_type="equals", actual=actual, expected=expected)

    # ---- 变量提取工具 ----

    @register_tool(
        name="extract",
        description="从上次HTTP响应中提取变量，存入session供后续使用",
        parameters={
            "json_path": {"type": "string", "required": True, "description": "JSON路径，如 data.token"},
            "variable_name": {"type": "string", "required": True, "description": "变量名"},
        },
        category="data",
        examples=["extract(json_path='data.token', variable_name='token')", "extract(json_path='data.user.id', variable_name='user_id')"]
    )
    def extract(**kwargs) -> ToolResponse:
        from apitestkit.mcp import ToolResponse, ToolStatus
        json_path = kwargs.get("json_path", "")
        variable_name = kwargs.get("variable_name", "")

        if not json_path or not variable_name:
            return ToolResponse(
                success=False,
                status=ToolStatus.FAILURE.value,
                tool_name="extract",
                message="json_path和variable_name都是必需的",
                error="参数不足"
            )

        # 从session获取上次响应
        last_response = None
        session = kwargs.get("_session")
        if session:
            record = session.get_last_request()
            if record and record.response_body:
                last_response = record.response_body

        if not last_response:
            return ToolResponse(
                success=False,
                status=ToolStatus.FAILURE.value,
                tool_name="extract",
                message="没有可用的响应数据，请先执行HTTP请求",
                error="no_response"
            )

        # 解析JSONPath
        value = _resolve_json_path(last_response, json_path)
        if value is None:
            return ToolResponse(
                success=False,
                status=ToolStatus.FAILURE.value,
                tool_name="extract",
                message=f"无法从响应中提取路径: {json_path}",
                error="json_path_not_found"
            )

        # 存入session
        if session:
            session.set_variable(variable_name, value)

        return ToolResponse(
            success=True,
            status=ToolStatus.SUCCESS.value,
            tool_name="extract",
            message=f"已提取 {json_path} → {variable_name}",
            data={"json_path": json_path, "variable_name": variable_name, "value": value}
        )

    # ---- 认证工具 ----

    @register_tool(
        name="set_bearer_token",
        description="设置Bearer Token认证，后续请求自动携带Authorization头",
        parameters={
            "token": {"type": "string", "required": True, "description": "Token值或 {{token}} 变量引用"},
        },
        category="auth",
        examples=["set_bearer_token(token='{{login_token}}')", "set_bearer_token(token='eyJhbGciOiJIUzI1NiJ9...')"]
    )
    def set_bearer_token(**kwargs) -> ToolResponse:
        from apitestkit.mcp import ToolResponse, ToolStatus
        token = kwargs.get("token", "")
        session = kwargs.get("_session")

        if session:
            session.set_auth("Bearer", token)
            return ToolResponse(
                success=True,
                status=ToolStatus.SUCCESS.value,
                tool_name="set_bearer_token",
                message=f"已设置Bearer Token",
                data={"auth_type": "Bearer"}
            )

        return ToolResponse(
            success=False,
            status=ToolStatus.FAILURE.value,
            tool_name="set_bearer_token",
            message="session未初始化",
            error="no_session"
        )

    # ---- 配置工具 ----

    @register_tool(
        name="config_set",
        description="设置框架配置",
        parameters={
            "key": {"type": "string", "required": True, "description": "配置键，支持点号分隔的嵌套键如 ai.temperature"},
            "value": {"type": "any", "required": True, "description": "配置值"},
        },
        category="config",
        examples=["config_set(key='base_url', value='https://api.example.com')", "config_set(key='ai.temperature', value=0.7)"]
    )
    def config_set(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        return call_mcp_tool("config_set", key=kwargs.get("key"), value=kwargs.get("value"))

    @register_tool(
        name="config_get",
        description="获取框架配置",
        parameters={
            "key": {"type": "string", "required": True, "description": "配置键"},
            "default": {"type": "any", "required": False, "description": "默认值"},
        },
        category="config",
    )
    def config_get(**kwargs) -> ToolResponse:
        from apitestkit.mcp import call_mcp_tool
        return call_mcp_tool("config_get", key=kwargs.get("key"), default=kwargs.get("default"))


# ========== 辅助函数 ==========

def _resolve_json_path(data: Any, path: str) -> Any:
    """
    简单JSONPath解析
    支持: data.token, data.items[0].name, data[0]
    """
    if not path or not data:
        return None

    parts = path.split(".")
    current = data

    for part in parts:
        if not part:
            continue

        # 数组索引
        if "[" in part and "]" in part:
            base, rest = part.split("[", 1)
            if rest.endswith("]"):
                rest = rest[:-1]

            if base:
                if isinstance(current, dict):
                    current = current.get(base, {})
                elif hasattr(current, base):
                    current = getattr(current, base)
                else:
                    return None

            # 解析索引
            if rest.isdigit():
                idx = int(rest)
                if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None

            # 处理嵌套
            if "[" in rest:
                inner = "[" + rest.split("]", 1)[1] if "]" in rest else ""
                if inner:
                    current = _resolve_json_path(current, inner.lstrip("."))
        else:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

        if current is None:
            return None

    return current


# 初始化内置工具
_init_builtin_tools()
