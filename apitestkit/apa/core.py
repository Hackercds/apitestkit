"""
APA核心引擎

提供面向大模型的统一接口，自动选择工具、规划路径、处理异常。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from apitestkit.apa.session import APISession
from apitestkit.apa.planner import TestPlanner, Step
from apitestkit.apa.tools import ToolRegistry, apa_tools
from apitestkit.mcp import ToolResponse


class ResultStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"      # 部分成功
    NEED_CLARIFICATION = "need_clarification"  # 需要人工确认


@dataclass
class ExecutionResult:
    """执行结果"""
    status: ResultStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    raw_llm_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data or {},
            "steps": self.steps,
            "error": self.error,
            "raw_llm_response": self.raw_llm_response,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @property
    def success(self) -> bool:
        return self.status == ResultStatus.SUCCESS


class APA:
    """
    ApiTestKit Agent (APA)

    顶层入口，大模型通过自然语言描述意图，APA自动：
    1. 解析意图 → 拆解成可执行步骤
    2. 路由到合适的工具
    3. 管理Session上下文（变量、认证状态）
    4. 汇总结果返回结构化响应

    用法:
        apa = APA()
        result = apa.run("帮我测试登录接口，用户名test，密码123456")
        print(result.to_json())
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session = APISession()
        self.planner = TestPlanner()
        self._tools = apa_tools().tools  # 共享工具注册表

    def run(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        核心入口：接收自然语言指令，执行并返回结构化结果

        Args:
            instruction: 自然语言指令，如 "测试登录接口"
            context: 额外上下文（如当前用户信息等）

        Returns:
            ExecutionResult: 结构化执行结果
        """
        context = context or {}

        try:
            # Step 1: 规划
            steps = self.planner.plan(instruction, context)
            if not steps:
                return ExecutionResult(
                    status=ResultStatus.NEED_CLARIFICATION,
                    message=f"无法理解指令: {instruction}",
                    error="指令不明确，请提供更具体的信息"
                )

            # Step 2: 执行每个步骤
            all_step_results = []
            for i, step in enumerate(steps):
                step_result = self._execute_step(step, context)
                all_step_results.append(step_result)

                # 如果步骤失败，根据策略决定是否继续
                if not step_result.get("success", False):
                    if step.critical:
                        return ExecutionResult(
                            status=ResultStatus.FAILURE,
                            message=f"步骤 [{i+1}] {step.description} 执行失败",
                            steps=all_step_results,
                            error=step_result.get("error", "未知错误")
                        )
                    # 非关键步骤失败，记录并继续
                    all_step_results.append(step_result)

            # Step 3: 汇总结果
            success_count = sum(1 for r in all_step_results if r.get("success", False))
            total_count = len(all_step_results)

            if success_count == total_count:
                status = ResultStatus.SUCCESS
            elif success_count > 0:
                status = ResultStatus.PARTIAL
            else:
                status = ResultStatus.FAILURE

            return ExecutionResult(
                status=status,
                message=f"执行完成: {success_count}/{total_count} 步骤成功",
                steps=all_step_results,
                data={"total": total_count, "succeeded": success_count}
            )

        except Exception as e:
            return ExecutionResult(
                status=ResultStatus.FAILURE,
                message=f"执行异常: {str(e)}",
                error=str(e)
            )

    def _execute_step(self, step: Step, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        tool_name = step.tool
        params = step.params.copy()
        description = step.description

        if not tool_name:
            return {"success": False, "error": "步骤缺少tool字段"}

        # 获取工具
        tool = self._tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"未知工具: {tool_name}"}

        try:
            # 替换参数中的变量占位符
            enriched_params = {}
            for k, v in params.items():
                if isinstance(v, str):
                    enriched_params[k] = self.session.replace_variables(v)
                else:
                    enriched_params[k] = v

            # 注入session上下文
            enriched_params["_session"] = self.session
            enriched_params["_context"] = context

            # 执行工具
            result = tool.execute(**enriched_params)

            # 提取变量到session
            if result.success and hasattr(result, 'data') and result.data:
                extracted = result.data.get("extracted_variables", {})
                for key, value in extracted.items():
                    self.session.set_variable(key, value)

                # 记录请求历史
                if "status_code" in result.data:
                    from apitestkit.apa.session import RequestRecord
                    record = RequestRecord(
                        timestamp=str(datetime.now()),
                        method=tool_name.upper().replace("HTTP_", ""),
                        url=enriched_params.get("url", ""),
                        response_body=result.data.get("body"),
                        status_code=result.data.get("status_code", 0),
                    )
                    self.session.add_request_record(record)

            return {
                "success": result.success,
                "tool": tool_name,
                "description": description,
                "message": result.message,
                "data": result.data,
                "error": result.error,
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "description": description,
                "error": str(e)
            }

    def execute_raw(self, tool_name: str, **kwargs) -> ToolResponse:
        """直接执行指定工具（不经过规划器）"""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResponse(
                success=False,
                status="failure",
                tool_name=tool_name,
                message=f"未知工具: {tool_name}",
                error=f"可用工具: {list(self._tools.keys())}"
            )
        kwargs["_session"] = self.session
        return tool.execute(**kwargs)

    def reset(self):
        """重置会话（清空变量、认证状态等）"""
        self.session.clear()

    def set_context(self, **kwargs):
        """设置会话上下文"""
        for key, value in kwargs.items():
            self.session.set_variable(key, value)

    def get_context(self) -> Dict[str, Any]:
        """获取当前会话上下文"""
        return self.session.get_all()
