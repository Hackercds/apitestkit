"""
APA - ApiTestKit Agent
高层Agent封装，让大模型用自然语言驱动API测试。

类比 Selenium (底层驱动) → Selenide/Appium (高层API) → Playwright (高级封装)
                    apitestkit (底层驱动) → APA (高层Agent封装)

核心设计理念：
1. 大模型不需要知道HTTP协议、状态码、JSON结构
2. 用自然语言描述测试意图，APA自动拆解执行
3. Session级上下文管理，支持多轮对话
4. 自动异常恢复和重试策略
5. 结构化输出，大模型可解析结果
"""

from apitestkit.apa.session import APISession
from apitestkit.apa.planner import TestPlanner
from apitestkit.apa.core import APA
from apitestkit.apa.nl import NLInterface
from apitestkit.apa.tools import register_tool, list_apa_tools

__version__ = "2.0.0"
__all__ = ['APISession', 'TestPlanner', 'APA', 'NLInterface', 'register_tool', 'list_apa_tools', '__version__']
