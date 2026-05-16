"""
APA会话管理器

管理API测试的上下文状态：变量、认证、请求历史、会话级别数据。
类比Selenide的Session概念，但针对API测试场景。
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class RequestRecord:
    """单次请求记录"""
    timestamp: str
    method: str
    url: str
    request_body: Any = None
    response_body: Any = None
    status_code: int = 0
    response_time_ms: float = 0.0
    variables_extracted: Dict[str, Any] = field(default_factory=dict)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "method": self.method,
            "url": self.url,
            "request_body": self.request_body,
            "response_body": self.response_body,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "variables_extracted": self.variables_extracted,
            "assertions": self.assertions,
            "error": self.error,
        }


class APISession:
    """
    API测试会话管理器

    负责：
    - 变量存储和替换 ({{variable}} 语法)
    - 认证状态管理 (Bearer Token / API Key / Cookie)
    - 请求历史记录
    - 会话级别的数据共享

    用法:
        session = APISession()
        session.set_variable("token", "abc123")
        session.set_auth("Bearer", token)
        session.get_variable("token")  # "abc123"
    """

    def __init__(self):
        self._variables: Dict[str, Any] = {}
        self._auth: Optional[Dict[str, str]] = None  # {"type": "Bearer", "token": "..."}
        self._history: List[RequestRecord] = []
        self._metadata: Dict[str, Any] = {}  # 自定义元数据
        self._lock = threading.RLock()

    # ========== 变量管理 ==========

    def set_variable(self, key: str, value: Any):
        """设置变量"""
        with self._lock:
            self._variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        with self._lock:
            return self._variables.get(key, default)

    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        with self._lock:
            return dict(self._variables)

    def replace_variables(self, text: str) -> str:
        """
        替换文本中的 {{variable}} 占位符

        "Bearer {{token}}" → "Bearer abc123"
        """
        if not isinstance(text, str):
            return text
        for key, value in self._variables.items():
            placeholder = "{{" + key + "}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))
        return text

    # ========== 认证管理 ==========

    def set_auth(self, auth_type: str, credentials: Any):
        """
        设置认证信息

        Args:
            auth_type: "Bearer" | "APIKey" | "Basic" | "Cookie"
            credentials: 根据类型不同而不同
                - Bearer: token字符串
                - APIKey: {"key": "X-API-KEY", "value": "..."}
                - Basic: {"username": "...", "password": "..."}
                - Cookie: {"name": "...", "value": "..."}
        """
        with self._lock:
            self._auth = {"type": auth_type, "credentials": credentials}

    def get_auth(self) -> Optional[Dict[str, Any]]:
        """获取当前认证信息"""
        with self._lock:
            return dict(self._auth) if self._auth else None

    def clear_auth(self):
        """清除认证信息"""
        with self._lock:
            self._auth = None

    def apply_auth_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """将认证信息应用到请求头"""
        headers = dict(headers)  # 复制
        auth = self.get_auth()
        if not auth:
            return headers

        auth_type = auth["type"]
        creds = auth["credentials"]

        if auth_type == "Bearer":
            headers["Authorization"] = f"Bearer {creds}"
        elif auth_type == "APIKey":
            headers[creds.get("key", "X-API-KEY")] = creds.get("value", "")
        elif auth_type == "Basic":
            import base64
            encoded = base64.b64encode(f"{creds['username']}:{creds['password']}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_type == "Cookie":
            headers["Cookie"] = f"{creds['name']}={creds['value']}"

        return headers

    # ========== 请求历史 ==========

    def add_request_record(self, record: RequestRecord):
        """添加请求记录"""
        with self._lock:
            self._history.append(record)

    def get_history(self) -> List[RequestRecord]:
        """获取请求历史"""
        with self._lock:
            return list(self._history)

    def get_last_request(self) -> Optional[RequestRecord]:
        """获取最后一次请求"""
        with self._lock:
            return self._history[-1] if self._history else None

    def get_history_by_method(self, method: str) -> List[RequestRecord]:
        """按方法过滤历史"""
        with self._lock:
            return [r for r in self._history if r.method.upper() == method.upper()]

    # ========== 元数据 ==========

    def set_metadata(self, key: str, value: Any):
        """设置会话元数据"""
        with self._lock:
            self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取会话元数据"""
        with self._lock:
            return self._metadata.get(key, default)

    # ========== 生命周期 ==========

    def clear(self):
        """清空会话（保留历史，可选）"""
        with self._lock:
            self._variables.clear()
            self._auth = None
            self._metadata.clear()
            # 保留历史记录

    def clear_all(self, include_history: bool = False):
        """完全清空会话"""
        with self._lock:
            self._variables.clear()
            self._auth = None
            self._metadata.clear()
            if include_history:
                self._history.clear()

    def snapshot(self) -> Dict[str, Any]:
        """获取会话快照"""
        with self._lock:
            return {
                "variables": dict(self._variables),
                "auth": dict(self._auth) if self._auth else None,
                "metadata": dict(self._metadata),
                "history_count": len(self._history),
            }

    def restore(self, snapshot: Dict[str, Any]):
        """恢复会话快照"""
        with self._lock:
            self._variables = snapshot.get("variables", {})
            self._auth = snapshot.get("auth")
            self._metadata = snapshot.get("metadata", {})
