"""
HTTP客户端模块
提供统一的HTTP请求接口，支持各种请求方法和功能
"""

import requests
import time
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
import json
import logging

from apitestkit.core.config import config_manager
from apitestkit.core.logger import get_framework_logger
from apitestkit.request.auth.auth_manager import auth_manager
from apitestkit.exception.exceptions import ApiTestException

# 获取日志记录器
logger = get_framework_logger(__name__)


class HttpClient:
    """
    HTTP客户端类，封装requests库，提供统一的HTTP请求接口
    """
    
    def __init__(self):
        """初始化HTTP客户端"""
        self._base_url = config_manager.get("base_url", "")
        self._timeout = config_manager.get("timeout", 30)
        self._retry_enabled = config_manager.get("retry_enabled", False)
        self._retry_config = {
            "max_retries": config_manager.get("max_retries", 3),
            "delay": config_manager.get("retry_delay", 1),
            "status_codes": config_manager.get("retry_status_codes", [500, 502, 503, 504])
        }
        self._session = self._create_session()
    
    def _create_session(self):
        """创建requests会话"""
        session = requests.Session()
        
        # 配置重试策略
        if self._retry_enabled:
            retry_strategy = Retry(
                total=self._retry_config["max_retries"],
                status_forcelist=self._retry_config["status_codes"],
                allowed_methods=["GET", "POST", "PUT", "DELETE"],
                backoff_factor=self._retry_config["delay"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        
        return session
    
    def _prepare_url(self, url: str) -> str:
        """准备请求URL"""
        if not url.startswith("http") and self._base_url:
            return f"{self._base_url.rstrip('/')}/{url.lstrip('/')}"
        return url
    
    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求日志"""
        # 过滤敏感信息
        filtered_kwargs = self._filter_sensitive_data(kwargs)
        logger.info(f"发送{method}请求到: {url}")
        logger.debug(f"请求参数: {json.dumps(filtered_kwargs, ensure_ascii=False, indent=2)}")
    
    def _log_response(self, response: requests.Response):
        """记录响应日志"""
        logger.info(f"收到响应，状态码: {response.status_code}")
        # 尝试记录响应内容，但限制大小
        if len(response.content) < 10000:  # 限制响应日志大小
            try:
                response_data = response.json()
                logger.debug(f"响应内容: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            except ValueError:
                logger.debug(f"响应内容: {response.text[:500]}..." if len(response.text) > 500 else f"响应内容: {response.text}")
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤敏感信息"""
        sensitive_keys = ["password", "token", "secret", "key"]
        filtered = data.copy()
        
        # 过滤headers中的敏感信息
        if "headers" in filtered:
            for key in list(filtered["headers"].keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    filtered["headers"][key] = "******"
        
        # 过滤auth中的敏感信息
        if "auth" in filtered:
            filtered["auth"] = "******"
        
        # 过滤json中的敏感信息
        if "json" in filtered and isinstance(filtered["json"], dict):
            for key in list(filtered["json"].keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    filtered["json"][key] = "******"
        
        return filtered
    
    def _handle_streaming_response(self, response: requests.Response, stream_handler: Callable) -> requests.Response:
        """处理流式响应"""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                continue_stream = stream_handler(chunk)
                if not continue_stream:
                    break
        return response
    
    def _prepare_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """准备请求参数"""
        # 设置超时
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._timeout
        
        # 应用认证
        if kwargs.pop("use_auth", False):
            auth_config = auth_manager.get_auth_config(method, url, kwargs)
            kwargs.update(auth_config)
        
        return kwargs
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: 请求方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
        """
        try:
            # 准备URL和请求参数
            full_url = self._prepare_url(url)
            request_kwargs = self._prepare_request(method, full_url, **kwargs)
            
            # 记录请求
            self._log_request(method, full_url, **kwargs)
            
            # 发送请求
            start_time = time.time()
            response = self._session.request(method, full_url, **request_kwargs)
            # 同时设置elapsed_ms（毫秒）和response_time（秒）以确保与断言方法兼容
            response.elapsed_ms = int((time.time() - start_time) * 1000)
            response.response_time = (time.time() - start_time)
            
            # 记录响应
            self._log_response(response)
            
            # 处理流式响应
            if kwargs.get("stream", False) and "stream_handler" in kwargs:
                response = self._handle_streaming_response(response, kwargs["stream_handler"])
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            raise ApiTestException(f"HTTP请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"请求处理异常: {str(e)}")
            raise ApiTestException(f"请求处理异常: {str(e)}")
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """发送GET请求"""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """发送POST请求"""
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """发送PUT请求"""
        return self.request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """发送DELETE请求"""
        return self.request("DELETE", url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> requests.Response:
        """发送PATCH请求"""
        return self.request("PATCH", url, **kwargs)
    
    def head(self, url: str, **kwargs) -> requests.Response:
        """发送HEAD请求"""
        return self.request("HEAD", url, **kwargs)
    
    def options(self, url: str, **kwargs) -> requests.Response:
        """发送OPTIONS请求"""
        return self.request("OPTIONS", url, **kwargs)
    
    def upload_file(self, url: str, file_path: Union[str, Path], file_key: str = "file", **kwargs) -> requests.Response:
        """
        上传文件
        
        Args:
            url: 请求URL
            file_path: 文件路径
            file_key: 表单字段名
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ApiTestException(f"文件不存在: {file_path}")
        
        files = {file_key: (file_path.name, open(file_path, 'rb'))}
        try:
            return self.post(url, files=files, **kwargs)
        finally:
            # 确保文件被关闭
            for f in files.values():
                if hasattr(f, 'close') and callable(f.close):
                    f.close()
    
    def upload_files(self, url: str, file_paths: List[Union[str, Path]], file_key: str = "files", **kwargs) -> requests.Response:
        """
        批量上传文件
        
        Args:
            url: 请求URL
            file_paths: 文件路径列表
            file_key: 表单字段名
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
        """
        files = []
        try:
            for file_path in file_paths:
                path = Path(file_path)
                if not path.exists():
                    raise ApiTestException(f"文件不存在: {path}")
                files.append((file_key, (path.name, open(path, 'rb'))))
            
            return self.post(url, files=files, **kwargs)
        finally:
            # 确保所有文件被关闭
            for _, f in files:
                if hasattr(f, 'close') and callable(f.close):
                    f.close()


# 创建全局HTTP客户端实例
http_client = HttpClient()