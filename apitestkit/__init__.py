"""
API测试工具包 (ApiTestKit)

一个轻量级、易用的API测试框架，提供链式调用、装饰器等多种测试方式，
支持请求发送、响应断言、变量提取等核心功能。
"""

__version__ = "1.0.0"
__author__ = "Hackercd"
__license__ = "MIT"

# 导出主要功能
from apitestkit.adapter.api_adapter import ApiAdapter, api
from apitestkit.adapter.api_decorators import (
    api_test, http_get, http_post, http_put, http_delete,
    assert_response, extract_variables, quick_assert, quick_test
)
from apitestkit.core.logger import logger_manager, get_user_logger, get_framework_logger
from apitestkit.core.config import config_manager
from apitestkit.core.data_storage import DataStorageManager, get_data_storage
from apitestkit.test.test_runner import TestRunner
from apitestkit.assertion.assertions import AssertionError as AssertionException
from apitestkit.report import (
    ReportGenerator, ChartsGenerator,
    generate_html_report, generate_pdf_report,
    generate_json_report, generate_csv_report,
    generate_excel_report
)

# MCP工具协议（Agent/MCP集成用）
try:
    from apitestkit.mcp.tool_protocol import MCPToolProtocol, mcp_tool
    _mcp_available = True
except ImportError:
    _mcp_available = False

__all__ = [
    # 核心组件
    'ApiAdapter', 'api',

    # 装饰器
    'api_test', 'http_get', 'http_post', 'http_put', 'http_delete',
    'assert_response', 'extract_variables', 'quick_assert', 'quick_test',

    # 核心管理器
    'logger_manager', 'config_manager',
    'DataStorageManager', 'get_data_storage',

    # 测试运行器
    'TestRunner',

    # 断言异常
    'AssertionException',

    # 日志工具
    'get_user_logger', 'get_framework_logger',

    # 报告生成
    'ReportGenerator', 'ChartsGenerator',
    'generate_html_report', 'generate_pdf_report',
    'generate_json_report', 'generate_csv_report',
    'generate_excel_report',

    # MCP工具协议
    'MCPToolProtocol', 'mcp_tool', '_mcp_available',
]