"""
API适配器模块

提供核心的API测试功能，包括链式调用的ApiAdapter类和多种测试装饰器。
"""

from apitestkit.adapter.api_adapter import ApiAdapter, api
from apitestkit.adapter.api_decorators import (
    api_test, http_get, http_post, http_put, http_delete,
    assert_response, extract_variables, quick_assert, quick_test
)

__all__ = [
    'ApiAdapter', 'api',
    'api_test', 'http_get', 'http_post', 'http_put', 'http_delete',
    'assert_response', 'extract_variables', 'quick_assert', 'quick_test'
]