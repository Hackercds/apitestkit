"""
APA自然语言接口

让大模型用自然语言描述测试意图，无需了解HTTP/JSON细节。
提供对话式交互、多轮上下文支持、结构化输出。

类比：Selenide的流畅API → APA的自然语言层
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json

from apitestkit.apa.core import APA, ExecutionResult, ResultStatus
from apitestkit.apa.session import APISession, RequestRecord
from apitestkit.apa.planner import TestPlanner


@dataclass
class NLResponse:
    """
    自然语言响应 — 大模型可解析的结构化输出

    区别于ExecutionResult：
    - 面向大模型，意图明确
    - 包含人类可读的summary
    - 包含下一步行动建议
    """
    content: str               # 人类可读的总结
    result: ExecutionResult    # 原始执行结果
    summary: str               # 一句话总结
    succeeded: bool            # 是否完全成功
    steps_summary: List[str]   # 每个步骤的简述
    suggestions: List[str]     # 下一步建议
    variables: Dict[str, Any]   # 当前会话中的变量
    raw: str                   # 原始JSON

    def __str__(self) -> str:
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "succeeded": self.succeeded,
            "summary": self.summary,
            "steps_summary": self.steps_summary,
            "suggestions": self.suggestions,
            "variables": self.variables,
            "raw": self.raw,
        }


class NLInterface:
    """
    自然语言接口

    大模型通过自然语言指令操作APA，无需了解底层实现。

    用法:
        nl = NLInterface()
        resp = nl.execute("帮我测试登录，用户名test，密码123456")
        print(resp.summary)
        print(resp.suggestions)
    """

    def __init__(self, session: Optional[APISession] = None, config: Optional[Dict] = None):
        self._apa = APA(config=config)
        self._session = session or APISession()
        self._planner = TestPlanner()
        self._last_response: Optional[NLResponse] = None

    def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> NLResponse:
        """
        执行自然语言指令

        Args:
            instruction: 自然语言指令
            context: 额外上下文

        Returns:
            NLResponse: 结构化响应
        """
        # 替换指令中的变量引用
        instruction = self._session.replace_variables(instruction)

        # 合并session变量到context
        merged_context = dict(context or {})
        for key, value in self._session.get_all_variables().items():
            if key not in merged_context:
                merged_context[key] = value

        # 执行
        result = self._apa.run(instruction, context=merged_context)

        # 构建NL响应
        nl_resp = self._build_nl_response(result)

        self._last_response = nl_resp
        return nl_resp

    def chat(self, message: str) -> NLResponse:
        """
        对话式交互（execute的别名，更符合Agent习惯）
        """
        return self.execute(message)

    def _build_nl_response(self, result: ExecutionResult) -> NLResponse:
        """将ExecutionResult转换为NLResponse"""

        # 步骤简述
        steps_summary = []
        for i, step in enumerate(result.steps):
            tool = step.get("tool", "")
            success = step.get("success", False)
            desc = step.get("description", "")
            status = "✓" if success else "✗"
            steps_summary.append(f"[{i+1}] {status} {tool}: {desc}")

        # 建议
        suggestions = self._generate_suggestions(result)

        # 变量
        variables = self._session.get_all_variables()

        content_lines = [
            f"**执行结果**: {'成功' if result.success else '失败'}",
            f"**消息**: {result.message}",
            "",
        ]

        if steps_summary:
            content_lines.append("**步骤详情**:")
            for s in steps_summary:
                content_lines.append(f"  {s}")
            content_lines.append("")

        if variables:
            var_lines = [f"  {k}: {v}" for k, v in list(variables.items())[:5]]
            content_lines.append(f"**当前变量** ({len(variables)}个):")
            content_lines.extend(var_lines)
            content_lines.append("")

        if suggestions:
            content_lines.append("**建议**:")
            for sug in suggestions:
                content_lines.append(f"  → {sug}")

        content = "\n".join(content_lines)

        return NLResponse(
            content=content,
            result=result,
            summary=result.message,
            succeeded=result.success,
            steps_summary=steps_summary,
            suggestions=suggestions,
            variables=variables,
            raw=result.to_json(),
        )

    def _generate_suggestions(self, result: ExecutionResult) -> List[str]:
        """根据执行结果生成下一步建议"""
        suggestions = []

        if not result.success:
            if result.error:
                suggestions.append(f"检查错误: {result.error}")
            suggestions.append("修正指令后重试")
            return suggestions

        # 成功后的建议
        if self._session.get_auth() is None:
            suggestions.append("建议设置认证: 使用 set_bearer_token 设置Token")

        history = self._session.get_history()
        if len(history) == 1:
            suggestions.append("可以用 extract 提取响应中的数据供后续使用")
        elif len(history) > 1:
            suggestions.append("测试流程已建立，可以继续执行下一步操作")

        return suggestions

    # ========== 便捷方法 ==========

    def login(self, url: str, username: str, password: str, token_path: str = "data.token") -> NLResponse:
        """快速登录"""
        instruction = f"登录 {url}，用户名{username}，密码{password}，提取token到{token_path}"
        return self.execute(instruction)

    def get(self, url: str, params: Optional[Dict] = None) -> NLResponse:
        """快速GET请求"""
        p = f", 参数{params}" if params else ""
        return self.execute(f"GET {url}{p}")

    def post(self, url: str, json_data: Dict) -> NLResponse:
        """快速POST请求"""
        return self.execute(f"POST {url}，请求体{json_data}")

    def set_base_url(self, url: str) -> NLResponse:
        """设置Base URL"""
        self._session.set_variable("base_url", url)
        self._apa.session.set_variable("base_url", url)
        return NLResponse(
            content=f"已设置 base_url = {url}",
            result=ExecutionResult(status=ResultStatus.SUCCESS, message=f"base_url已设置为{url}", steps=[]),
            summary=f"base_url = {url}",
            succeeded=True,
            steps_summary=[],
            suggestions=["可以使用相对路径的API了"],
            variables=self._session.get_all_variables(),
            raw="{}",
        )

    def set_token(self, token: str) -> NLResponse:
        """设置Bearer Token"""
        self._session.set_auth("Bearer", token)
        self._apa.session.set_auth("Bearer", token)
        return NLResponse(
            content="已设置Bearer Token",
            result=ExecutionResult(status=ResultStatus.SUCCESS, message="Token已设置", steps=[]),
            summary="Token已设置",
            succeeded=True,
            steps_summary=[],
            suggestions=["可以使用需要认证的接口了"],
            variables=self._session.get_all_variables(),
            raw="{}",
        )

    def get_variables(self) -> Dict[str, Any]:
        """获取当前会话变量"""
        return self._session.get_all_variables()

    def get_history(self) -> List[Dict]:
        """获取请求历史"""
        return [r.to_dict() for r in self._session.get_history()]

    def reset(self):
        """重置会话"""
        self._session.clear()
        self._apa.reset()


# ========== CLI入口 ==========

def main():
    """命令行演示"""
    nl = NLInterface()

    print("=== APA 自然语言接口演示 ===\n")

    # 示例1: 设置基础URL
    resp = nl.set_base_url("https://jsonplaceholder.typicode.com")
    print(resp.content)

    # 示例2: GET请求
    resp = nl.execute("获取用户ID为1的信息")
    print(resp.content)

    # 示例3: 登录场景（需要真实API）
    resp = nl.execute("POST /posts，创建一篇新文章，标题是测试标题，内容是测试内容")
    print(resp.content)

    print("\n=== 变量状态 ===")
    print(nl.get_variables())

    print("\n=== 请求历史 ===")
    for r in nl.get_history():
        print(f"  {r['method']} {r['url']} → {r['status_code']}")


if __name__ == "__main__":
    main()
