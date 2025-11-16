"""
配置管理测试

验证配置管理模块的基本功能和配置
"""

import os
import unittest
import tempfile
import json
from apitestkit.core.config import config_manager


class TestConfig(unittest.TestCase):
    """
    测试配置管理器的功能
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        # 保存原始配置，以便测试后恢复
        self.original_config = config_manager._config.copy()
        
        # 创建临时配置文件用于测试
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        test_config = {
            "test_key": "test_value",
            "test_section": {
                "nested_key": "nested_value"
            }
        }
        self.temp_config_file.write(json.dumps(test_config).encode('utf-8'))
        self.temp_config_file.close()
    
    def tearDown(self):
        """
        测试后的清理工作
        """
        # 恢复原始配置
        config_manager._config = self.original_config
        
        # 删除临时配置文件
        if os.path.exists(self.temp_config_file.name):
            os.unlink(self.temp_config_file.name)
    
    def test_get_config(self):
        """
        测试获取配置的功能
        """
        # 测试获取现有配置
        log_dir = config_manager.get_config('log_dir')
        self.assertIsNotNone(log_dir)
        self.assertTrue(isinstance(log_dir, str))
        
        # 测试获取不存在的配置，应该返回None或默认值
        non_existent = config_manager.get_config('non_existent_key')
        self.assertIsNone(non_existent)
        
        # 测试获取带默认值的配置
        default_value = "default"
        result = config_manager.get_config('non_existent_key', default_value)
        self.assertEqual(result, default_value)
    
    def test_set_config(self):
        """
        测试设置配置的功能
        """
        # 测试设置新配置
        test_key = "test_config_key"
        test_value = "test_config_value"
        config_manager.set_config(test_key, test_value)
        self.assertEqual(config_manager.get_config(test_key), test_value)
        
        # 测试更新现有配置
        updated_value = "updated_value"
        config_manager.set_config(test_key, updated_value)
        self.assertEqual(config_manager.get_config(test_key), updated_value)
    
    def test_load_config_file(self):
        """
        测试从文件加载配置的功能
        """
        # 测试加载临时配置文件
        config_manager.load_config_file(self.temp_config_file.name)
        
        # 验证配置是否正确加载
        self.assertEqual(config_manager.get_config('test_key'), "test_value")
        # 测试嵌套配置
        nested_value = config_manager.get_config('test_section.nested_key')
        self.assertEqual(nested_value, "nested_value")
    
    def test_directory_creation(self):
        """
        测试目录自动创建功能
        """
        # 验证必要的目录是否存在
        config_dir = config_manager.get_config('config_dir')
        log_dir = config_manager.get_config('log_dir')
        report_dir = config_manager.get_config('report_dir')
        data_dir = config_manager.get_config('data_dir')
        
        self.assertTrue(os.path.exists(config_dir), f"配置目录 {config_dir} 应该存在")
        self.assertTrue(os.path.exists(log_dir), f"日志目录 {log_dir} 应该存在")
        self.assertTrue(os.path.exists(report_dir), f"报告目录 {report_dir} 应该存在")
        self.assertTrue(os.path.exists(data_dir), f"数据目录 {data_dir} 应该存在")
    
    def test_merge_configs(self):
        """
        测试合并配置的功能
        """
        # 测试合并新配置到现有配置中
        new_config = {
            "new_key": "new_value",
            "test_section": {
                "new_nested_key": "new_nested_value"
            }
        }
        config_manager.merge_config(new_config)
        
        # 验证新配置是否合并成功
        self.assertEqual(config_manager.get_config('new_key'), "new_value")
        # 验证嵌套配置是否正确合并
        self.assertEqual(config_manager.get_config('test_section.new_nested_key'), "new_nested_value")
    
    def test_input_output_dir_control(self):
        """
        测试输入输出目录控制功能
        """
        # 测试设置自定义输入输出目录
        custom_input_dir = os.path.join(tempfile.gettempdir(), 'custom_input')
        custom_output_dir = os.path.join(tempfile.gettempdir(), 'custom_output')
        
        config_manager.set_input_dir(custom_input_dir)
        config_manager.set_output_dir(custom_output_dir)
        
        # 验证目录是否正确设置并创建
        self.assertEqual(config_manager.get_config('input_dir'), custom_input_dir)
        self.assertEqual(config_manager.get_config('output_dir'), custom_output_dir)
        self.assertTrue(os.path.exists(custom_input_dir))
        self.assertTrue(os.path.exists(custom_output_dir))
        
        # 清理测试创建的目录
        if os.path.exists(custom_input_dir):
            os.rmdir(custom_input_dir)
        if os.path.exists(custom_output_dir):
            os.rmdir(custom_output_dir)


if __name__ == '__main__':
    unittest.main()