"""
测试规划器 - 将自然语言指令拆解为可执行步骤

类比 Selenium IDE 的录制 → 回放，但这里是：
自然语言描述 → 结构化测试步骤 → 执行
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import re


@dataclass
class Step:
    """
    单个测试步骤

    Attributes:
        tool: 工具名 (如 http_get, assert_eq, extract_json)
        params: 工具参数字典
        description: 人类可读的步骤描述
        critical: 是否关键步骤（失败是否中断测试）
        retry: 重试次数
        timeout: 超时秒数
    """
    tool: str
    params: Dict[str, Any]
    description: str = ""
    critical: bool = True
    retry: int = 0
    timeout: Optional[int] = None
    # 内部字段
    _raw: Optional[Dict[str, Any]] = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "params": self.params,
            "description": self.description,
            "critical": self.critical,
            "retry": self.retry,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Step':
        return cls(
            tool=d.get("tool", ""),
            params=d.get("params", {}),
            description=d.get("description", ""),
            critical=d.get("critical", True),
            retry=d.get("retry", 0),
            timeout=d.get("timeout"),
            _raw=d,
        )


class TestPlanner:
    """
    测试规划器

    将自然语言指令解析为结构化测试步骤。
    支持：
    - 关键词匹配（登录、注册、获取、创建）
    - 参数提取（用户名、密码、URL）
    - 多步骤场景识别
    - CRUD模式识别

    用法:
        planner = TestPlanner()
        steps = planner.plan("测试登录接口，用户名test，密码123456")
        for step in steps:
            print(step.tool, step.params)
    """

    # HTTP方法关键词映射
    METHOD_PATTERNS = {
        "get": ["获取", "查询", "get", "fetch", "retrieve", "读取"],
        "post": ["创建", "新增", "post", "add", "create", "注册", "登录", "提交"],
        "put": ["更新", "修改", "put", "update", "编辑"],
        "delete": ["删除", "delete", "remove"],
        "patch": ["部分更新", "patch"],
    }

    # 工具路由
    TOOL_ROUTES = {
        "http_get": "http_get",
        "http_post": "http_post",
        "http_put": "http_put",
        "http_delete": "http_delete",
        "assert_eq": "assert",
        "assert_status": "assert",
        "assert_contains": "assert",
    }

    def __init__(self):
        self._custom_intent_handlers: Dict[str, callable] = {}

    def register_intent(self, pattern: str, handler: callable):
        """
        注册自定义意图处理器

        handler signature: (text: str, context: Dict) -> List[Step]
        """
        self._custom_intent_handlers[pattern] = handler

    def plan(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> List[Step]:
        """
        将自然语言指令规划为步骤列表

        Args:
            instruction: 自然语言指令
            context: 上下文信息（已提取的变量等）

        Returns:
            List[Step]: 步骤列表
        """
        context = context or {}
        instruction = instruction.strip()

        # 1. 尝试自定义意图处理器
        for pattern, handler in self._custom_intent_handlers.items():
            if pattern in instruction.lower():
                steps = handler(instruction, context)
                if steps:
                    return steps

        # 2. 内置意图识别
        steps = self._parse_instruction(instruction, context)
        if steps:
            return steps

        # 3. 兜底：通用HTTP请求
        return self._generic_fallback(instruction, context)

    def _parse_instruction(self, text: str, context: Dict[str, Any]) -> List[Step]:
        """解析指令"""
        text_lower = text.lower()

        # === 登录场景 ===
        if any(k in text_lower for k in ["登录", "login", "登陆", "sign in"]):
            return self._plan_login(text, context)

        # === 注册场景 ===
        if any(k in text_lower for k in ["注册", "register", "signup", "新增用户"]):
            return self._plan_register(text, context)

        # === CRUD操作 ===
        crud = self._plan_crud(text, context)
        if crud:
            return crud

        # === 多步骤场景 ===
        if "然后" in text or "接下来" in text or "之后" in text:
            return self._plan_multi_step(text, context)

        return []

    def _plan_login(self, text: str, context: Dict[str, Any]) -> List[Step]:
        """规划登录场景"""
        steps = []

        # 提取用户名
        username = self._extract_param(text, ["用户名", "user", "username", "账号"], r"用户名[：:]\s*(\S+)")
        if not username:
            username = context.get("username", "{{username}}")

        # 提取密码
        password = self._extract_param(text, ["密码", "password", "pwd"], r"密码[：:]\s*(\S+)")
        if not password:
            password = context.get("password", "{{password}}")

        # 提取URL
        url = self._extract_url(text) or context.get("login_url", "{{base_url}}/api/login")

        steps.append(Step(
            tool="http_post",
            params={
                "url": url,
                "json_data": {"username": username, "password": password},
            },
            description=f"POST {url} - 登录",
            critical=True,
        ))

        # 登录后提取token
        steps.append(Step(
            tool="assert",
            params={
                "assertion_type": "equals",
                "actual": "{{status_code}}",
                "expected": "200",
            },
            description="验证登录状态码",
            critical=True,
        ))

        steps.append(Step(
            tool="extract",
            params={
                "source": "response",
                "json_path": "data.token",
                "variable_name": "token",
            },
            description="提取登录Token",
            critical=False,
        ))

        return steps

    def _plan_register(self, text: str, context: Dict[str, Any]) -> List[Step]:
        """规划注册场景"""
        steps = []

        username = self._extract_param(text, ["用户名", "user", "username"], r"用户名[：:]\s*(\S+)")
        password = self._extract_param(text, ["密码", "password"], r"密码[：:]\s*(\S+)")
        email = self._extract_param(text, ["邮箱", "email"], r"邮箱[：:]\s*(\S+)")

        url = self._extract_url(text) or context.get("register_url", "{{base_url}}/api/register")

        json_body = {}
        if username:
            json_body["username"] = username
        if password:
            json_body["password"] = password
        if email:
            json_body["email"] = email

        steps.append(Step(
            tool="http_post",
            params={"url": url, "json_data": json_body},
            description=f"POST {url} - 注册",
            critical=True,
        ))

        return steps

    def _plan_crud(self, text: str, context: Dict[str, Any]) -> Optional[List[Step]]:
        """规划CRUD操作"""
        text_lower = text.lower()
        method = None

        for m, keywords in self.METHOD_PATTERNS.items():
            if any(k in text_lower for k in keywords):
                method = m
                break

        if not method:
            return None

        # 提取URL
        url = self._extract_url(text)
        if not url:
            url = context.get("base_url", "{{base_url}}")
            # 从文本中提取路径
            path_match = re.search(r"(?:/|/api/)[\w/]+", text)
            if path_match:
                url = url.rstrip("/") + path_match.group()

        # 提取请求体
        json_data = self._extract_json_body(text)

        step = Step(
            tool=f"http_{method}",
            params={"url": url},
            description=f"{method.upper()} {url}",
            critical=True,
        )

        if json_data:
            step.params["json_data"] = json_data

        return [step]

    def _plan_multi_step(self, text: str, context: Dict[str, Any]) -> List[Step]:
        """规划多步骤场景"""
        # 按连接词拆分
        separators = ["然后", "接下来", "之后", "再", "并", "再然后"]
        parts = [text]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts

        all_steps = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            sub_steps = self._parse_instruction(part, context)
            all_steps.extend(sub_steps)

        return all_steps

    def _generic_fallback(self, text: str, context: Dict[str, Any]) -> List[Step]:
        """兜底：通用HTTP请求"""
        url = self._extract_url(text)
        if not url:
            url = "{{base_url}}" + (re.search(r"(/[\w/]+)", text) or re.search(r"(api/[\w/]+)", text) or "")

        method = "get"
        for m, keywords in self.METHOD_PATTERNS.items():
            if any(k in text.lower() for k in keywords):
                method = m
                break

        json_data = self._extract_json_body(text)

        params = {"url": url}
        if json_data:
            params["json_data"] = json_data

        return [Step(tool=f"http_{method}", params=params, description=text, critical=True)]

    # ========== 辅助方法 ==========

    def _extract_param(self, text: str, keywords: List[str], regex: str = None) -> Optional[str]:
        """从文本中提取参数"""
        # 先尝试正则
        if regex:
            match = re.search(regex, text)
            if match:
                return match.group(1)

        # 关键词匹配
        for kw in keywords:
            pattern = rf"{kw}[：:]\s*(\S+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_url(self, text: str) -> Optional[str]:
        """从文本中提取URL"""
        # URL正则
        url_match = re.search(r"https?://[^\s]+", text)
        if url_match:
            return url_match.group()

        # 相对路径
        path_match = re.search(r"(?:base_url[：:]?\s*)?{{base_url}}([^\s,，]+)", text)
        if path_match:
            return "{{base_url}}" + path_match.group(1)

        return None

    def _extract_json_body(self, text: str) -> Optional[Dict[str, Any]]:
        """尝试从文本中提取JSON结构"""
        # 匹配 {"key": "value"} 格式
        json_match = re.search(r"\{[^{}]*\"[^\"]+\"[^\"]*\}", text)
        if json_match:
            import json
            try:
                return json.loads(json_match.group())
            except:
                pass

        # 键值对提取 (key: value 或 key=value)
        kv_pattern = r"(\w+)[：:]\s*([^\s,，]+)"
        matches = re.findall(kv_pattern, text)
        if matches:
            # 排除常见非JSON字段
            excluded = {"用户名", "密码", "密码", "邮箱", "手机", "url", "地址"}
            return {k: v for k, v in matches if k not in excluded}

        return None
