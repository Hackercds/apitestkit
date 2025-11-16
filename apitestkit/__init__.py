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
from apitestkit.report import (
    ReportGenerator, ChartsGenerator,
    generate_html_report, generate_pdf_report,
    generate_json_report, generate_csv_report,
    generate_excel_report
)

__all__ = [
    # 核心组件
    'ApiAdapter', 'api',
    
    # 装饰器
    'api_test', 'http_get', 'http_post', 'http_put', 'http_delete',
    'assert_response', 'extract_variables', 'quick_assert', 'quick_test',
    
    # 核心管理器
    'logger_manager', 'config_manager',
    
    # 日志工具
    'get_user_logger', 'get_framework_logger',
    
    # 报告生成
    'ReportGenerator', 'ChartsGenerator',
    'generate_html_report', 'generate_pdf_report',
    'generate_json_report', 'generate_csv_report',
    'generate_excel_report'
]