"""
测试模块

提供完整的测试用例管理系统，支持：
- 测试用例定义与执行
- 测试套件管理
- 高级测试运行器
- 工厂函数简化测试创建
"""

from .test_case import TestCase
from .test_suite import TestSuite, TestSuiteResult
from .test_runner import TestRunner, RunnerResult
from .factory import (
    create_test_case,
    create_test_suite,
    create_test_runner,
    create_api_test,
    load_tests_from_json,
    create_authorization_test,
    create_multi_api_test,
    create_async_test
)

__all__ = [
    # 核心类
    'TestCase',
    'TestSuite', 'TestSuiteResult',
    'TestRunner', 'RunnerResult',
    # 工厂函数
    'create_test_case',
    'create_test_suite',
    'create_test_runner',
    'create_api_test',
    'load_tests_from_json',
    'create_authorization_test',
    'create_multi_api_test',
    'create_async_test'
]