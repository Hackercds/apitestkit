"""
日志系统测试

验证日志管理模块的基本功能和配置，特别是用户日志和框架日志的区分功能
"""

import os
import unittest
from unittest.mock import patch
from apitestkit.core.logger import logger_manager, create_user_logger
from apitestkit.core.config import config_manager


class TestLoggerManager(unittest.TestCase):
    """
    测试日志管理器的功能
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        # 保存原始配置
        self.original_log_level = config_manager.get('log_level')
        self.original_log_dir = config_manager.get('log_dir')
        
        # 设置测试配置
        config_manager.set('log_level', 'DEBUG')
        # 使用临时日志目录
        self.test_log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
        config_manager.set('log_dir', self.test_log_dir)
        
        # 清除现有的日志记录器
        logger_manager._loggers.clear()
        logger_manager._user_loggers.clear()
        
        # 创建测试日志目录
        os.makedirs(self.test_log_dir, exist_ok=True)
    
    def tearDown(self):
        """
        测试后的清理工作
        """
        # 恢复原始配置
        config_manager.set('log_level', self.original_log_level)
        config_manager.set('log_dir', self.original_log_dir)
        
        # 清除测试中创建的日志记录器
        logger_manager._loggers.clear()
        logger_manager._user_loggers.clear()
        
        # 清理测试日志文件
        if os.path.exists(self.test_log_dir):
            for file in os.listdir(self.test_log_dir):
                os.remove(os.path.join(self.test_log_dir, file))
            os.rmdir(self.test_log_dir)
    
    def test_log_level_setting(self):
        """
        测试日志级别的设置功能
        """
        # 测试设置不同的日志级别
        logger_manager.set_level('DEBUG')
        logger = logger_manager._get_logger('apitestkit')
        self.assertEqual(logger.level, 10)  # 10 对应 DEBUG
        
        logger_manager.set_level('INFO')
        logger = logger_manager._get_logger('apitestkit')
        self.assertEqual(logger.level, 20)  # 20 对应 INFO
        
        logger_manager.set_level('WARNING')
        logger = logger_manager._get_logger('apitestkit')
        self.assertEqual(logger.level, 30)  # 30 对应 WARNING
        
        logger_manager.set_level('ERROR')
        logger = logger_manager._get_logger('apitestkit')
        self.assertEqual(logger.level, 40)  # 40 对应 ERROR
    
    def test_log_methods(self):
        """
        测试各种日志方法是否正常工作
        """
        # 设置为最低级别，确保所有日志都能输出
        logger_manager.set_level('DEBUG')
        
        # 测试各种日志级别
        logger_manager.debug('这是一条调试日志')
        logger_manager.info('这是一条信息日志')
        logger_manager.warning('这是一条警告日志')
        logger_manager.error('这是一条错误日志')
        logger_manager.critical('这是一条严重错误日志')
        
        # 验证日志记录器存在
        self.assertIn('apitestkit', logger_manager._loggers)
    
    def test_user_logger_creation(self):
        """
        测试用户日志记录器创建
        """
        # 创建用户日志记录器
        user_logger = logger_manager.get_user_logger('test_user_log')
        
        # 验证用户日志记录器存在
        self.assertIn('test_user_log', logger_manager._user_loggers)
        self.assertEqual(user_logger.name, 'user.test_user_log')
        
        # 使用便捷函数创建
        user_logger2 = create_user_logger('another_test')
        self.assertEqual(user_logger2.name, 'user.another_test')
        self.assertIn('another_test', logger_manager._user_loggers)
    
    def test_request_logging(self):
        """
        测试请求日志的记录功能
        """
        logger_manager.set_level('INFO')
        
        # 记录请求日志
        headers = {'Authorization': 'Bearer token123', 'Content-Type': 'application/json'}
        params = {'page': 1, 'limit': 10}
        json_data = {'username': 'test', 'password': 'secret123'}
        
        logger_manager.log_request('GET', 'https://api.example.com/users', 
                                 headers=headers, params=params, json_data=json_data)
        
        # 记录响应日志
        logger_manager.log_response(200, 150.5, '{"success": true}')
        
        # 验证请求响应日志记录器存在
        self.assertIn('apitestkit.request', logger_manager._loggers)
        self.assertIn('apitestkit.response', logger_manager._loggers)
    
    def test_log_file_creation(self):
        """
        测试日志文件是否正确创建
        """
        logger_manager.set_level('INFO')
        
        # 写入一些日志
        logger_manager.info('测试日志文件创建')
        
        # 检查日志文件是否存在
        log_files = [f for f in os.listdir(self.test_log_dir) if f.endswith('.log')]
        self.assertTrue(len(log_files) > 0, "日志文件应该已创建")
    
    def test_sensitive_data_filtering(self):
        """
        测试敏感数据过滤
        """
        # 创建包含敏感数据的请求
        headers = {'Authorization': 'Bearer secret_token', 'Cookie': 'session=abc123'}
        json_data = {
            'user': {
                'username': 'testuser',
                'password': 'secret_password',
                'api_key': '123456789'
            },
            'settings': {
                'auth_token': 'auth123',
                'normal_data': 'safe'
            }
        }
        
        # 使用mock避免实际写入文件
        with patch('logging.Logger.debug') as mock_debug:
            logger_manager.log_request('POST', 'https://api.example.com/login',
                                     headers=headers, json_data=json_data)
            
            # 验证是否记录了日志，且敏感信息被过滤
            calls = [call for call in mock_debug.call_args_list]
            sensitive_data_logged = False
            
            for call in calls:
                msg = call[0][0]
                # 确保敏感信息没有被直接记录
                self.assertNotIn('secret_token', msg)
                self.assertNotIn('abc123', msg)
                self.assertNotIn('secret_password', msg)
                self.assertNotIn('123456789', msg)
                self.assertNotIn('auth123', msg)
                # 确认敏感信息被替换为***
                self.assertIn('***', msg)
                if '***' in msg:
                    sensitive_data_logged = True
            
            self.assertTrue(sensitive_data_logged, "应该记录了过滤后的敏感信息")
    
    def test_clear_user_loggers(self):
        """
        测试清理用户日志记录器
        """
        # 创建几个用户日志记录器
        logger_manager.get_user_logger('test1')
        logger_manager.get_user_logger('test2')
        
        # 验证创建成功
        self.assertEqual(len(logger_manager._user_loggers), 2)
        
        # 清理用户日志记录器
        logger_manager.clear_user_loggers()
        
        # 验证清理成功
        self.assertEqual(len(logger_manager._user_loggers), 0)
    
    def test_different_logger_instances(self):
        """
        测试不同名称的日志记录器是不同的实例
        """
        logger1 = logger_manager._get_logger('logger1')
        logger2 = logger_manager._get_logger('logger2')
        
        # 验证是不同的实例
        self.assertIsNot(logger1, logger2)
        
        # 验证都在日志记录器字典中
        self.assertIn('logger1', logger_manager._loggers)
        self.assertIn('logger2', logger_manager._loggers)
    
    def test_log_format(self):
        """
        测试日志格式是否符合预期
        """
        # 设置为最低级别
        logger_manager.set_level('DEBUG')
        
        # 记录一条日志
        test_message = '测试日志格式'
        logger_manager.info(test_message)
        
        # 读取最新的日志文件，验证日志格式
        log_files = sorted([os.path.join(self.test_log_dir, f) for f in os.listdir(self.test_log_dir) if f.endswith('.log')], 
                          key=os.path.getmtime, reverse=True)
        
        if log_files:
            with open(log_files[0], 'r', encoding='utf-8') as f:
                last_line = f.readlines()[-1]
                # 检查日志格式是否包含时间戳、日志级别和消息
                self.assertIn('INFO', last_line)
                self.assertIn(test_message, last_line)
    
    def test_user_logger_distinct_from_framework(self):
        """
        测试用户日志记录器与框架日志记录器是独立的
        """
        # 创建用户日志记录器
        user_logger = logger_manager.get_user_logger('distinct_test')
        
        # 获取框架日志记录器
        framework_logger = logger_manager._get_logger('apitestkit')
        
        # 验证是不同的实例
        self.assertIsNot(user_logger, framework_logger)
        
        # 验证名称不同
        self.assertNotEqual(user_logger.name, framework_logger.name)
        self.assertTrue(user_logger.name.startswith('user.'))
        self.assertFalse(framework_logger.name.startswith('user.'))
    
    def test_log_directory_creation(self):
        """
        测试日志目录创建
        """
        # 设置一个不存在的日志目录
        new_log_dir = os.path.join(os.path.dirname(__file__), 'new_test_logs')
        config_manager.set('log_dir', new_log_dir)
        
        # 清除日志记录器缓存
        logger_manager._loggers.clear()
        
        # 触发日志目录创建
        logger_manager.info("测试日志目录创建")
        
        # 验证目录是否创建
        self.assertTrue(os.path.exists(new_log_dir))
        
        # 清理
        if os.path.exists(new_log_dir):
            if os.listdir(new_log_dir):
                for file in os.listdir(new_log_dir):
                    os.remove(os.path.join(new_log_dir, file))
            os.rmdir(new_log_dir)


if __name__ == '__main__':
    unittest.main()