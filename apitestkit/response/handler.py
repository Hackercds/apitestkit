"""
响应处理器模块
提供HTTP响应的统一处理和解析功能
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Union, List
import logging
import re

from apitestkit.core.logger import logger_manager
from apitestkit.exception.exceptions import ApiTestException

# 获取日志记录器
logger = logger_manager.get_logger(__name__)


class ResponseHandler:
    """
    响应处理器，提供统一的响应解析和处理功能
    """
    
    def get_json(self, response: Union[object, str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        从响应中获取JSON数据
        
        Args:
            response: 响应对象、字符串或字典
            
        Returns:
            JSON数据字典
        """
        try:
            # 如果已经是字典，直接返回
            if isinstance(response, dict):
                return response
            
            # 如果是响应对象，尝试从text或content中解析
            if hasattr(response, 'json') and callable(response.json):
                try:
                    return response.json()
                except (ValueError, json.JSONDecodeError):
                    # 如果response.json()失败，尝试从text解析
                    if hasattr(response, 'text'):
                        return self._parse_json(response.text)
                    elif hasattr(response, 'content'):
                        return self._parse_json(response.content.decode('utf-8'))
            
            # 如果是字符串，直接解析
            if isinstance(response, str):
                return self._parse_json(response)
            
            # 如果是字节串，解码后解析
            if isinstance(response, bytes):
                return self._parse_json(response.decode('utf-8'))
            
            raise ApiTestException("无法从响应中解析JSON数据")
            
        except Exception as e:
            logger.error(f"JSON解析失败: {str(e)}")
            raise ApiTestException(f"JSON解析失败: {str(e)}")
    
    def _parse_json(self, json_str: str) -> Dict[str, Any]:
        """
        解析JSON字符串
        
        Args:
            json_str: JSON字符串
            
        Returns:
            解析后的字典
        """
        try:
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            raise ApiTestException(f"JSON字符串解析失败: {str(e)}")
    
    def get_xml(self, response: Union[object, str]) -> ET.Element:
        """
        从响应中获取XML数据
        
        Args:
            response: 响应对象或字符串
            
        Returns:
            XML元素对象
        """
        try:
            # 如果是响应对象，获取text
            if hasattr(response, 'text'):
                xml_str = response.text
            elif hasattr(response, 'content'):
                xml_str = response.content.decode('utf-8')
            elif isinstance(response, str):
                xml_str = response
            else:
                raise ApiTestException("无法从响应中提取XML数据")
            
            return ET.fromstring(xml_str)
            
        except ET.ParseError as e:
            logger.error(f"XML解析失败: {str(e)}")
            raise ApiTestException(f"XML解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"XML处理失败: {str(e)}")
            raise ApiTestException(f"XML处理失败: {str(e)}")
    
    def get_text(self, response: Union[object, str]) -> str:
        """
        从响应中获取文本内容
        
        Args:
            response: 响应对象或字符串
            
        Returns:
            文本内容
        """
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'content'):
            try:
                return response.content.decode('utf-8')
            except UnicodeDecodeError:
                # 尝试其他编码
                try:
                    return response.content.decode('gbk')
                except UnicodeDecodeError:
                    # 最后返回字节串的repr
                    return repr(response.content)
        elif isinstance(response, str):
            return response
        elif isinstance(response, bytes):
            try:
                return response.decode('utf-8')
            except UnicodeDecodeError:
                return repr(response)
        else:
            return str(response)
    
    def get_headers(self, response: object) -> Dict[str, str]:
        """
        从响应中获取headers
        
        Args:
            response: 响应对象
            
        Returns:
            Headers字典
        """
        if hasattr(response, 'headers'):
            return dict(response.headers)
        return {}
    
    def get_status_code(self, response: object) -> int:
        """
        从响应中获取状态码
        
        Args:
            response: 响应对象
            
        Returns:
            状态码
        """
        if hasattr(response, 'status_code'):
            return response.status_code
        raise ApiTestException("无法从响应中获取状态码")
    
    def get_response_time(self, response: object) -> int:
        """
        从响应中获取响应时间（毫秒）
        
        Args:
            response: 响应对象
            
        Returns:
            响应时间（毫秒）
        """
        if hasattr(response, 'elapsed_ms'):
            return response.elapsed_ms
        elif hasattr(response, 'elapsed'):
            # 如果有elapsed属性但没有elapsed_ms，计算它
            return int(response.elapsed.total_seconds() * 1000)
        return 0
    
    def extract_cookies(self, response: object) -> Dict[str, str]:
        """
        从响应中提取cookies
        
        Args:
            response: 响应对象
            
        Returns:
            Cookies字典
        """
        if hasattr(response, 'cookies'):
            return dict(response.cookies)
        return {}
    
    def is_json_response(self, response: object) -> bool:
        """
        检查响应是否为JSON格式
        
        Args:
            response: 响应对象
            
        Returns:
            是否为JSON格式
        """
        # 检查Content-Type
        content_type = self.get_headers(response).get('Content-Type', '')
        if 'application/json' in content_type or 'application/javascript' in content_type:
            return True
        
        # 尝试解析JSON
        try:
            self.get_json(response)
            return True
        except:
            return False
    
    def is_xml_response(self, response: object) -> bool:
        """
        检查响应是否为XML格式
        
        Args:
            response: 响应对象
            
        Returns:
            是否为XML格式
        """
        # 检查Content-Type
        content_type = self.get_headers(response).get('Content-Type', '')
        if 'application/xml' in content_type or 'text/xml' in content_type:
            return True
        
        # 尝试解析XML
        try:
            self.get_xml(response)
            return True
        except:
            return False
    
    def get_content_type(self, response: object) -> str:
        """
        获取响应的Content-Type
        
        Args:
            response: 响应对象
            
        Returns:
            Content-Type字符串
        """
        return self.get_headers(response).get('Content-Type', '').split(';')[0].strip()
    
    def format_response(self, response: object) -> Dict[str, Any]:
        """
        格式化响应为统一的字典格式
        
        Args:
            response: 响应对象
            
        Returns:
            格式化后的响应字典
        """
        return {
            "status_code": self.get_status_code(response),
            "headers": self.get_headers(response),
            "cookies": self.extract_cookies(response),
            "response_time": self.get_response_time(response),
            "content_type": self.get_content_type(response),
            "text": self.get_text(response)
        }
    
    def save_response_to_file(self, response: object, file_path: str):
        """
        保存响应到文件
        
        Args:
            response: 响应对象
            file_path: 文件路径
        """
        try:
            content = self.get_text(response)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"响应已保存到文件: {file_path}")
        except Exception as e:
            logger.error(f"保存响应到文件失败: {str(e)}")
            raise ApiTestException(f"保存响应到文件失败: {str(e)}")


# 创建全局响应处理器实例
response_handler = ResponseHandler()