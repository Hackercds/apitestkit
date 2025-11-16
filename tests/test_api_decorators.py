"""
API装饰器测试

验证API装饰器模块的基本功能
"""

import unittest
from unittest.mock import patch, MagicMock
from apitestkit.adapter.api_decorators import (
    api_test, http_get, http_post, http_put, http_delete,
    assert_response, extract_variables, TestResult
)


class TestApiDecorators(unittest.TestCase):
    """
    测试API装饰器的功能
    """
    
    def test_test_result_class(self):
        """
        测试TestResult类的基本功能
        """
        result = TestResult()
        result.add_success("test_case", "测试成功")
        result.add_failure("failed_case", "测试失败")
        
        self.assertEqual(len(result.successes), 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)
        
        # 测试格式化输出
        output = result.format_summary()
        self.assertIn("测试结果汇总", output)
        self.assertIn("成功: 1", output)
        self.assertIn("失败: 1", output)
    
    @patch('apitestkit.adapter.api_decorators._make_http_request')
    def test_api_test_decorator(self, mock_request):
        """
        测试api_test装饰器
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"success": true}'
        mock_request.return_value = mock_response
        
        # 使用装饰器定义测试函数
        @api_test("测试API")
        def test_func():
            pass
        
        # 执行测试函数
        result = test_func()
        
        # 验证结果
        self.assertIsInstance(result, TestResult)
        self.assertEqual(result.success_count, 1)
    
    @patch('apitestkit.adapter.api_decorators._make_http_request')
    def test_http_get_decorator(self, mock_request):
        """
        测试http_get装饰器
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        # 使用装饰器定义测试函数
        @http_get("https://api.example.com/test")
        def test_get():
            pass
        
        # 执行测试函数
        result = test_get()
        
        # 验证请求是否正确发送
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['method'], 'GET')
        self.assertEqual(kwargs['url'], 'https://api.example.com/test')
        
        # 验证结果
        self.assertIsInstance(result, TestResult)
    
    @patch('apitestkit.adapter.api_decorators._make_http_request')
    def test_http_post_decorator(self, mock_request):
        """
        测试http_post装饰器
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        
        # 使用装饰器定义测试函数
        @http_post("https://api.example.com/test", json={"key": "value"})
        def test_post():
            pass
        
        # 执行测试函数
        result = test_post()
        
        # 验证请求是否正确发送
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['method'], 'POST')
        self.assertEqual(kwargs['json'], {"key": "value"})
    
    @patch('apitestkit.adapter.api_decorators._make_http_request')
    def test_assert_response_decorator(self, mock_request):
        """
        测试assert_response装饰器
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'
        mock_request.return_value = mock_response
        
        # 使用装饰器定义测试函数
        @http_get("https://api.example.com/test")
        @assert_response(status_code=200)
        def test_with_assert():
            pass
        
        # 执行测试函数，应该成功
        result = test_with_assert()
        self.assertEqual(result.success_count, 1)
        
        # 测试失败的情况
        @http_get("https://api.example.com/test")
        @assert_response(status_code=404)
        def test_with_assert_failure():
            pass
        
        result = test_with_assert_failure()
        self.assertEqual(result.failure_count, 1)
    
    @patch('apitestkit.adapter.api_decorators._make_http_request')
    def test_extract_variables_decorator(self, mock_request):
        """
        测试extract_variables装饰器
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user": {
                "id": 123,
                "name": "testuser"
            }
        }
        mock_request.return_value = mock_response
        
        # 使用装饰器定义测试函数
        extracted_vars = {}
        
        @http_get("https://api.example.com/test")
        @extract_variables(variables=[("user_id", "user.id"), ("user_name", "user.name")], result_dict=extracted_vars)
        def test_extract():
            pass
        
        # 执行测试函数
        result = test_extract()
        
        # 验证变量是否正确提取
        self.assertEqual(extracted_vars["user_id"], 123)
        self.assertEqual(extracted_vars["user_name"], "testuser")
    
    @patch('apitestkit.adapter.api_decorators._make_http_request')
    def test_quick_test_function(self, mock_request):
        """
        测试快捷测试函数
        """
        from apitestkit.adapter.api_decorators import quick_test
        
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # 执行快捷测试
        result = quick_test(
            method="GET",
            url="https://api.example.com/test",
            assertions=[{"status_code": 200}]
        )
        
        # 验证结果
        self.assertIsInstance(result, TestResult)
        self.assertEqual(result.success_count, 1)


if __name__ == '__main__':
    unittest.main()