"""
断言功能测试

验证断言模块的基本功能和增强功能
"""

import json
import unittest
from unittest.mock import MagicMock, patch
import pytest
from apitestkit.assertion.assertions import ResponseAssertion, AssertionError, AssertionResult


class TestResponseAssertion(unittest.TestCase):
    """
    测试响应断言功能
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        # 创建响应断言实例
        self.assertion = ResponseAssertion()
        
        # 创建模拟响应对象
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        # 添加响应时间属性（0.15秒）
        self.mock_response.response_time = 0.15
        self.mock_response.json.return_value = {
            "data": {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "roles": ["admin", "user"],
                "profile": {
                    "age": 30,
                    "active": True
                }
            },
            "metadata": {
                "total": 100,
                "page": 1
            }
        }
        self.mock_response.headers = {
            "Content-Type": "application/json",
            "X-Request-ID": "12345",
            "X-RateLimit-Limit": "100"
        }
        self.mock_response.text = '{"data":{"id":1,"name":"Test User"}}'
        self.mock_response.elapsed.total_seconds.return_value = 0.15
    
    def test_status_code_assertion(self):
        """
        测试状态码断言
        """
        # 测试成功情况
        result = self.assertion.assert_status_code(
            self.mock_response,
            200
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_status_code(
                self.mock_response,
                404
            )
    
    def test_status_code_comparators(self):
        """
        测试状态码比较器
        """
        # 测试大于
        result = self.assertion.assert_status_code(
            self.mock_response,
            199,
            comparator='gt'
        )
        self.assertTrue(result)
        
        # 测试小于
        result = self.assertion.assert_status_code(
            self.mock_response,
            201,
            comparator='lt'
        )
        self.assertTrue(result)
        
        # 测试不等于
        with self.assertRaises(AssertionError):
            self.assertion.assert_status_code(
                self.mock_response,
                200,
                comparator='neq'
            )
    
    def test_status_code_in_list_assertion(self):
        """
        测试状态码是否在列表中
        """
        # 测试成功情况
        result = self.assertion.assert_status_code_in(
            self.mock_response,
            [200, 201]
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_status_code_in(
                self.mock_response,
                [400, 404]
            )
    
    def test_status_code_not_in_list_assertion(self):
        """
        测试状态码不在列表中
        """
        # 测试成功情况
        result = self.assertion.assert_status_code_not_in(
            self.mock_response,
            [400, 404]
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_status_code_not_in(
                self.mock_response,
                [200, 201]
            )
    
    def test_json_path_assertion(self):
        """
        测试JSON路径断言
        """
        # 测试简单路径
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.id",
            1
        )
        self.assertTrue(result)
        
        # 测试嵌套路径
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.profile.active",
            True
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_json_path(
                self.mock_response,
                "data.id",
                999
            )
        
        # 测试不存在的路径
        with self.assertRaises(AssertionError):
            self.assertion.assert_json_path(
                self.mock_response,
                "nonexistent.path",
                "value"
            )
    
    def test_json_path_comparators(self):
        """
        测试JSON路径比较器
        """
        # 测试contains
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.name",
            "Test",
            comparator='contains'
        )
        self.assertTrue(result)
        
        # 测试matches
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.name",
            r'^Test\s+User$',
            comparator='matches'
        )
        self.assertTrue(result)
        
        # 测试gt
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.profile.age",
            25,
            comparator='gt'
        )
        self.assertTrue(result)
    
    def test_json_path_exists_assertion(self):
        """
        测试JSON路径是否存在
        """
        # 测试存在的路径
        result = self.assertion.assert_json_path_exists(
            self.mock_response,
            "data.name"
        )
        self.assertTrue(result)
        
        # 测试不存在的路径
        with self.assertRaises(AssertionError):
            self.assertion.assert_json_path_exists(
                self.mock_response,
                "nonexistent.path"
            )
    
    def test_json_path_not_exists_assertion(self):
        """
        测试JSON路径不存在
        """
        # 测试不存在的路径
        result = self.assertion.assert_json_path_not_exists(
            self.mock_response,
            "nonexistent.path"
        )
        self.assertTrue(result)
        
        # 测试存在的路径
        with self.assertRaises(AssertionError):
            self.assertion.assert_json_path_not_exists(
                self.mock_response,
                "data.name"
            )
    
    def test_json_path_array_access(self):
        """
        测试JSON路径数组访问
        """
        # 测试数组索引访问
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.roles.0",
            "admin"
        )
        self.assertTrue(result)
        
        # 测试另一种语法
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.roles[0]",
            "admin"
        )
        self.assertTrue(result)
    
    def test_json_path_wildcard(self):
        """
        测试JSON路径通配符
        """
        # 测试数组通配符
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.roles[*]",
            ["admin", "user"],
            comparator='eq'
        )
        self.assertTrue(result)
    
    def test_response_time_assertion(self):
        """
        测试响应时间断言
        """
        # 测试成功情况 (0.15 < 1)
        result = self.assertion.assert_response_time(
            self.mock_response,
            1.0  # 1秒
        )
        self.assertTrue(result)
        
        # 测试失败情况 (0.15 > 0.1)
        with self.assertRaises(AssertionError):
            self.assertion.assert_response_time(
                self.mock_response,
                0.1  # 0.1秒
            )
    
    def test_response_time_range(self):
        """
        测试响应时间范围断言
        """
        # 测试范围内
        result = self.assertion.assert_response_time_range(
            self.mock_response,
            0.1,
            0.2
        )
        self.assertTrue(result)
        
        # 测试边界值
        result = self.assertion.assert_response_time_range(
            self.mock_response,
            0.15,
            0.2
        )
        self.assertTrue(result)
        
        # 测试超出范围
        with self.assertRaises(AssertionError):
            self.assertion.assert_response_time_range(
                self.mock_response,
                0.0,
                0.1
            )
    
    def test_header_assertion(self):
        """
        测试响应头断言
        """
        # 测试存在的头
        result = self.assertion.assert_header_exists(
            self.mock_response,
            "Content-Type"
        )
        self.assertTrue(result)
        
        # 测试不存在的头
        with self.assertRaises(AssertionError):
            self.assertion.assert_header_exists(
                self.mock_response,
                "X-Nonexistent"
            )
        
        # 测试头不存在
        result = self.assertion.assert_header_not_exists(
            self.mock_response,
            "X-Nonexistent"
        )
        self.assertTrue(result)
        
        # 测试头值
        result = self.assertion.assert_header_value(
            self.mock_response,
            "Content-Type",
            "application/json"
        )
        self.assertTrue(result)
        
        # 测试头值失败
        with self.assertRaises(AssertionError):
            self.assertion.assert_header_value(
                self.mock_response,
                "Content-Type",
                "text/plain"
            )
        
        # 测试头值包含
        result = self.assertion.assert_header_contains(
            self.mock_response,
            "Content-Type",
            "json"
        )
        self.assertTrue(result)
    
    def test_content_contains_assertion(self):
        """
        测试响应内容包含字符串
        """
        # 测试成功情况
        result = self.assertion.assert_response_contains(
            self.mock_response,
            "Test User"
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_response_contains(
                self.mock_response,
                "Non-existent string"
            )
    
    def test_content_not_contains_assertion(self):
        """
        测试响应内容不包含字符串
        """
        # 测试成功情况
        result = self.assertion.assert_response_not_contains(
            self.mock_response,
            "Non-existent string"
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_response_not_contains(
                self.mock_response,
                "Test User"
            )
    
    def test_regex_match_assertion(self):
        """
        测试正则表达式匹配
        """
        # 测试成功情况
        result = self.assertion.assert_response_matches(
            self.mock_response,
            r"Test\s+User"
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_response_matches(
                self.mock_response,
                r"Admin\s+User"
            )
    
    def test_response_not_matches(self):
        """
        测试响应内容不匹配正则
        """
        # 测试成功情况
        result = self.assertion.assert_response_not_matches(
            self.mock_response,
            r"Admin\s+User"
        )
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.assertion.assert_response_not_matches(
                self.mock_response,
                r"Test\s+User"
            )
    
    def test_global_assertions_instance(self):
        """
        测试全局assertions实例
        """
        self.assertIsInstance(assertions, ResponseAssertion)
        
        # 测试使用全局实例
        result = assertions.assert_status_code(
            self.mock_response,
            200
        )
        self.assertTrue(result)
    
    def test_assertion_result_tracking(self):
        """
        测试断言结果跟踪
        """
        # 执行成功断言
        self.assertion.assert_status_code(self.mock_response, 200)
        self.assertFalse(self.assertion.has_failed_assertions())
        
        # 执行失败断言
        try:
            self.assertion.assert_status_code(self.mock_response, 400)
        except AssertionError:
            pass
        
        self.assertTrue(self.assertion.has_failed_assertions())
        self.assertEqual(len(self.assertion.get_failed_assertions()), 1)
        
        # 清除失败断言
        self.assertion.clear_failed_assertions()
        self.assertFalse(self.assertion.has_failed_assertions())
    
    def test_assert_all_passed(self):
        """
        测试所有断言通过
        """
        # 只有成功断言
        self.assertion.assert_status_code(self.mock_response, 200)
        result = self.assertion.assert_all_passed()
        self.assertTrue(result)
        
        # 有失败断言
        try:
            self.assertion.assert_status_code(self.mock_response, 400)
        except AssertionError:
            pass
        
        with self.assertRaises(AssertionError):
            self.assertion.assert_all_passed()
    
    def test_assert_custom(self):
        """
        测试自定义断言
        """
        # 成功断言
        result = self.assertion.assert_custom(1 == 1, "自定义断言测试")
        self.assertTrue(result)
        
        # 失败断言
        with self.assertRaises(AssertionError):
            self.assertion.assert_custom(1 == 2, "自定义断言失败")
    
    def test_assert_with_func(self):
        """
        测试使用自定义函数断言
        """
        def custom_func(a, b):
            return a == b
        
        # 成功断言
        result = self.assertion.assert_with_func(custom_func, 1, 1)
        self.assertTrue(result)
        
        # 失败断言
        with self.assertRaises(AssertionError):
            self.assertion.assert_with_func(custom_func, 1, 2)
    
    def test_json_schema_validation(self):
        """
        测试JSON Schema验证
        """
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    },
                    "required": ["id", "name"]
                }
            },
            "required": ["data"]
        }
        
        # 尝试导入jsonschema库
        try:
            import jsonschema
            result = self.assertion.assert_json_schema(
                self.mock_response,
                schema
            )
            self.assertTrue(result)
        except ImportError:
            self.skipTest("jsonschema库未安装")
    
    def test_stream_assertions(self):
        """
        测试流式响应断言
        """
        stream_data = '{"data":{"id":1,"name":"Test User"}}'
        
        # 测试包含
        result = self.assertion.assert_stream_contains(stream_data, "Test User")
        self.assertTrue(result)
        
        # 测试正则匹配
        result = self.assertion.assert_stream_matches(stream_data, r"Test\s+User")
        self.assertTrue(result)
        
        # 测试字节流
        stream_bytes = b'{"data":{"id":1,"name":"Test User"}}'
        result = self.assertion.assert_stream_contains(stream_bytes, "Test User")
        self.assertTrue(result)
    
    @pytest.mark.asyncio
    async def test_async_assertions(self):
        """
        测试异步断言
        """
        # 异步状态码断言
        result = await self.assertion.assert_status_code_async(
            self.mock_response,
            200
        )
        self.assertTrue(result)
        
        # 异步JSON路径断言
        result = await self.assertion.assert_json_path_async(
            self.mock_response,
            "data.id",
            1
        )
        self.assertTrue(result)
    
    def test_json_deep_equal(self):
        """
        测试JSON深度比较
        """
        # 创建只包含部分字段的预期数据
        expected_data = {
            "data": {
                "id": 1,
                "name": "Test User"
            }
        }
        
        # 部分匹配应该通过
        result = self.assertion.assert_json_deep_equal(
            self.mock_response,
            expected_data
        )
        self.assertTrue(result)
        
        # 完全匹配也应该通过
        result = self.assertion.assert_json_deep_equal(
            self.mock_response,
            self.mock_response.json()
        )
        self.assertTrue(result)
        
        # 不匹配的数据应该失败
        expected_data["data"]["id"] = 999
        with self.assertRaises(AssertionError):
            self.assertion.assert_json_deep_equal(
                self.mock_response,
                expected_data
            )
    
    def test_complex_json_path_assertion(self):
        """
        测试复杂JSON路径断言，如数组访问
        """
        # 测试数组元素
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.roles[0]",
            "admin"
        )
        self.assertTrue(result)
        
        result = self.assertion.assert_json_path(
            self.mock_response,
            "data.roles[1]",
            "user"
        )
        self.assertTrue(result)
    
    def test_json_path_length(self):
        """
        测试JSON路径值长度断言
        """
        # 测试数组长度
        result = self.assertion.assert_json_path_length(
            self.mock_response,
            "data.roles",
            2
        )
        self.assertTrue(result)
        
        # 测试字符串长度
        result = self.assertion.assert_json_path_length(
            self.mock_response,
            "data.name",
            9  # "Test User" 的长度
        )
        self.assertTrue(result)
        
        # 测试比较器
        result = self.assertion.assert_json_path_length(
            self.mock_response,
            "data.roles",
            1,
            comparator='gt'
        )
        self.assertTrue(result)
    
    def test_json_path_type(self):
        """
        测试JSON路径值类型断言
        """
        # 测试整数类型
        result = self.assertion.assert_json_path_type(
            self.mock_response,
            "data.id",
            "int"
        )
        self.assertTrue(result)
        
        # 测试字符串类型
        result = self.assertion.assert_json_path_type(
            self.mock_response,
            "data.name",
            str
        )
        self.assertTrue(result)
        
        # 测试布尔类型
        result = self.assertion.assert_json_path_type(
            self.mock_response,
            "data.profile.active",
            "bool"
        )
        self.assertTrue(result)
        
        # 测试列表类型
        result = self.assertion.assert_json_path_type(
            self.mock_response,
            "data.roles",
            list
        )
        self.assertTrue(result)
        
        # 测试对象类型
        result = self.assertion.assert_json_path_type(
            self.mock_response,
            "data",
            "dict"
        )
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()