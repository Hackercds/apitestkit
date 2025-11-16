"""
API适配器测试

验证API适配器模块的基本功能
"""

import unittest
from unittest.mock import patch, MagicMock
from apitestkit.adapter.api_adapter import ApiAdapter, api


class TestApiAdapter(unittest.TestCase):
    """
    测试API适配器的功能
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        # 创建一个API适配器实例用于测试
        self.api = ApiAdapter()
    
    def test_api_factory_function(self):
        """
        测试api工厂函数是否正确创建ApiAdapter实例
        """
        api_instance = api()
        self.assertIsInstance(api_instance, ApiAdapter)
    
    def test_set_base_url(self):
        """
        测试设置基础URL功能
        """
        base_url = "https://api.example.com"
        self.api.set_base_url(base_url)
        self.assertEqual(self.api.base_url, base_url)
        
        # 测试链式调用
        result = self.api.set_base_url("https://test.com")
        self.assertEqual(result, self.api)
    
    def test_set_headers(self):
        """
        测试设置请求头功能
        """
        headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
        self.api.set_headers(headers)
        self.assertEqual(self.api.headers, headers)
        
        # 测试链式调用
        result = self.api.set_headers({"X-Custom": "Value"})
        self.assertEqual(result, self.api)
    
    @patch('apitestkit.adapter.api_adapter.requests.request')
    def test_send_request(self, mock_request):
        """
        测试发送请求功能（模拟requests库）
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_request.return_value = mock_response
        
        # 发送GET请求
        response = self.api.set_base_url("https://api.example.com").get("/test")
        
        # 验证请求是否正确发送
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs['method'], 'GET')
        self.assertEqual(kwargs['url'], 'https://api.example.com/test')
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
    
    @patch('apitestkit.adapter.api_adapter.requests.request')
    def test_assert_response(self, mock_request):
        """
        测试响应断言功能
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": 1, "name": "test"}}
        mock_request.return_value = mock_response
        
        # 测试断言状态码
        with self.assertRaises(AssertionError):
            # 故意设置错误的状态码以测试断言失败
            self.api.set_base_url("https://api.example.com").get("/test").assert_status_code(404)
        
        # 正确的状态码断言应该通过
        response = self.api.get("/test")
        response.assert_status_code(200)  # 这不会抛出异常
    
    @patch('apitestkit.adapter.api_adapter.requests.request')
    def test_extract_variables(self, mock_request):
        """
        测试变量提取功能
        """
        # 配置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "user_id": 123,
                "user_name": "testuser"
            }
        }
        mock_request.return_value = mock_response
        
        # 提取变量
        response = self.api.set_base_url("https://api.example.com").get("/test")
        variables = response.extract_variables([
            ("user_id", "data.user_id"),
            ("user_name", "data.user_name")
        ])
        
        # 验证变量是否正确提取
        self.assertEqual(variables["user_id"], 123)
        self.assertEqual(variables["user_name"], "testuser")
    
    def test_set_timeout(self):
        """
        测试设置超时功能
        """
        timeout = 30
        self.api.set_timeout(timeout)
        self.assertEqual(self.api.timeout, timeout)
        
        # 测试链式调用
        result = self.api.set_timeout(60)
        self.assertEqual(result, self.api)
    
    def test_set_params(self):
        """
        测试设置查询参数功能
        """
        params = {"page": 1, "limit": 10}
        self.api.set_params(params)
        self.assertEqual(self.api.params, params)
        
        # 测试链式调用
        result = self.api.set_params({"sort": "desc"})
        self.assertEqual(result, self.api)


if __name__ == '__main__':
    unittest.main()