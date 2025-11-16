"""
响应验证器模块
提供对API响应进行各种验证的功能
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Union
import logging
from datetime import datetime

from apitestkit.core.logger import logger_manager
from apitestkit.exception.exceptions import ApiTestException
from apitestkit.response.handler import response_handler
from apitestkit.extractor.data_extractor import data_extractor

# 获取日志记录器
logger = logger_manager.get_logger(__name__)


class ResponseValidator:
    """
    响应验证器，提供多种验证方法
    """
    
    def validate_status_code(self, response: object, expected_status_code: Union[int, List[int]]) -> bool:
        """
        验证响应状态码
        
        Args:
            response: 响应对象
            expected_status_code: 期望的状态码或状态码列表
            
        Returns:
            是否验证通过
        """
        try:
            actual_status_code = response_handler.get_status_code(response)
            
            if isinstance(expected_status_code, list):
                result = actual_status_code in expected_status_code
                if not result:
                    logger.warning(f"状态码验证失败: 期望 {expected_status_code}, 实际 {actual_status_code}")
                return result
            else:
                result = actual_status_code == expected_status_code
                if not result:
                    logger.warning(f"状态码验证失败: 期望 {expected_status_code}, 实际 {actual_status_code}")
                return result
                
        except Exception as e:
            logger.error(f"状态码验证异常: {str(e)}")
            raise ApiTestException(f"状态码验证异常: {str(e)}")
    
    def validate_response_time(self, response: object, max_time_ms: int) -> bool:
        """
        验证响应时间
        
        Args:
            response: 响应对象
            max_time_ms: 最大响应时间（毫秒）
            
        Returns:
            是否验证通过
        """
        try:
            actual_time_ms = response_handler.get_response_time(response)
            result = actual_time_ms <= max_time_ms
            if not result:
                logger.warning(f"响应时间验证失败: 期望 <= {max_time_ms}ms, 实际 {actual_time_ms}ms")
            return result
        except Exception as e:
            logger.error(f"响应时间验证异常: {str(e)}")
            raise ApiTestException(f"响应时间验证异常: {str(e)}")
    
    def validate_contains_text(self, response: object, expected_text: str, case_sensitive: bool = True) -> bool:
        """
        验证响应文本是否包含指定内容
        
        Args:
            response: 响应对象
            expected_text: 期望包含的文本
            case_sensitive: 是否区分大小写
            
        Returns:
            是否验证通过
        """
        try:
            actual_text = response_handler.get_text(response)
            
            if case_sensitive:
                result = expected_text in actual_text
            else:
                result = expected_text.lower() in actual_text.lower()
            
            if not result:
                logger.warning(f"文本内容验证失败: 响应中未找到 '{expected_text}'")
            return result
            
        except Exception as e:
            logger.error(f"文本内容验证异常: {str(e)}")
            raise ApiTestException(f"文本内容验证异常: {str(e)}")
    
    def validate_matches_regex(self, response: object, regex_pattern: str) -> bool:
        """
        验证响应文本是否匹配正则表达式
        
        Args:
            response: 响应对象
            regex_pattern: 正则表达式
            
        Returns:
            是否验证通过
        """
        try:
            actual_text = response_handler.get_text(response)
            result = bool(re.search(regex_pattern, actual_text))
            
            if not result:
                logger.warning(f"正则表达式验证失败: 响应文本不匹配 '{regex_pattern}'")
            return result
            
        except Exception as e:
            logger.error(f"正则表达式验证异常: {str(e)}")
            raise ApiTestException(f"正则表达式验证异常: {str(e)}")
    
    def validate_json_contains(self, response: object, expected_json: Dict[str, Any], strict: bool = False) -> bool:
        """
        验证JSON响应是否包含预期的数据
        
        Args:
            response: 响应对象
            expected_json: 期望包含的JSON数据
            strict: 是否严格匹配（键值完全相同）
            
        Returns:
            是否验证通过
        """
        try:
            actual_json = response_handler.get_json(response)
            
            # 如果严格匹配，直接比较
            if strict:
                result = actual_json == expected_json
                if not result:
                    logger.warning(f"JSON严格匹配失败: 实际与期望不相同")
                return result
            
            # 否则，检查expected_json是否是actual_json的子集
            return self._dict_contains(actual_json, expected_json)
            
        except Exception as e:
            logger.error(f"JSON内容验证异常: {str(e)}")
            raise ApiTestException(f"JSON内容验证异常: {str(e)}")
    
    def _dict_contains(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """
        检查actual字典是否包含expected字典的所有键值对
        
        Args:
            actual: 实际字典
            expected: 期望字典
            
        Returns:
            是否包含
        """
        for key, expected_value in expected.items():
            if key not in actual:
                logger.warning(f"JSON内容验证失败: 缺少键 '{key}'")
                return False
            
            actual_value = actual[key]
            
            # 如果值是字典，递归检查
            if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                if not self._dict_contains(actual_value, expected_value):
                    return False
            # 如果值是列表，特殊处理
            elif isinstance(expected_value, list) and isinstance(actual_value, list):
                if not self._list_contains(actual_value, expected_value):
                    return False
            # 其他情况直接比较
            elif actual_value != expected_value:
                logger.warning(f"JSON内容验证失败: 键 '{key}' 的值不匹配，期望 {expected_value}，实际 {actual_value}")
                return False
        
        return True
    
    def _list_contains(self, actual: List[Any], expected: List[Any]) -> bool:
        """
        检查actual列表是否包含expected列表的所有元素
        
        Args:
            actual: 实际列表
            expected: 期望列表
            
        Returns:
            是否包含
        """
        # 简单实现：检查expected中的每个元素是否在actual中
        # 更复杂的实现可能需要考虑元素顺序和深层结构
        for item in expected:
            if isinstance(item, dict):
                # 检查是否存在一个字典包含item的所有键值对
                found = False
                for actual_item in actual:
                    if isinstance(actual_item, dict) and self._dict_contains(actual_item, item):
                        found = True
                        break
                if not found:
                    logger.warning(f"JSON内容验证失败: 列表中未找到包含 {item} 的元素")
                    return False
            else:
                # 简单类型直接检查
                if item not in actual:
                    logger.warning(f"JSON内容验证失败: 列表中未找到元素 {item}")
                    return False
        
        return True
    
    def validate_header(self, response: object, header_name: str, expected_value: Optional[str] = None) -> bool:
        """
        验证响应头
        
        Args:
            response: 响应对象
            header_name: header名称（不区分大小写）
            expected_value: 期望的值，如果为None则只检查存在性
            
        Returns:
            是否验证通过
        """
        try:
            headers = response_handler.get_headers(response)
            header_name_lower = header_name.lower()
            
            # 查找header（不区分大小写）
            actual_value = None
            for key, value in headers.items():
                if key.lower() == header_name_lower:
                    actual_value = value
                    break
            
            # 如果只检查存在性
            if expected_value is None:
                result = actual_value is not None
                if not result:
                    logger.warning(f"Header验证失败: 未找到header '{header_name}'")
                return result
            
            # 否则检查值
            result = actual_value == expected_value
            if not result:
                logger.warning(f"Header验证失败: header '{header_name}' 的值不匹配，期望 '{expected_value}'，实际 '{actual_value}'")
            return result
            
        except Exception as e:
            logger.error(f"Header验证异常: {str(e)}")
            raise ApiTestException(f"Header验证异常: {str(e)}")
    
    def validate_cookie(self, response: object, cookie_name: str, expected_value: Optional[str] = None) -> bool:
        """
        验证响应cookie
        
        Args:
            response: 响应对象
            cookie_name: cookie名称
            expected_value: 期望的值，如果为None则只检查存在性
            
        Returns:
            是否验证通过
        """
        try:
            cookies = response_handler.extract_cookies(response)
            
            # 如果只检查存在性
            if expected_value is None:
                result = cookie_name in cookies
                if not result:
                    logger.warning(f"Cookie验证失败: 未找到cookie '{cookie_name}'")
                return result
            
            # 否则检查值
            result = cookies.get(cookie_name) == expected_value
            if not result:
                logger.warning(f"Cookie验证失败: cookie '{cookie_name}' 的值不匹配，期望 '{expected_value}'，实际 '{cookies.get(cookie_name)}'")
            return result
            
        except Exception as e:
            logger.error(f"Cookie验证异常: {str(e)}")
            raise ApiTestException(f"Cookie验证异常: {str(e)}")
    
    def validate_multiple(self, response: object, validations: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        执行多个验证
        
        Args:
            response: 响应对象
            validations: 验证配置列表
            
        Returns:
            验证结果字典，键为名称，值为是否通过
        """
        results = {}
        
        for validation in validations:
            try:
                name = validation['name']
                validation_type = validation['type']
                
                # 根据验证类型执行相应的验证
                if validation_type == 'status_code':
                    expected = validation['expected']
                    results[name] = self.validate_status_code(response, expected)
                elif validation_type == 'response_time':
                    max_time = validation['max_time_ms']
                    results[name] = self.validate_response_time(response, max_time)
                elif validation_type == 'contains_text':
                    text = validation['text']
                    case_sensitive = validation.get('case_sensitive', True)
                    results[name] = self.validate_contains_text(response, text, case_sensitive)
                elif validation_type == 'matches_regex':
                    pattern = validation['pattern']
                    results[name] = self.validate_matches_regex(response, pattern)
                elif validation_type == 'json_contains':
                    expected_json = validation['expected_json']
                    strict = validation.get('strict', False)
                    results[name] = self.validate_json_contains(response, expected_json, strict)
                elif validation_type == 'header':
                    header_name = validation['header_name']
                    expected_value = validation.get('expected_value')
                    results[name] = self.validate_header(response, header_name, expected_value)
                elif validation_type == 'cookie':
                    cookie_name = validation['cookie_name']
                    expected_value = validation.get('expected_value')
                    results[name] = self.validate_cookie(response, cookie_name, expected_value)
                else:
                    logger.error(f"未知的验证类型: {validation_type}")
                    results[name] = False
                    
            except Exception as e:
                logger.error(f"多验证执行失败: {validation.get('name')}, 错误: {str(e)}")
                results[validation.get('name', 'unknown')] = False
        
        return results
    
    def assert_validation(self, response: object, validation_type: str, *args, **kwargs) -> None:
        """
        断言验证，如果验证失败则抛出异常
        
        Args:
            response: 响应对象
            validation_type: 验证类型
            *args: 位置参数
            **kwargs: 关键字参数
        """
        validation_methods = {
            'status_code': self.validate_status_code,
            'response_time': self.validate_response_time,
            'contains_text': self.validate_contains_text,
            'matches_regex': self.validate_matches_regex,
            'json_contains': self.validate_json_contains,
            'header': self.validate_header,
            'cookie': self.validate_cookie
        }
        
        if validation_type not in validation_methods:
            raise ApiTestException(f"不支持的断言验证类型: {validation_type}")
        
        # 执行验证
        result = validation_methods[validation_type](response, *args, **kwargs)
        
        # 如果验证失败，抛出异常
        if not result:
            raise ApiTestException(f"断言验证失败: {validation_type}")


# 创建全局响应验证器实例
response_validator = ResponseValidator()