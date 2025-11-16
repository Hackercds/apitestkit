"""
断言功能模块

提供丰富的API响应断言功能，支持各种断言场景。
增强版断言系统支持更多比较器、数组断言、深度比较、模糊匹配等高级功能。
"""

import json
import re
import time
import asyncio
from typing import Any, Dict, List, Union, Callable, Optional, Pattern
from dataclasses import dataclass
from apitestkit.core.logger import logger_manager, create_user_logger


@dataclass
class AssertionResult:
    """
    断言结果数据类
    """
    success: bool
    message: str
    assertion_type: str
    expected: Any = None
    actual: Any = None
    details: Dict[str, Any] = None


class AssertionError(Exception):
    """
    断言错误异常类
    """
    def __init__(self, message, assertion_type=None, expected=None, actual=None):
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
        super().__init__(message)


class ResponseAssertion:
    """
    响应断言类，提供各种断言方法
    
    支持多种比较器、数组断言、深度比较、模糊匹配等高级功能。
    """
    
    # 支持的比较器
    COMPARATORS = {
        'eq': lambda a, b: a == b,
        'neq': lambda a, b: a != b,
        'gt': lambda a, b: a > b,
        'gte': lambda a, b: a >= b,
        'lt': lambda a, b: a < b,
        'lte': lambda a, b: a <= b,
        'contains': lambda a, b: b in str(a),
        'not_contains': lambda a, b: b not in str(a),
        'startswith': lambda a, b: str(a).startswith(str(b)),
        'endswith': lambda a, b: str(a).endswith(str(b)),
        'matches': lambda a, b: bool(re.search(str(b), str(a))),
        'not_matches': lambda a, b: not bool(re.search(str(b), str(a))),
        'type': lambda a, b: isinstance(a, b),
        'length_eq': lambda a, b: len(a) == b,
        'length_gt': lambda a, b: len(a) > b,
        'length_lt': lambda a, b: len(a) < b,
        'any': lambda a, b: any(item == b for item in a) if isinstance(a, (list, tuple)) else False,
        'all': lambda a, b: all(item == b for item in a) if isinstance(a, (list, tuple)) else False
    }
    
    # 比较器描述
    COMPARATOR_DESCRIPTIONS = {
        'eq': '等于',
        'neq': '不等于',
        'gt': '大于',
        'gte': '大于等于',
        'lt': '小于',
        'lte': '小于等于',
        'contains': '包含',
        'not_contains': '不包含',
        'startswith': '以...开头',
        'endswith': '以...结尾',
        'matches': '匹配正则',
        'not_matches': '不匹配正则',
        'type': '类型为',
        'length_eq': '长度等于',
        'length_gt': '长度大于',
        'length_lt': '长度小于',
        'any': '任一元素等于',
        'all': '所有元素等于'
    }
    
    def __init__(self, user_logger=None):
        """
        初始化断言器
        
        Args:
            user_logger: 用户日志记录器，如果为None则使用默认日志器
        """
        self.user_logger = user_logger or create_user_logger("assertion_logger")
        self.failed_assertions = []
        
    def _get_comparator(self, comparator):
        """
        获取比较器函数
        
        Args:
            comparator: 比较器名称
            
        Returns:
            Callable: 比较器函数
            
        Raises:
            ValueError: 当比较器不存在时抛出
        """
        if comparator not in self.COMPARATORS:
            available = ', '.join(self.COMPARATORS.keys())
            raise ValueError(f"不支持的比较器: {comparator}. 可用的比较器: {available}")
        return self.COMPARATORS[comparator]
    
    def _get_comparator_description(self, comparator):
        """
        获取比较器描述
        
        Args:
            comparator: 比较器名称
            
        Returns:
            str: 比较器描述
        """
        return self.COMPARATOR_DESCRIPTIONS.get(comparator, comparator)
    
    def assert_status_code(self, response, expected_status, comparator='eq'):
        """
        断言响应状态码满足指定条件
        
        Args:
            response: 响应对象
            expected_status: 期望的状态码
            comparator: 比较器，默认为'eq'（等于）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        actual_status = response.status_code
        comparator_func = self._get_comparator(comparator)
        comparator_desc = self._get_comparator_description(comparator)
        
        try:
            assert comparator_func(actual_status, expected_status), \
                f"状态码断言失败：期望 {comparator_desc} {expected_status}，实际 {actual_status}"
            # 确保日志器正常工作
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"状态码断言成功：{actual_status} {comparator_desc} {expected_status}")
            return True
        except AssertionError as e:
            error_message = str(e)
            self.failed_assertions.append({
                'type': 'status_code',
                'expected': expected_status,
                'actual': actual_status,
                'comparator': comparator,
                'message': error_message
            })
            # 确保日志器正常工作
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
            raise AssertionError(error_message)
    
    def assert_status_code_in(self, response, expected_statuses):
        """
        断言响应状态码在指定范围内
        
        Args:
            response: 响应对象
            expected_statuses: 期望的状态码列表或范围
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        actual_status = response.status_code
        
        try:
            assert actual_status in expected_statuses, \
                f"状态码断言失败：期望在 {expected_statuses} 中，实际 {actual_status}"
            self.user_logger.info(f"状态码断言成功：{actual_status} 在 {expected_statuses} 中")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'status_code_in',
                'expected': expected_statuses,
                'actual': actual_status,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_status_code_not_in(self, response, unexpected_statuses):
        """
        断言响应状态码不在指定范围内
        
        Args:
            response: 响应对象
            unexpected_statuses: 不期望的状态码列表或范围
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        actual_status = response.status_code
        
        try:
            assert actual_status not in unexpected_statuses, \
                f"状态码断言失败：期望不在 {unexpected_statuses} 中，实际 {actual_status}"
            # 确保日志器正常工作
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"状态码断言成功：{actual_status} 不在 {unexpected_statuses} 中")
            return True
        except AssertionError as e:
            error_message = str(e)
            self.failed_assertions.append({
                'type': 'status_code_not_in',
                'expected': unexpected_statuses,
                'actual': actual_status,
                'message': error_message
            })
            # 确保日志器正常工作
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
            raise AssertionError(error_message)
    
    def _extract_json_path(self, json_data, json_path):
        """
        从JSON数据中提取指定路径的值
        
        Args:
            json_data: JSON数据
            json_path: JSON路径（使用点号分隔，如 'data.user.id'）
            
        Returns:
            Any: 提取的值，如果路径不存在返回None
        """
        # 处理空路径
        if not json_path:
            return json_data
        
        # 支持更复杂的JSON路径表达式
        # 如: data.users[0].name, data.*.id, data.users[*].name
        if '[' in json_path and ']' in json_path:
            # 处理带数组索引的路径
            path_parts = []
            current = ''
            in_brackets = False
            
            for char in json_path:
                if char == '[':
                    in_brackets = True
                    if current:
                        path_parts.append(current)
                        current = ''
                    path_parts.append(char)
                elif char == ']':
                    in_brackets = False
                    path_parts.append(current + char)
                    current = ''
                elif char == '.' and not in_brackets:
                    if current:
                        path_parts.append(current)
                    current = ''
                else:
                    current += char
            
            if current:
                path_parts.append(current)
            
            actual_value = json_data
            for part in path_parts:
                if part.startswith('[') and part.endswith(']'):
                    # 处理数组索引
                    index_str = part[1:-1].strip()
                    if index_str == '*':
                        # 通配符，返回所有元素
                        if isinstance(actual_value, list):
                            # 特殊处理：如果是最后一个路径部分，返回整个数组
                            if part == path_parts[-1]:
                                return actual_value
                            # 否则，尝试从每个元素中继续提取
                            results = []
                            remaining_path = '.'.join(path_parts[path_parts.index(part) + 1:])
                            for item in actual_value:
                                try:
                                    # 递归提取剩余路径的值
                                    extracted_value = self._extract_json_path(item, remaining_path)
                                    if extracted_value is not None:
                                        results.append(extracted_value)
                                except AssertionError:
                                    # 跳过不存在路径的元素
                                    continue
                            # 返回结果列表，如果为空则返回None
                            return results if results else None
                        else:
                            # 非数组使用通配符，返回None
                            return None
                    elif index_str.isdigit():
                        index = int(index_str)
                        if isinstance(actual_value, list) and 0 <= index < len(actual_value):
                            actual_value = actual_value[index]
                        else:
                            # 索引越界或非列表，返回None
                            return None
                    else:
                        # 无效索引，返回None
                        return None
                else:
                    # 处理对象属性
                    if part == '*' and isinstance(actual_value, dict):
                        # 通配符，返回所有属性值
                        if part == path_parts[-1]:
                            return list(actual_value.values())
                        # 否则，尝试从每个属性值中继续提取
                        results = []
                        remaining_path = '.'.join(path_parts[path_parts.index(part) + 1:])
                        for value in actual_value.values():
                            try:
                                extracted_value = self._extract_json_path(value, remaining_path)
                                # 只有成功提取的值才加入结果
                                if extracted_value is not None:
                                    results.append(extracted_value)
                            except AssertionError:
                                continue
                        return results if results else None
                    elif isinstance(actual_value, dict) and part in actual_value:
                        actual_value = actual_value[part]
                    else:
                        # 属性不存在，返回None
                        return None
            
            return actual_value
        else:
            # 处理简单的点分隔路径
            keys = json_path.split('.')
            actual_value = json_data
            
            for key in keys:
                # 支持通配符
                if key == '*' and isinstance(actual_value, dict):
                    actual_value = list(actual_value.values())
                    # 如果是空字典，返回None
                    if not actual_value:
                        return None
                    # 如果是最后一个键，返回所有值
                    if key == keys[-1]:
                        return actual_value
                    # 否则，从第一个值继续
                    actual_value = actual_value[0]
                # 支持数组索引
                elif isinstance(actual_value, list) and key.isdigit():
                    index = int(key)
                    if 0 <= index < len(actual_value):
                        actual_value = actual_value[index]
                    else:
                        # 索引越界，返回None
                        return None
                elif isinstance(actual_value, dict) and key in actual_value:
                    actual_value = actual_value[key]
                else:
                    # 路径不存在，返回None
                    return None
            
            return actual_value
    
    def assert_json_path(self, response, json_path, expected_value, comparator='eq'):
        """
        断言JSON路径的值
        
        Args:
            response: 响应对象
            json_path: JSON路径（使用点号分隔，支持通配符和数组索引）
            expected_value: 期望的值
            comparator: 比较器，默认为'eq'（等于）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            compare_func = self._get_comparator(comparator)
            comparator_desc = self._get_comparator_description(comparator)
            
            # 执行比较
            comparison_result = False
            if comparator in ['contains', 'not_contains']:
                comparison_result = compare_func(str(actual_value), expected_value)
            else:
                comparison_result = compare_func(actual_value, expected_value)
            
            if not comparison_result:
                if comparator in ['contains', 'not_contains']:
                    error_message = f"JSON路径断言失败：路径 '{json_path}'，期望 {comparator_desc} '{expected_value}'，实际 '{actual_value}'"
                else:
                    error_message = f"JSON路径断言失败：路径 '{json_path}'，期望 {comparator_desc} {expected_value}，实际 {actual_value}"
                
                # 记录失败信息
                self.failed_assertions.append({
                    'type': 'json_path',
                    'expected': expected_value,
                    'actual': actual_value,
                    'path': json_path,
                    'comparator': comparator,
                    'message': error_message
                })
                
                # 安全地记录错误
                if hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                    
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"JSON路径断言成功：路径 '{json_path}' 值 {comparator_desc} {expected_value}")
                
            return True
        except AssertionError:
            # 重新抛出AssertionError以保持测试行为一致
            raise
        except (ValueError, TypeError) as e:
            error_message = f"JSON解析失败: {str(e)}"
            
            # 安全地记录错误
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
        except Exception as e:
            # 处理其他异常
            error_message = f"JSON路径断言出错：{str(e)}"
            
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_json_path_exists(self, response, json_path):
        """
        断言JSON路径存在
        
        Args:
            response: 响应对象
            json_path: JSON路径
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            value = self._extract_json_path(json_data, json_path)
            
            # 检查提取的值是否为None（路径不存在）
            if value is None:
                error_message = f"JSON路径存在断言失败：路径 '{json_path}' 不存在"
                # 记录失败信息
                if hasattr(self, 'failed_assertions'):
                    self.failed_assertions.append({
                        'type': 'json_path_exists',
                        'path': json_path,
                        'message': error_message
                    })
                
                if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                    
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"JSON路径存在断言成功：路径 '{json_path}' 存在")
                
            return True
        except (ValueError, TypeError) as e:
            error_message = f"JSON解析失败: {str(e)}"
            
            # 安全地记录错误
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
        except AssertionError:
            # 重新抛出之前的AssertionError
            raise
        except Exception as e:
            # 处理其他未预期的异常
            error_message = f"JSON路径断言错误：路径 '{json_path}' 出现错误: {str(e)}"
            
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_json_path_not_exists(self, response, json_path):
        """
        断言JSON路径不存在
        
        Args:
            response: 响应对象
            json_path: JSON路径
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            
            # 直接调用_extract_json_path，根据返回值判断路径是否存在
            value = self._extract_json_path(json_data, json_path)
            
            # 根据路径是否存在来决定断言结果
            if value is not None:
                # 路径存在，断言失败
                error_message = f"JSON路径不存在断言失败：路径 '{json_path}' 存在，值为 '{value}'"
                
                # 记录失败信息
                if hasattr(self, 'failed_assertions'):
                    self.failed_assertions.append({
                        'type': 'json_path_not_exists',
                        'path': json_path,
                        'message': error_message
                    })
                
                # 安全地记录错误
                if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                
                # 抛出断言失败错误
                raise AssertionError(error_message)
            else:
                # 路径不存在，断言成功
                if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'info'):
                    self.user_logger.info(f"JSON路径不存在断言成功：路径 '{json_path}' 不存在")
                return True
                
        except (ValueError, TypeError) as e:
            error_message = f"JSON解析失败: {str(e)}"
            
            # 安全地记录错误
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_json_path_contains(self, response, json_path, expected_substring):
        """
        断言JSON路径的值包含指定子字符串
        
        Args:
            response: 响应对象
            json_path: JSON路径
            expected_substring: 期望的子字符串
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            # 确保实际值是字符串
            actual_str = str(actual_value)
            
            # 执行比较
            if expected_substring not in actual_str:
                error_message = f"JSON路径包含断言失败：路径 '{json_path}' 的值 '{actual_str}' 不包含 '{expected_substring}'"
                
                # 记录失败信息
                self.failed_assertions.append({
                    'type': 'json_path_contains',
                    'expected': expected_substring,
                    'actual': actual_value,
                    'path': json_path,
                    'message': error_message
                })
                
                # 安全地记录错误
                if hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                    
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"JSON路径包含断言成功：路径 '{json_path}' 的值包含 '{expected_substring}'")
                
            return True
        except AssertionError:
            # 重新抛出AssertionError以保持测试行为一致
            raise
        except (ValueError, TypeError) as e:
            error_message = f"JSON解析失败: {str(e)}"
            
            # 安全地记录错误
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
        except Exception as e:
            # 处理其他异常
            error_message = f"JSON路径包含断言出错：{str(e)}"
            
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_json_path_length(self, response, json_path, expected_length, comparator='eq'):
        """
        断言JSON路径的值的长度
        
        Args:
            response: 响应对象
            json_path: JSON路径
            expected_length: 期望的长度
            comparator: 比较器，默认为'eq'（等于）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            # 检查是否有长度属性
            try:
                actual_length = len(actual_value)
            except (TypeError, AttributeError):
                error_message = f"无法获取路径 '{json_path}' 值的长度"
                if hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                raise AssertionError(error_message)
            
            compare_func = self._get_comparator(comparator)
            comparator_desc = self._get_comparator_description(comparator)
            
            # 执行比较
            if not compare_func(actual_length, expected_length):
                error_message = f"JSON路径长度断言失败：路径 '{json_path}'，期望长度 {comparator_desc} {expected_length}，实际长度 {actual_length}"
                
                # 记录失败信息
                self.failed_assertions.append({
                    'type': 'json_path_length',
                    'expected': expected_length,
                    'actual': actual_length,
                    'path': json_path,
                    'comparator': comparator,
                    'message': error_message
                })
                
                # 安全地记录错误
                if hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                    
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"JSON路径长度断言成功：路径 '{json_path}' 长度 {comparator_desc} {expected_length}")
                
            return True
        except AssertionError:
            # 重新抛出AssertionError以保持测试行为一致
            raise
        except (ValueError, TypeError) as e:
            error_message = f"JSON解析失败: {str(e)}"
            
            # 安全地记录错误
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
        except Exception as e:
            # 处理其他异常
            error_message = f"JSON路径长度断言出错：{str(e)}"
            
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_json_path_type(self, response, json_path, expected_type):
        """
        断言JSON路径的值的类型
        
        Args:
            response: 响应对象
            json_path: JSON路径
            expected_type: 期望的类型（str, int, float, dict, list等）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            # 字符串类型映射到Python类型
            type_mapping = {
                'str': str,
                'int': int,
                'float': float,
                'dict': dict,
                'list': list,
                'bool': bool,
                'none': type(None)
            }
            
            if isinstance(expected_type, str):
                expected_type_obj = type_mapping.get(expected_type.lower(), type(expected_type))
            else:
                expected_type_obj = expected_type
            
            # 使用显式比较结果判断
            comparison_result = isinstance(actual_value, expected_type_obj)
            actual_type_name = type(actual_value).__name__
            
            if not comparison_result:
                error_message = f"JSON路径类型断言失败：路径 '{json_path}'，期望类型 {expected_type}，实际类型 {actual_type_name}"
                
                # 记录失败信息
                if hasattr(self, 'failed_assertions'):
                    self.failed_assertions.append({
                        'type': 'json_path_type',
                        'path': json_path,
                        'expected_type': expected_type,
                        'actual_type': actual_type_name,
                        'message': error_message
                    })
                
                if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"JSON路径类型断言成功：路径 '{json_path}' 类型为 {expected_type}")
            
            return True
        except (ValueError, TypeError) as e:
            error_msg = f"JSON解析失败: {str(e)}"
            
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_msg)
            
            raise AssertionError(error_msg)
        except Exception as e:
            # 处理其他异常
            error_message = f"JSON路径类型断言出错：{str(e)}"
            
            if hasattr(self, 'user_logger') and hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
            
            raise AssertionError(error_message)
    
    def assert_json_path_in(self, response, json_path, expected_values):
        """
        断言JSON路径的值在指定列表中
        
        Args:
            response: 响应对象
            json_path: JSON路径
            expected_values: 期望的值列表
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            assert actual_value in expected_values, \
                f"JSON路径包含于断言失败：路径 '{json_path}' 的值 {actual_value} 不在 {expected_values} 中"
            
            self.user_logger.info(f"JSON路径包含于断言成功：路径 '{json_path}' 的值 {actual_value} 在 {expected_values} 中")
            return True
        except (ValueError, TypeError) as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_json_path_not_in(self, response, json_path, unexpected_values):
        """
        断言JSON路径的值不在指定列表中
        
        Args:
            response: 响应对象
            json_path: JSON路径
            unexpected_values: 不期望的值列表
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            assert actual_value not in unexpected_values, \
                f"JSON路径不包含于断言失败：路径 '{json_path}' 的值 {actual_value} 在 {unexpected_values} 中"
            
            self.user_logger.info(f"JSON路径不包含于断言成功：路径 '{json_path}' 的值 {actual_value} 不在 {unexpected_values} 中")
            return True
        except (ValueError, TypeError) as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_json_path_regex(self, response, json_path, regex_pattern):
        """
        断言JSON路径的值匹配正则表达式
        
        Args:
            response: 响应对象
            json_path: JSON路径
            regex_pattern: 正则表达式模式
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            json_data = response.json()
            actual_value = self._extract_json_path(json_data, json_path)
            
            assert isinstance(regex_pattern, str), "正则表达式必须是字符串"
            
            match = re.search(regex_pattern, str(actual_value))
            assert match is not None, \
                f"JSON路径正则匹配失败：路径 '{json_path}' 的值 '{actual_value}' 不匹配模式 '{regex_pattern}'"
            
            self.user_logger.info(f"JSON路径正则匹配成功：路径 '{json_path}' 的值匹配模式 '{regex_pattern}'")
            return True
        except (ValueError, TypeError) as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_json_deep_equal(self, response, expected_data, ignore_order=False):
        """
        深度比较JSON响应和期望数据
        
        Args:
            response: 响应对象
            expected_data: 期望的JSON数据
            ignore_order: 是否忽略数组顺序，默认为False
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        def _deep_compare(actual, expected, path="$"):
            """深度比较函数"""
            # 检查类型
            if type(actual) != type(expected):
                return False, f"{path}: 类型不匹配: 期望 {type(expected).__name__}, 实际 {type(actual).__name__}"
            
            # 比较基本类型
            if isinstance(expected, (str, int, float, bool, type(None))):
                if actual != expected:
                    return False, f"{path}: 值不匹配: 期望 {expected}, 实际 {actual}"
                return True, ""
            
            # 比较字典
            elif isinstance(expected, dict):
                # 检查键是否存在
                for key in expected:
                    if key not in actual:
                        return False, f"{path}.{key}: 键不存在"
                
                # 深度比较每个值
                for key in expected:
                    success, message = _deep_compare(actual[key], expected[key], f"{path}.{key}")
                    if not success:
                        return False, message
                return True, ""
            
            # 比较列表
            elif isinstance(expected, list):
                if len(actual) != len(expected) and not ignore_order:
                    return False, f"{path}: 长度不匹配: 期望 {len(expected)}, 实际 {len(actual)}"
                
                if ignore_order:
                    # 忽略顺序比较，使用集合思想
                    # 这里简化处理，实际可能需要更复杂的比较逻辑
                    if len(actual) != len(expected):
                        return False, f"{path}: 长度不匹配: 期望 {len(expected)}, 实际 {len(actual)}"
                    
                    # 尝试匹配每个元素
                    matched = set()
                    for i, exp_item in enumerate(expected):
                        found = False
                        for j, act_item in enumerate(actual):
                            if j not in matched:
                                success, _ = _deep_compare(act_item, exp_item)
                                if success:
                                    matched.add(j)
                                    found = True
                                    break
                        if not found:
                            return False, f"{path}[{i}]: 找不到匹配的元素 {exp_item}"
                    return True, ""
                else:
                    # 按顺序比较
                    for i, (act_item, exp_item) in enumerate(zip(actual, expected)):
                        success, message = _deep_compare(act_item, exp_item, f"{path}[{i}]")
                        if not success:
                            return False, message
                    return True, ""
            
            return False, f"{path}: 不支持的类型 {type(expected).__name__}"
        
        try:
            actual_data = response.json()
            success, message = _deep_compare(actual_data, expected_data)
            
            assert success, f"JSON深度比较失败: {message}"
            
            self.user_logger.info(f"JSON深度比较成功")
            return True
        except (ValueError, TypeError) as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_response_time(self, response, expected_time, comparator='lte'):
        """
        断言响应时间
        
        Args:
            response: 响应对象（包含response_time属性）
            expected_time: 期望的响应时间（秒）
            comparator: 比较器，默认为'lte'（小于等于）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        comparator_func = self._get_comparator(comparator)
        comparator_desc = self._get_comparator_description(comparator)
        
        try:
            # 从响应对象获取响应时间
            actual_time = getattr(response, 'response_time', 0)
            
            # 确保值都是数字类型
            actual_time = float(actual_time)
            expected_time = float(expected_time)
            
            # 执行比较
            comparison_result = comparator_func(actual_time, expected_time)
            
            if not comparison_result:
                error_message = f"响应时间断言失败：期望 {comparator_desc} {expected_time}秒，实际 {actual_time:.2f}秒"
                
                # 记录失败信息
                self.failed_assertions.append({
                    'type': 'response_time',
                    'expected': expected_time,
                    'actual': actual_time,
                    'comparator': comparator,
                    'message': error_message
                })
                
                # 安全地记录错误
                if hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                    
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"响应时间断言成功：{actual_time:.2f}秒 {comparator_desc} {expected_time}秒")
                
            return True
        except AssertionError:
            # 重新抛出AssertionError以保持测试行为一致
            raise
        except Exception as e:
            # 处理其他异常
            error_message = f"响应时间断言出错：{str(e)}"
            
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_response_time_range(self, response, min_time, max_time):
        """
        断言响应时间在指定范围内
        
        Args:
            response: 响应对象（包含response_time属性）
            min_time: 最小允许响应时间（秒）
            max_time: 最大允许响应时间（秒）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            # 从响应对象获取响应时间
            actual_time = getattr(response, 'response_time', 0)
            
            # 确保所有值都是数字类型
            actual_time = float(actual_time)
            min_time = float(min_time)
            max_time = float(max_time)
            
            # 执行范围检查
            in_range = min_time <= actual_time <= max_time
            
            if not in_range:
                error_message = f"响应时间范围断言失败：期望在 [{min_time}, {max_time}]秒 之间，实际 {actual_time:.2f}秒"
                
                # 记录失败信息
                self.failed_assertions.append({
                    'type': 'response_time_range',
                    'expected': f"[{min_time}, {max_time}]秒",
                    'actual': actual_time,
                    'message': error_message
                })
                
                # 安全地记录错误
                if hasattr(self.user_logger, 'error'):
                    self.user_logger.error(error_message)
                    
                raise AssertionError(error_message)
            
            # 安全地记录成功日志
            if hasattr(self.user_logger, 'info'):
                self.user_logger.info(f"响应时间范围断言成功：{actual_time:.2f}秒 在 [{min_time}, {max_time}]秒 之间")
                
            return True
        except AssertionError:
            # 重新抛出AssertionError以保持测试行为一致
            raise
        except Exception as e:
            # 处理其他异常
            error_message = f"响应时间范围断言出错：{str(e)}"
            
            if hasattr(self.user_logger, 'error'):
                self.user_logger.error(error_message)
                
            raise AssertionError(error_message)
    
    def assert_header_exists(self, response, header_name):
        """
        断言响应头存在
        
        Args:
            response: 响应对象
            header_name: 响应头名称
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert header_name in response.headers, \
                f"响应头断言失败：未找到头信息 '{header_name}'"
            self.user_logger.info(f"响应头断言成功：找到头信息 '{header_name}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'header_exists',
                'expected': header_name,
                'actual': None,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_header_not_exists(self, response, header_name):
        """
        断言响应头不存在
        
        Args:
            response: 响应对象
            header_name: 响应头名称
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert header_name not in response.headers, \
                f"响应头断言失败：找到不期望的头信息 '{header_name}'"
            self.user_logger.info(f"响应头不存在断言成功：未找到头信息 '{header_name}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'header_not_exists',
                'expected': None,
                'actual': header_name,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_header_value(self, response, header_name, expected_value, comparator='eq'):
        """
        断言响应头的值
        
        Args:
            response: 响应对象
            header_name: 响应头名称
            expected_value: 期望的值
            comparator: 比较器，默认为'eq'（等于）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert header_name in response.headers, \
                f"响应头断言失败：未找到头信息 '{header_name}'"
            
            actual_value = response.headers[header_name]
            compare_func = self._get_comparator(comparator)
            
            # 对于某些比较器（如contains, matches），确保两边都是可比较的类型
            if comparator in ['contains', 'not_contains', 'matches', 'not_matches']:
                assert compare_func(str(actual_value), expected_value), \
                    f"响应头值断言失败：头 '{header_name}' 期望 {self._get_comparator_description(comparator)} '{expected_value}'，实际 '{actual_value}'"
            else:
                assert compare_func(actual_value, expected_value), \
                    f"响应头值断言失败：头 '{header_name}' 期望 {self._get_comparator_description(comparator)} '{expected_value}'，实际 '{actual_value}'"
            
            self.user_logger.info(f"响应头值断言成功：头 '{header_name}' 值 {self._get_comparator_description(comparator)} '{expected_value}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'header_value',
                'expected': expected_value,
                'actual': response.headers.get(header_name),
                'comparator': comparator,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_header_contains(self, response, header_name, expected_substring):
        """
        断言响应头的值包含指定子字符串
        
        Args:
            response: 响应对象
            header_name: 响应头名称
            expected_substring: 期望的子字符串
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert header_name in response.headers, \
                f"响应头断言失败：未找到头信息 '{header_name}'"
            
            actual_value = response.headers[header_name]
            assert expected_substring in actual_value, \
                f"响应头包含断言失败：头 '{header_name}' 的值 '{actual_value}' 不包含 '{expected_substring}'"
            
            self.user_logger.info(f"响应头包含断言成功：头 '{header_name}' 的值包含 '{expected_substring}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'header_contains',
                'expected': expected_substring,
                'actual': response.headers.get(header_name),
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_response_contains(self, response, expected_content):
        """
        断言响应内容包含指定字符串
        
        Args:
            response: 响应对象
            expected_content: 期望包含的内容
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert expected_content in response.text, \
                f"响应内容断言失败：响应不包含 '{expected_content}'"
            self.user_logger.info(f"响应内容断言成功：响应包含 '{expected_content}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'response_contains',
                'expected': expected_content,
                'actual': response.text[:100] + '...' if len(response.text) > 100 else response.text,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_response_not_contains(self, response, unexpected_content):
        """
        断言响应内容不包含指定字符串
        
        Args:
            response: 响应对象
            unexpected_content: 不期望包含的内容
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert unexpected_content not in response.text, \
                f"响应内容断言失败：响应包含不期望的内容 '{unexpected_content}'"
            self.user_logger.info(f"响应内容不包含断言成功：响应不包含 '{unexpected_content}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'response_not_contains',
                'expected': None,
                'actual': unexpected_content,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_response_length(self, response, expected_length, comparator='eq'):
        """
        断言响应内容长度
        
        Args:
            response: 响应对象
            expected_length: 期望的长度
            comparator: 比较器，默认为'eq'（等于）
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        actual_length = len(response.text)
        compare_func = self._get_comparator(comparator)
        
        try:
            assert compare_func(actual_length, expected_length), \
                f"响应长度断言失败：期望 {self._get_comparator_description(comparator)} {expected_length}，实际 {actual_length}"
            self.user_logger.info(f"响应长度断言成功：{actual_length} {self._get_comparator_description(comparator)} {expected_length}")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'response_length',
                'expected': expected_length,
                'actual': actual_length,
                'comparator': comparator,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_response_matches(self, response, regex_pattern):
        """
        断言响应内容匹配正则表达式
        
        Args:
            response: 响应对象
            regex_pattern: 正则表达式模式
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            match = re.search(regex_pattern, response.text)
            assert match is not None, \
                f"响应正则匹配断言失败：响应不匹配模式 '{regex_pattern}'"
            
            # 记录匹配的内容
            matched_content = match.group(0) if match else ""
            self.user_logger.info(f"响应正则匹配断言成功：响应匹配模式 '{regex_pattern}'，匹配内容: '{matched_content}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'response_matches',
                'expected': regex_pattern,
                'actual': response.text[:100] + '...' if len(response.text) > 100 else response.text,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_response_not_matches(self, response, regex_pattern):
        """
        断言响应内容不匹配正则表达式
        
        Args:
            response: 响应对象
            regex_pattern: 正则表达式模式
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            match = re.search(regex_pattern, response.text)
            assert match is None, \
                f"响应正则不匹配断言失败：响应匹配了不期望的模式 '{regex_pattern}'"
            
            self.user_logger.info(f"响应正则不匹配断言成功：响应不匹配模式 '{regex_pattern}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'response_not_matches',
                'expected': None,
                'actual': regex_pattern,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_json_schema(self, response, schema):
        """
        断言JSON响应符合指定的schema
        注意：此功能需要安装jsonschema库
        
        Args:
            response: 响应对象
            schema: JSON schema定义
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            import jsonschema
            from jsonschema import validate, ValidationError as JsonSchemaValidationError
            
            json_data = response.json()
            validate(instance=json_data, schema=schema)
            
            self.user_logger.info("JSON Schema验证成功")
            return True
        except ImportError:
            error_msg = "JSON Schema验证需要安装jsonschema库：pip install jsonschema"
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
        except JsonSchemaValidationError as e:
            # 美化错误消息
            error_msg = f"JSON Schema验证失败: {str(e)}"
            # 尝试提取更详细的路径信息
            if hasattr(e, 'path') and e.path:
                path_str = '.'.join(str(p) for p in e.path)
                error_msg += f"，路径: {path_str}"
            
            self.failed_assertions.append({
                'type': 'json_schema',
                'expected': schema,
                'actual': response.json(),
                'message': error_msg
            })
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
        except (ValueError, TypeError) as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
    
    # 异步断言方法
    async def assert_json_path_async(self, response, json_path, expected_value, comparator='eq'):
        """
        异步断言JSON路径的值
        
        Args:
            response: 响应对象
            json_path: JSON路径
            expected_value: 期望的值
            comparator: 比较器
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        # 对于异步断言，我们可以在这里添加一些异步特有的逻辑
        # 比如处理异步响应流等
        return self.assert_json_path(response, json_path, expected_value, comparator)
    
    async def assert_status_code_async(self, response, expected_status, comparator='eq'):
        """
        异步断言响应状态码
        
        Args:
            response: 响应对象
            expected_status: 期望的状态码
            comparator: 比较器
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        return self.assert_status_code(response, expected_status, comparator)
    
    # 流式响应断言
    def assert_stream_contains(self, stream_data, expected_content):
        """
        断言流式响应包含指定内容
        
        Args:
            stream_data: 流式响应数据（字符串或字节流）
            expected_content: 期望包含的内容
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            # 确保stream_data是字符串
            if isinstance(stream_data, bytes):
                stream_str = stream_data.decode('utf-8')
            else:
                stream_str = str(stream_data)
            
            assert expected_content in stream_str, \
                f"流式响应断言失败：响应不包含 '{expected_content}'"
            
            self.user_logger.info(f"流式响应断言成功：响应包含 '{expected_content}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'stream_contains',
                'expected': expected_content,
                'actual': stream_str[:100] + '...' if len(stream_str) > 100 else stream_str,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_stream_matches(self, stream_data, regex_pattern):
        """
        断言流式响应匹配正则表达式
        
        Args:
            stream_data: 流式响应数据
            regex_pattern: 正则表达式模式
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            # 确保stream_data是字符串
            if isinstance(stream_data, bytes):
                stream_str = stream_data.decode('utf-8')
            else:
                stream_str = str(stream_data)
            
            match = re.search(regex_pattern, stream_str)
            assert match is not None, \
                f"流式响应正则匹配断言失败：响应不匹配模式 '{regex_pattern}'"
            
            self.user_logger.info(f"流式响应正则匹配断言成功：响应匹配模式 '{regex_pattern}'")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'stream_matches',
                'expected': regex_pattern,
                'actual': stream_str[:100] + '...' if len(stream_str) > 100 else stream_str,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    # 自定义断言方法
    def assert_custom(self, condition, message="自定义断言失败"):
        """
        自定义断言
        
        Args:
            condition: 断言条件
            message: 失败消息
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            assert condition, message
            self.user_logger.info(f"自定义断言成功: {message}")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'custom',
                'expected': True,
                'actual': condition,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    def assert_with_func(self, func, *args, **kwargs):
        """
        使用自定义函数进行断言
        
        Args:
            func: 断言函数，返回True表示通过，False表示失败
            *args: 传递给断言函数的位置参数
            **kwargs: 传递给断言函数的关键字参数
            
        Raises:
            AssertionError: 断言失败时抛出
        """
        try:
            result = func(*args, **kwargs)
            assert result, f"自定义函数断言失败: {func.__name__}"
            self.user_logger.info(f"自定义函数断言成功: {func.__name__}")
            return True
        except AssertionError as e:
            self.failed_assertions.append({
                'type': 'custom_func',
                'expected': True,
                'actual': False,
                'message': str(e)
            })
            self.user_logger.error(str(e))
            raise
    
    # 断言集合管理
    def clear_failed_assertions(self):
        """
        清除失败的断言记录
        """
        self.failed_assertions.clear()
    
    def get_failed_assertions(self):
        """
        获取失败的断言记录
        
        Returns:
            List[Dict]: 失败断言列表
        """
        return self.failed_assertions.copy()
    
    def has_failed_assertions(self):
        """
        检查是否有失败的断言
        
        Returns:
            bool: 如果有失败的断言返回True，否则返回False
        """
        return len(self.failed_assertions) > 0
    
    def assert_all_passed(self):
        """
        断言所有之前的断言都通过了
        
        Raises:
            AssertionError: 如果有失败的断言抛出
        """
        if self.has_failed_assertions():
            error_messages = [f"- {fail['message']}" for fail in self.failed_assertions]
            error_msg = "有断言失败:\n" + "\n".join(error_messages)
            self.user_logger.error(error_msg)
            raise AssertionError(error_msg)
        
        self.user_logger.info("所有断言通过")
        return True


# 创建全局断言实例
assertions = ResponseAssertion()