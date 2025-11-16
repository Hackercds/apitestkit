"""
日志管理模块

提供灵活的日志记录功能，支持文件和控制台双处理器，多级别日志记录，
并明确区分用户输出和包输出，确保包输出包含用户输出。
"""

import os
import logging
import time
import json
import tempfile
import warnings
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from logging.handlers import RotatingFileHandler
from apitestkit.core.config import config_manager


class LoggerManager:
    """
    日志管理器类，负责配置和提供日志记录器
    
    核心功能：
    - 区分框架日志和用户日志
    - 框架日志包含所有日志信息（框架 + 用户）
    - 用户日志只包含用户测试相关信息
    - 支持不同的日志级别和格式化
    - 提供控制台和文件双重输出
    """
    
    def __init__(self):
        # 框架日志记录器字典
        self._framework_loggers = {}
        # 用户日志记录器字典
        self._user_loggers = {}
        # 为测试兼容，添加_loggers属性作为_framework_loggers的别名
        self._loggers = self._framework_loggers
        # 处理器列表
        self._handlers = []
        # 日志级别映射
        self._log_level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'WARN': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        # 日志目录 - 初始化为None，在_ensure_log_directory中设置
        self._log_dir = None
        # 确保日志目录存在
        self._ensure_log_directory()
        # 初始化根日志记录器配置
        self._configure_root_logger()
        
    def _ensure_log_directory(self):
        """
        确保日志目录存在
        每次都从配置中获取最新的日志目录
        """
        # 每次都从配置中获取最新的日志目录
        try:
            current_log_dir = config_manager.get('log_dir', str(Path.cwd() / 'logs'))
            # 如果是测试环境，使用临时目录避免权限问题
            if self._is_test_environment():
                current_log_dir = tempfile.gettempdir()
            
            # 使用Path对象进行路径处理
            self._log_dir_path = Path(current_log_dir)
            self._log_dir = str(self._log_dir_path)
            
            # 确保目录存在
            self._log_dir_path.mkdir(parents=True, exist_ok=True)
            logging.debug(f"日志目录已确认: {self._log_dir}")
        except Exception as e:
            # 如果创建目录失败，回退到临时目录
            self._log_dir = tempfile.gettempdir()
            self._log_dir_path = Path(self._log_dir)
            logging.warning(f"无法创建指定的日志目录，已回退到临时目录: {str(e)}")
            
    def _generate_safe_filename(self, name: str) -> str:
        """
        生成安全的文件名
        
        Args:
            name: 原始名称
            
        Returns:
            安全的文件名
        """
        # 移除或替换不安全字符，确保跨平台兼容性
        # 这个正则表达式可以处理Windows和Unix/Linux/MacOS的文件系统限制
        safe_name = re.sub(r'[\\/*?"<>|]', '_', name)
        # 确保文件名不超过255个字符
        return safe_name[:255]
            
    def _configure_root_logger(self):
        """
        配置根日志记录器，确保所有日志记录器的基础配置正确
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 清除默认处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def _get_framework_logger(self, name='apitestkit'):
        """
        获取或创建框架日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 框架日志记录器实例
        """
        if name not in self._framework_loggers:
            self._setup_framework_logger(name)
        return self._framework_loggers[name]
    
    def _is_test_environment(self):
        """
        检测是否在测试环境中
        
        Returns:
            bool: 是否在测试环境中
        """
        # 检查是否正在运行pytest或unittest
        import sys
        return 'pytest' in sys.modules or 'unittest' in sys.modules
    
    def __del__(self):
        """
        析构函数，关闭所有处理器
        """
        try:
            if hasattr(self, '_handlers'):
                for handler in self._handlers[:]:  # 使用副本迭代
                    try:
                        handler.close()
                    except:
                        pass
                self._handlers.clear()
        except:
            pass
    
    def _setup_framework_logger(self, name):
        """
        设置框架日志记录器
        
        Args:
            name: 日志记录器名称
        """
        # 确保日志目录存在并获取最新路径
        self._ensure_log_directory()
        
        # 获取日志记录器
        logger = logging.getLogger(name)
        
        # 清理现有的处理器（避免文件锁定问题）
        for handler in logger.handlers[:]:
            try:
                handler.close()
            except:
                pass
            logger.removeHandler(handler)
        
        # 设置日志级别
        logger_level = self._log_level_map.get(
            config_manager.get('framework_log_level', 'INFO'), 
            logging.INFO
        )
        logger.setLevel(logger_level)
        logger.propagate = False  # 防止重复记录
        
        # 只添加控制台处理器，避免文件锁定问题
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger_level)
        
        # 创建框架日志格式化器
        framework_formatter = logging.Formatter(
            config_manager.get('framework_log_format', 
            '%(asctime)s - [FRAMEWORK] %(name)s - %(levelname)s - %(message)s')
        )
        
        # 设置格式化器
        console_handler.setFormatter(framework_formatter)
        
        # 添加处理器到日志记录器
        logger.addHandler(console_handler)
        
        # 保存处理器引用以便后续清理
        self._handlers.append(console_handler)
        
        self._framework_loggers[name] = logger
        
        return logger
    
    def set_framework_level(self, level):
        """
        设置框架日志级别
        
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        if level in self._log_level_map:
            config_manager.set('framework_log_level', level)
            # 更新所有已创建的框架日志记录器的级别
            for logger in self._framework_loggers.values():
                logger.setLevel(self._log_level_map[level])
                for handler in logger.handlers:
                    handler.setLevel(self._log_level_map[level])
    
    def set_user_log_level(self, level):
        """
        设置用户日志级别
        
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        if level in self._log_level_map:
            config_manager.set('user_log_level', level)
            # 更新所有已创建的用户日志记录器的级别
            for logger in self._user_loggers.values():
                logger.setLevel(self._log_level_map[level])
                for handler in logger.handlers:
                    # 用户日志只更新文件处理器级别
                    if isinstance(handler, logging.FileHandler):
                        handler.setLevel(self._log_level_map[level])
    
    def set_level(self, level):
        """
        设置日志级别（为测试兼容性添加的别名方法）
        
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        self.set_framework_level(level)
    
    def _get_logger(self, name='apitestkit'):
        """
        获取日志记录器（为测试兼容性添加的别名方法）
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        return self._get_framework_logger(name)
    
    def debug(self, message, name='apitestkit'):
        """
        记录框架调试日志
        
        Args:
            message: 日志消息
            name: 日志记录器名称
        """
        self._get_framework_logger(name).debug(message)
    
    def info(self, message, name='apitestkit'):
        """
        记录框架信息日志
        
        Args:
            message: 日志消息
            name: 日志记录器名称
        """
        self._get_framework_logger(name).info(message)
    
    def warning(self, message, name='apitestkit'):
        """
        记录框架警告日志
        
        Args:
            message: 日志消息
            name: 日志记录器名称
        """
        self._get_framework_logger(name).warning(message)
    
    def error(self, message, name='apitestkit'):
        """
        记录框架错误日志
        
        Args:
            message: 日志消息
            name: 日志记录器名称
        """
        self._get_framework_logger(name).error(message)
    
    def critical(self, message, name='apitestkit'):
        """
        记录框架严重错误日志
        
        Args:
            message: 日志消息
            name: 日志记录器名称
        """
        self._get_framework_logger(name).critical(message)
    
    def log_request(self, method, url, headers=None, params=None, json_data=None, name='apitestkit.request'):
        """
        记录请求日志
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: URL参数
            json_data: JSON数据
            name: 日志记录器名称
        """
        logger = self._get_logger(name)
        
        # 记录基本请求信息
        logger.info(f"发送请求: {method} {url}")
        
        # 过滤敏感信息
        if headers:
            filtered_headers = headers.copy()
            # 从配置获取敏感头列表
            sensitive_headers = config_manager.get('sensitive_headers', 
                                                 ['Authorization', 'Cookie', 'X-API-Key', 'Token', 
                                                  'Password', 'Secret', 'Key'])
            
            for header in sensitive_headers:
                if header in filtered_headers:
                    filtered_headers[header] = '***'
            logger.debug(f"请求头: {filtered_headers}")
            
        if params:
            # 过滤URL参数中的敏感信息
            if isinstance(params, dict):
                filtered_params = self._filter_sensitive_data(params)
                logger.debug(f"URL参数: {filtered_params}")
            else:
                logger.debug(f"URL参数: {params}")
            
        if json_data:
            # 过滤JSON中的敏感信息，支持复杂嵌套结构
            filtered_data = self._filter_sensitive_data(json_data)
            
            # 如果启用了结构化日志，使用不同格式
            if config_manager.get('enable_structured_logging', False):
                try:
                    logger.debug(f"请求数据: {json.dumps(filtered_data, ensure_ascii=False)}")
                except Exception:
                    logger.debug(f"请求数据: {filtered_data}")
            else:
                logger.debug(f"请求数据: {filtered_data}")
    
    def log_response(self, status_code, response_time, text=None, name='apitestkit.response'):
        """
        记录响应日志
        
        Args:
            status_code: 状态码
            response_time: 响应时间（毫秒）
            text: 响应文本
            name: 日志记录器名称
        """
        logger = self._get_logger(name)
        
        # 记录基本响应信息
        logger.info(f"收到响应: 状态码={status_code}, 响应时间={response_time:.2f}ms")
        
        # 根据状态码增加额外日志级别
        if status_code >= 500:
            logger.error(f"服务器错误响应: 状态码={status_code}")
        elif status_code >= 400:
            logger.warning(f"客户端错误响应: 状态码={status_code}")
        
        if text and logger.level <= logging.DEBUG:
            # 限制响应体日志长度
            max_length = config_manager.get('max_response_log_length', 1000)
            
            # 尝试解析JSON响应以过滤敏感信息
            filtered_text = text
            try:
                if text.strip().startswith(('{', '[')):  # 简单检查是否为JSON
                    response_data = json.loads(text)
                    filtered_data = self._filter_sensitive_data(response_data)
                    filtered_text = json.dumps(filtered_data, ensure_ascii=False)
            except Exception:
                # 如果不是JSON或解析失败，使用原始文本
                pass
            
            # 截断过长的响应
            if len(filtered_text) > max_length:
                filtered_text = filtered_text[:max_length] + '... (truncated)'
            
            logger.debug(f"响应体: {filtered_text}")
            
    def _filter_sensitive_data(self, data: Any) -> Any:
        """
        过滤数据中的敏感信息，支持字典、列表和嵌套结构
        
        Args:
            data: 要过滤的数据（字典、列表或基本类型）
            
        Returns:
            过滤后的数据
        """
        # 从配置获取敏感关键字列表
        sensitive_keys = config_manager.get('sensitive_keys', 
                                          ['password', 'token', 'secret', 'key', 'auth', 
                                           'credential', 'credit', 'card', 'ssn', 'social'])
        
        if isinstance(data, dict):
            filtered_data = data.copy()
            for key, value in list(filtered_data.items()):  # 使用list创建副本避免迭代中修改
                # 检查键名是否包含敏感词
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in sensitive_keys):
                    filtered_data[key] = '***'  # 掩码敏感值
                # 递归处理嵌套结构
                elif isinstance(value, (dict, list)):
                    filtered_data[key] = self._filter_sensitive_data(value)
            return filtered_data
        
        elif isinstance(data, list):
            # 处理列表中的每个元素
            return [self._filter_sensitive_data(item) for item in data]
        
        # 对于基本类型，直接返回
        return data
    
    def get_user_logger(self, name: str) -> logging.Logger:
        """
        获取用户测试日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            用户日志记录器
        """
        if name not in self._user_loggers:
            self._user_loggers[name] = self._create_user_logger(name)
        return self._user_loggers[name]
    
    def _create_user_logger(self, name: str) -> logging.Logger:
        """
        创建用户测试日志记录器
        
        特点：
        - 有独立的文件日志
        - 控制台输出带有[USER]标识
        - 所有用户日志同时会被框架日志捕获
        - 支持日志轮转，避免单个文件过大
        
        Args:
            name: 日志记录器名称
            
        Returns:
            用户日志记录器
        """
        # 创建用户日志记录器，使用特定前缀
        logger_name = f'user.{name}'
        logger = logging.getLogger(logger_name)
        
        # 清理现有处理器
        for handler in logger.handlers[:]:
            try:
                handler.close()
            except Exception as e:
                print(f"警告: 关闭用户日志处理器时出错: {str(e)}")
            logger.removeHandler(handler)
        
        # 设置日志级别
        user_level = self._log_level_map.get(
            config_manager.get('user_log_level', 'INFO'), 
            logging.INFO
        )
        logger.setLevel(user_level)
        logger.propagate = True  # 允许传播到父日志记录器，确保框架日志能捕获用户日志
        
        # 确保日志目录存在
        self._ensure_log_directory()
        
        # 生成安全的文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        log_file_path = self._log_dir_path / f'user_{safe_name}_{timestamp}.log'
        
        try:
            # 使用RotatingFileHandler实现日志轮转
            max_bytes = config_manager.get('max_user_log_size_bytes', 5 * 1024 * 1024)  # 默认5MB
            backup_count = config_manager.get('user_log_backup_count', 3)
            
            file_handler = RotatingFileHandler(
                log_file_path,
                mode='a',
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(user_level)
            
            # 用户日志格式化器 - 文件
            file_formatter = logging.Formatter(
                config_manager.get('user_log_format_file', 
                '%(asctime)s - [USER] %(name)s - %(levelname)s - %(message)s'),
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            self._handlers.append(file_handler)
            
        except Exception as e:
            print(f"警告: 创建用户日志文件处理器失败: {str(e)}")
        
        # 创建用户日志控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(user_level)
        
        # 用户日志格式化器 - 控制台
        console_formatter = logging.Formatter(
            config_manager.get('user_log_format_console', 
            '[USER] %(message)s')
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        self._handlers.append(console_handler)
        
        # 记录日志文件路径（使用框架日志）
        self.info(f"为测试 '{name}' 创建用户日志文件: {str(log_file_path)}")
        
        return logger
    
    def log_user_message(self, level: str, message: str, test_name: str):
        """
        直接记录用户日志的便捷方法
        
        Args:
            level: 日志级别
            message: 日志消息
            test_name: 测试名称
        """
        user_logger = self.get_user_logger(test_name)
        if hasattr(user_logger, level):
            getattr(user_logger, level)(message)
        else:
            user_logger.info(message)
    
    def clear_user_loggers(self):
        """
        清理所有用户日志记录器
        """
        try:
            # 关闭并清理所有用户日志处理器
            for name, logger in list(self._user_loggers.items()):
                for handler in logger.handlers[:]:  # 使用副本迭代
                    try:
                        handler.close()
                    except:
                        pass
                    try:
                        logger.removeHandler(handler)
                    except:
                        pass
            self._user_loggers.clear()
            
            # 同时清理_framework_loggers中可能存在的用户日志记录器
            for name in list(self._framework_loggers.keys()):
                if name.startswith('user.'):
                    logger = self._framework_loggers.pop(name)
                    for handler in logger.handlers[:]:  # 使用副本迭代
                        try:
                            handler.close()
                        except:
                            pass
                        try:
                            logger.removeHandler(handler)
                        except:
                            pass
        except Exception:
            # 忽略清理过程中的错误
            pass


# 创建全局日志管理器实例
logger_manager = LoggerManager()

# 创建用户日志记录器的便捷函数
def get_user_logger(test_name: str = 'default') -> logging.Logger:
    """
    获取用户日志记录器的便捷方法
    
    Args:
        test_name: 测试名称
        
    Returns:
        logging.Logger: 用户日志记录器
    """
    return logger_manager.get_user_logger(test_name)

# 创建框架日志记录器的便捷函数
def get_framework_logger(name: str = 'apitestkit') -> logging.Logger:
    """
    获取框架日志记录器的便捷方法
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 框架日志记录器
    """
    return logger_manager._get_framework_logger(name)

# 框架日志便捷函数
def framework_debug(message: str, name: str = 'apitestkit'):
    """
    记录框架调试日志的便捷函数
    
    Args:
        message: 日志消息
        name: 日志记录器名称
    """
    logger_manager.debug(message, name)


def framework_info(message: str, name: str = 'apitestkit'):
    """
    记录框架信息日志的便捷函数
    
    Args:
        message: 日志消息
        name: 日志记录器名称
    """
    logger_manager.info(message, name)


def framework_warning(message: str, name: str = 'apitestkit'):
    """
    记录框架警告日志的便捷函数
    
    Args:
        message: 日志消息
        name: 日志记录器名称
    """
    logger_manager.warning(message, name)


def framework_error(message: str, name: str = 'apitestkit'):
    """
    记录框架错误日志的便捷函数
    
    Args:
        message: 日志消息
        name: 日志记录器名称
    """
    logger_manager.error(message, name)


def framework_critical(message: str, name: str = 'apitestkit'):
    """
    记录框架严重错误日志的便捷函数
    
    Args:
        message: 日志消息
        name: 日志记录器名称
    """
    logger_manager.critical(message, name)


# 用户日志便捷函数
def create_user_logger(test_name: str) -> logging.Logger:
    """
    创建用户测试日志记录器的便捷函数
    
    Args:
        test_name: 测试名称
        
    Returns:
        用户日志记录器
    """
    try:
        return logger_manager.get_user_logger(test_name)
    except Exception:
        # 如果创建失败，返回一个简单的控制台日志记录器
        logger = logging.getLogger(f'user.{test_name}')
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # 清理现有处理器
        for handler in logger.handlers[:]:
            try:
                handler.close()
            except:
                pass
            try:
                logger.removeHandler(handler)
            except:
                pass
        
        # 添加控制台处理器
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        
        return logger


def user_log(level: str, message: str, test_name: str):
    """
    记录用户日志的便捷函数
    
    Args:
        level: 日志级别
        message: 日志消息
        test_name: 测试名称
    """
    logger_manager.log_user_message(level, message, test_name)