"""
数据提取器模块
提供从响应中提取特定数据的功能，支持多种提取方式
"""

import re
import jsonpath_ng
import xml.etree.ElementTree as ET
from typing import Any, Optional, Union, List, Dict
import logging

from apitestkit.core.logger import logger_manager
from apitestkit.exception.exceptions import ApiTestException
from apitestkit.response.handler import response_handler

# 获取日志记录器
logger = logger_manager.get_logger(__name__)


class DataExtractor:
    """
    数据提取器，提供多种数据提取方式
    """
    
    def extract_by_jsonpath(self, data: Union[Dict[str, Any], list], jsonpath_expr: str) -> List[Any]:
        """
        使用JSONPath从数据中提取值
        
        Args:
            data: 字典或列表数据
            jsonpath_expr: JSONPath表达式
            
        Returns:
            提取的值列表
        """
        try:
            # 编译JSONPath表达式
            expression = jsonpath_ng.parse(jsonpath_expr)
            # 查找所有匹配项
            matches = expression.find(data)
            # 返回所有匹配的值
            return [match.value for match in matches]
            
        except Exception as e:
            logger.error(f"JSONPath提取失败: {jsonpath_expr}, 错误: {str(e)}")
            raise ApiTestException(f"JSONPath提取失败: {jsonpath_expr}, 错误: {str(e)}")
    
    def extract_by_regex(self, text: str, regex_pattern: str, group: Optional[int] = None) -> List[str]:
        """
        使用正则表达式从文本中提取值
        
        Args:
            text: 文本内容
            regex_pattern: 正则表达式
            group: 提取的组索引，如果为None则提取全部匹配
            
        Returns:
            提取的值列表
        """
        try:
            # 编译正则表达式
            pattern = re.compile(regex_pattern)
            # 查找所有匹配项
            matches = pattern.findall(text)
            
            # 根据group参数返回对应的值
            if group is not None:
                # 确保matches中的元素是元组
                result = []
                for match in matches:
                    if isinstance(match, tuple) and len(match) > group:
                        result.append(match[group])
                    elif group == 0:
                        result.append(match)
                return result
            
            return matches
            
        except Exception as e:
            logger.error(f"正则表达式提取失败: {regex_pattern}, 错误: {str(e)}")
            raise ApiTestException(f"正则表达式提取失败: {regex_pattern}, 错误: {str(e)}")
    
    def extract_by_xpath(self, xml_element: ET.Element, xpath_expr: str) -> List[Any]:
        """
        使用XPath从XML元素中提取值
        
        Args:
            xml_element: XML元素
            xpath_expr: XPath表达式
            
        Returns:
            提取的元素或值列表
        """
        try:
            # 查找所有匹配的元素
            elements = xml_element.findall(xpath_expr)
            # 返回元素列表或元素文本
            result = []
            for elem in elements:
                if elem.text is not None:
                    result.append(elem.text.strip())
                else:
                    result.append(elem)
            return result
            
        except Exception as e:
            logger.error(f"XPath提取失败: {xpath_expr}, 错误: {str(e)}")
            raise ApiTestException(f"XPath提取失败: {xpath_expr}, 错误: {str(e)}")
    
    def extract_by_key(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        通过键名从字典中提取值
        
        Args:
            data: 字典数据
            key: 键名
            default: 默认值
            
        Returns:
            提取的值或默认值
        """
        try:
            # 支持嵌套键名，如 'user.name'
            keys = key.split('.')
            value = data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"键值提取失败: {key}, 错误: {str(e)}")
            return default
    
    def extract_from_response(self, response: object, extractor_type: str, extractor_expr: str) -> List[Any]:
        """
        从响应中提取数据
        
        Args:
            response: 响应对象
            extractor_type: 提取器类型，支持 'jsonpath', 'regex', 'xpath', 'key'
            extractor_expr: 提取表达式
            
        Returns:
            提取的值列表
        """
        try:
            # 根据提取器类型选择不同的提取方法
            if extractor_type.lower() == 'jsonpath':
                # 确保响应是JSON格式
                data = response_handler.get_json(response)
                return self.extract_by_jsonpath(data, extractor_expr)
                
            elif extractor_type.lower() == 'regex':
                # 获取响应文本
                text = response_handler.get_text(response)
                return self.extract_by_regex(text, extractor_expr)
                
            elif extractor_type.lower() == 'xpath':
                # 确保响应是XML格式
                xml_element = response_handler.get_xml(response)
                return self.extract_by_xpath(xml_element, extractor_expr)
                
            elif extractor_type.lower() == 'key':
                # 确保响应是JSON格式
                data = response_handler.get_json(response)
                value = self.extract_by_key(data, extractor_expr)
                return [value] if value is not None else []
                
            else:
                raise ApiTestException(f"不支持的提取器类型: {extractor_type}")
                
        except Exception as e:
            logger.error(f"从响应提取数据失败: {extractor_type}, {extractor_expr}, 错误: {str(e)}")
            raise ApiTestException(f"从响应提取数据失败: {extractor_type}, {extractor_expr}, 错误: {str(e)}")
    
    def extract_cookie(self, response: object, cookie_name: str) -> Optional[str]:
        """
        从响应中提取指定的cookie
        
        Args:
            response: 响应对象
            cookie_name: cookie名称
            
        Returns:
            cookie值或None
        """
        try:
            cookies = response_handler.extract_cookies(response)
            return cookies.get(cookie_name)
        except Exception as e:
            logger.error(f"提取Cookie失败: {cookie_name}, 错误: {str(e)}")
            return None
    
    def extract_header(self, response: object, header_name: str) -> Optional[str]:
        """
        从响应中提取指定的header
        
        Args:
            response: 响应对象
            header_name: header名称（不区分大小写）
            
        Returns:
            header值或None
        """
        try:
            headers = response_handler.get_headers(response)
            # 不区分大小写查找header
            header_name_lower = header_name.lower()
            for key, value in headers.items():
                if key.lower() == header_name_lower:
                    return value
            return None
        except Exception as e:
            logger.error(f"提取Header失败: {header_name}, 错误: {str(e)}")
            return None
    
    def extract_multiple(self, response: object, extract_configs: List[Dict[str, str]]) -> Dict[str, List[Any]]:
        """
        从响应中提取多个数据
        
        Args:
            response: 响应对象
            extract_configs: 提取配置列表，每个配置包含 'name', 'type', 'expr'
            
        Returns:
            提取结果字典，键为名称，值为提取的值列表
        """
        results = {}
        
        for config in extract_configs:
            try:
                name = config['name']
                extractor_type = config['type']
                extractor_expr = config['expr']
                
                # 提取数据
                results[name] = self.extract_from_response(response, extractor_type, extractor_expr)
                
            except Exception as e:
                logger.error(f"多数据提取失败: {config.get('name')}, 错误: {str(e)}")
                results[config.get('name', 'unknown')] = []
        
        return results
    
    def extract_first(self, response: object, extractor_type: str, extractor_expr: str, default: Any = None) -> Any:
        """
        从响应中提取第一个匹配的值
        
        Args:
            response: 响应对象
            extractor_type: 提取器类型
            extractor_expr: 提取表达式
            default: 默认值
            
        Returns:
            第一个提取的值或默认值
        """
        results = self.extract_from_response(response, extractor_type, extractor_expr)
        return results[0] if results else default


# 创建全局数据提取器实例
data_extractor = DataExtractor()