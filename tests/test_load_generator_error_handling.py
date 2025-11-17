#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
负载生成器错误处理功能测试

此测试文件专门验证apitestkit框架中LoadGenerator类的错误处理功能，包括：
1. 错误类型分类测试
2. 错误统计更新测试
3. 错误阈值检查测试
4. 连续错误计数测试
5. 错误重试机制测试
"""

import unittest
import time
import socket
from unittest.mock import patch, MagicMock, mock_open
from apitestkit.performance.load_generator import LoadGenerator
from apitestkit.performance.metrics_collector import MetricsCollector


class TestLoadGeneratorErrorHandling(unittest.TestCase):
    """测试LoadGenerator类的错误处理功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            "method": "GET",
            "url": "https://httpbin.org/get",
            "headers": {},
            "params": {},
            "timeout": 30,
            "max_retries": 3,
            "error_threshold": 10,
            "error_rate_threshold": 0.3,
            "consecutive_error_threshold": 5,
            "stop_on_error": True
        }
        self.metrics_collector = MetricsCollector()
    
    def test_classify_error_type(self):
        """测试错误类型分类功能"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        
        # 测试超时错误分类
        import socket
        timeout_error = socket.timeout("Connection timed out")
        error_type = generator._classify_error_type(timeout_error)
        self.assertEqual(error_type, "timeout")
        
        # 测试连接错误分类
        connection_error = ConnectionError("Connection refused")
        error_type = generator._classify_error_type(connection_error)
        self.assertEqual(error_type, "connection_error")
        
        # 测试HTTP错误分类
        class HTTPError(Exception):
            def __init__(self):
                pass
        http_error = HTTPError()
        error_type = generator._classify_error_type(http_error)
        self.assertEqual(error_type, "http_error")
        
        # 测试其他错误分类
        other_error = ValueError("Invalid value")
        error_type = generator._classify_error_type(other_error)
        self.assertEqual(error_type, "other_error")
    
    @patch('apitestkit.performance.load_generator.logger')
    def test_record_error(self, mock_logger):
        """测试错误记录功能"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        
        # 记录不同类型的错误
        generator._record_error("timeout", "Connection timed out")
        generator._record_error("connection_error", "Connection refused")
        generator._record_error("http_error", "HTTP 500 Error")
        
        # 验证错误统计更新
        self.assertEqual(generator._error_stats["timeout"], 1)
        self.assertEqual(generator._error_stats["connection_error"], 1)
        self.assertEqual(generator._error_stats["http_error"], 1)
        self.assertEqual(generator._total_errors, 3)
        self.assertEqual(generator._consecutive_errors, 3)
        
        # 测试连续错误重置
        generator._consecutive_errors = 0  # 模拟成功请求后的重置
        generator._record_error("other_error", "Unknown error")
        self.assertEqual(generator._consecutive_errors, 1)
    
    def test_check_error_threshold(self):
        """测试错误阈值检查功能"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        
        # 设置模拟数据
        generator._total_requests = 100
        generator._total_errors = 0
        generator._consecutive_errors = 0
        
        # 测试未达到阈值的情况
        should_stop = generator._check_error_threshold()
        self.assertFalse(should_stop)
        
        # 测试达到总错误数阈值
        generator._total_errors = 15  # 超过error_threshold=10
        should_stop = generator._check_error_threshold()
        self.assertTrue(should_stop)
        
        # 测试达到错误率阈值
        generator._total_errors = 0
        generator._total_requests = 10
        generator._total_errors = 5  # 50% 错误率，超过30%阈值
        should_stop = generator._check_error_threshold()
        self.assertTrue(should_stop)
        
        # 测试达到连续错误阈值
        generator._total_errors = 0
        generator._consecutive_errors = 6  # 超过consecutive_error_threshold=5
        should_stop = generator._check_error_threshold()
        self.assertTrue(should_stop)
    
    @patch('apitestkit.performance.load_generator.time.sleep')
    @patch('apitestkit.performance.load_generator.requests.request')
    def test_execute_with_retry_success(self, mock_request, mock_sleep):
        """测试成功重试场景"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        
        # 设置模拟响应，第一次失败，第二次成功
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"success": true}'
        mock_response_success.elapsed.total_seconds.return_value = 0.1
        
        # 模拟请求方法：第一次抛出超时错误，第二次返回成功响应
        mock_request.side_effect = [
            socket.timeout("Connection timed out"),
            mock_response_success
        ]
        
        # 执行带重试的任务
        result = generator._execute_with_retry("GET", "https://httpbin.org/get")
        
        # 验证重试被触发且最终成功
        self.assertEqual(mock_request.call_count, 2)
        self.assertTrue(mock_sleep.called)  # 验证重试延迟
        self.assertIsNotNone(result)
    
    @patch('apitestkit.performance.load_generator.time.sleep')
    @patch('apitestkit.performance.load_generator.requests.request')
    def test_execute_with_retry_failure(self, mock_request, mock_sleep):
        """测试重试失败场景"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        
        # 模拟请求方法：始终抛出超时错误
        mock_request.side_effect = socket.timeout("Connection timed out")
        
        # 执行带重试的任务
        result = generator._execute_with_retry("GET", "https://httpbin.org/get")
        
        # 验证达到最大重试次数
        self.assertEqual(mock_request.call_count, 4)  # 1次原始请求 + 3次重试
        self.assertEqual(mock_sleep.call_count, 3)  # 验证重试延迟被调用
        self.assertIsNone(result)  # 最终失败返回None
    
    @patch('apitestkit.performance.load_generator.requests.request')
    def test_execute_with_non_retryable_error(self, mock_request):
        """测试不可重试错误场景"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        # 配置只有timeout错误可重试
        generator._retry_config['retryable_errors'] = ['timeout']
        
        # 模拟请求方法：抛出ValueError（不可重试的错误类型）
        mock_request.side_effect = ValueError("Invalid request")
        
        # 执行带重试的任务
        result = generator._execute_with_retry("GET", "https://httpbin.org/get")
        
        # 验证没有进行重试
        self.assertEqual(mock_request.call_count, 1)
        self.assertIsNone(result)  # 失败返回None
    
    def test_error_statistics_reset(self):
        """测试错误统计重置功能"""
        generator = LoadGenerator(self.config, self.metrics_collector)
        
        # 记录一些错误
        generator._record_error("timeout", "Connection timed out")
        generator._record_error("connection_error", "Connection refused")
        
        # 模拟重置错误统计
        generator._total_errors = 0
        generator._consecutive_errors = 0
        for error_type in generator._error_stats:
            generator._error_stats[error_type] = 0
        
        # 验证重置成功
        self.assertEqual(generator._total_errors, 0)
        self.assertEqual(generator._consecutive_errors, 0)
        self.assertEqual(sum(generator._error_stats.values()), 0)


if __name__ == '__main__':
    unittest.main()