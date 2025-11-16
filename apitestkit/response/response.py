"""响应处理模块"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Generator, AsyncGenerator
from dataclasses import dataclass
from apitestkit.core.logger import logger_manager, create_user_logger


class ApiResponse:
    """
    API响应类，用于统一处理API响应数据
    """
    
    def __init__(self, status_code: int, headers: Dict[str, Any], content: bytes,
                 url: str = None, request_time: float = None, 
                 request_method: str = None, request_headers: Dict[str, Any] = None,
                 request_data: Any = None):
        """
        初始化API响应对象
        
        Args:
            status_code: HTTP状态码
            headers: 响应头
            content: 响应内容（字节）
            url: 请求URL
            request_time: 请求耗时（秒）
            request_method: 请求方法
            request_headers: 请求头
            request_data: 请求数据
        """
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.url = url
        self.request_time = request_time
        self.request_method = request_method
        self.request_headers = request_headers or {}
        self.request_data = request_data
        self._json_data = None
        self._text = None
        self._user_logger = create_user_logger("response_logger")
    
    @property
    def text(self) -> str:
        """
        获取响应文本内容
        
        Returns:
            str: 响应文本
        """
        if self._text is None:
            try:
                self._text = self.content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    self._text = self.content.decode('latin-1')
                except Exception as e:
                    self._user_logger.error(f"无法解码响应内容: {str(e)}")
                    self._text = str(self.content)
        return self._text
    
    @property
    def json(self) -> Dict[str, Any]:
        """
        获取JSON格式的响应内容
        
        Returns:
            Dict[str, Any]: JSON格式的响应数据
        
        Raises:
            ValueError: 如果响应不是有效的JSON
        """
        if self._json_data is None:
            try:
                self._json_data = json.loads(self.text)
            except json.JSONDecodeError as e:
                error_msg = f"响应内容不是有效的JSON: {str(e)}"
                self._user_logger.error(error_msg)
                raise ValueError(error_msg)
        return self._json_data
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将响应对象转换为字典
        
        Returns:
            Dict[str, Any]: 响应数据字典
        """
        return {
            'url': self.url,
            'method': self.request_method,
            'status_code': self.status_code,
            'headers': dict(self.headers),
            'request_headers': self.request_headers,
            'request_data': self.request_data,
            'request_time': self.request_time,
            'content': self.text
        }
    
    def get_header(self, name: str, default: Any = None) -> Any:
        """
        获取指定的响应头
        
        Args:
            name: 头名称
            default: 默认值
            
        Returns:
            Any: 头值或默认值
        """
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return default
    
    def has_header(self, name: str) -> bool:
        """
        检查响应是否包含指定的头
        
        Args:
            name: 头名称
            
        Returns:
            bool: 是否包含指定头
        """
        return any(key.lower() == name.lower() for key in self.headers)
    
    def __str__(self) -> str:
        """
        字符串表示
        """
        return f"ApiResponse(status_code={self.status_code}, url={self.url}, time={self.request_time}s)"
    
    def __repr__(self) -> str:
        """
        详细表示
        """
        return self.__str__()


class ApiStreamResponse:
    """
    API流式响应类，用于处理流式API响应
    """
    
    def __init__(self, url: str = None, request_method: str = None, 
                 request_headers: Dict[str, Any] = None, request_data: Any = None):
        """
        初始化流式响应对象
        
        Args:
            url: 请求URL
            request_method: 请求方法
            request_headers: 请求头
            request_data: 请求数据
        """
        self.url = url
        self.request_method = request_method
        self.request_headers = request_headers or {}
        self.request_data = request_data
        self._stream_content = []
        self._raw_stream_content = b''
        self.status_code = None
        self.headers = None
        self._user_logger = create_user_logger("stream_response_logger")
    
    def add_chunk(self, chunk: bytes) -> None:
        """
        添加一个流数据块
        
        Args:
            chunk: 数据块（字节）
        """
        if chunk:
            self._raw_stream_content += chunk
            try:
                text_chunk = chunk.decode('utf-8')
                self._stream_content.append(text_chunk)
            except UnicodeDecodeError:
                try:
                    text_chunk = chunk.decode('latin-1')
                    self._stream_content.append(text_chunk)
                except Exception as e:
                    self._user_logger.error(f"无法解码流数据块: {str(e)}")
                    # 存储原始字节
                    self._stream_content.append(str(chunk))
    
    @property
    def chunks(self) -> List[str]:
        """
        获取所有已接收的数据块
        
        Returns:
            List[str]: 数据块列表
        """
        return self._stream_content.copy()
    
    @property
    def content(self) -> str:
        """
        获取已接收的所有内容的合并文本
        
        Returns:
            str: 合并的文本内容
        """
        return ''.join(self._stream_content)
    
    @property
    def raw_content(self) -> bytes:
        """
        获取原始字节内容
        
        Returns:
            bytes: 原始字节内容
        """
        return self._raw_stream_content
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将流式响应对象转换为字典
        
        Returns:
            Dict[str, Any]: 响应数据字典
        """
        return {
            'url': self.url,
            'method': self.request_method,
            'status_code': self.status_code,
            'headers': dict(self.headers) if self.headers else None,
            'request_headers': self.request_headers,
            'request_data': self.request_data,
            'content': self.content,
            'chunks_count': len(self._stream_content)
        }
    
    def __str__(self) -> str:
        """
        字符串表示
        """
        return f"ApiStreamResponse(url={self.url}, chunks={len(self._stream_content)})"
    
    def __repr__(self) -> str:
        """
        详细表示
        """
        return self.__str__()