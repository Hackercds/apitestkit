"""
认证管理器模块
提供多种认证方式的支持和管理
"""

import hmac
import hashlib
import time
import base64
from typing import Dict, Any, Optional, Union
import requests
from pathlib import Path
import json
import logging

from apitestkit.core.logger import get_framework_logger
from apitestkit.exception.exceptions import ApiTestException

# 获取日志记录器
logger = get_framework_logger(__name__)


class AuthManager:
    """
    认证管理器，支持多种认证方式
    """
    
    # 支持的认证类型
    AUTH_TYPES = {
        "basic": "basic_auth",
        "bearer": "bearer_auth",
        "hmac256": "hmac256_auth",
        "api_key": "api_key_auth"
    }
    
    def __init__(self):
        """初始化认证管理器"""
        self._default_auth_type = None
        self._default_auth_config = {}
        self._auth_configs = {}
        self._auth_cache = {}
    
    def set_default_auth(self, auth_type: str, config: Dict[str, Any]):
        """
        设置默认认证策略
        
        Args:
            auth_type: 认证类型
            config: 认证配置
        """
        if auth_type not in self.AUTH_TYPES:
            raise ApiTestException(f"不支持的认证类型: {auth_type}")
        
        self._default_auth_type = auth_type
        self._default_auth_config = config.copy()
        logger.info(f"已设置默认认证类型: {auth_type}")
    
    def add_auth_config(self, name: str, auth_type: str, config: Dict[str, Any]):
        """
        添加命名认证配置
        
        Args:
            name: 配置名称
            auth_type: 认证类型
            config: 认证配置
        """
        if auth_type not in self.AUTH_TYPES:
            raise ApiTestException(f"不支持的认证类型: {auth_type}")
        
        self._auth_configs[name] = {
            "type": auth_type,
            "config": config.copy()
        }
        logger.info(f"已添加认证配置: {name} ({auth_type})")
    
    def get_auth_config(self, method: str, url: str, request_params: Dict[str, Any] = None,
                       auth_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取认证配置
        
        Args:
            method: 请求方法
            url: 请求URL
            request_params: 请求参数
            auth_name: 认证配置名称
            
        Returns:
            应用了认证的请求参数
        """
        if auth_name:
            if auth_name not in self._auth_configs:
                raise ApiTestException(f"认证配置不存在: {auth_name}")
            
            auth_type = self._auth_configs[auth_name]["type"]
            auth_config = self._auth_configs[auth_name]["config"]
        elif self._default_auth_type:
            auth_type = self._default_auth_type
            auth_config = self._default_auth_config
        else:
            raise ApiTestException("未设置默认认证策略")
        
        # 获取认证方法
        auth_method_name = self.AUTH_TYPES[auth_type]
        auth_method = getattr(self, auth_method_name)
        
        # 应用认证
        return auth_method(method, url, request_params or {}, auth_config)
    
    def basic_auth(self, method: str, url: str, request_params: Dict[str, Any],
                   config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic认证
        
        Args:
            method: 请求方法
            url: 请求URL
            request_params: 请求参数
            config: 认证配置
            
        Returns:
            更新后的请求参数
        """
        username = config.get("username")
        password = config.get("password")
        
        if not username or not password:
            raise ApiTestException("Basic认证需要username和password")
        
        # 设置认证参数
        return {
            "auth": (username, password)
        }
    
    def bearer_auth(self, method: str, url: str, request_params: Dict[str, Any],
                    config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bearer Token认证
        
        Args:
            method: 请求方法
            url: 请求URL
            request_params: 请求参数
            config: 认证配置
            
        Returns:
            更新后的请求参数
        """
        token = config.get("token")
        
        if not token:
            raise ApiTestException("Bearer认证需要token")
        
        # 更新或创建headers
        headers = request_params.get("headers", {}).copy()
        headers["Authorization"] = f"Bearer {token}"
        
        return {
            "headers": headers
        }
    
    def hmac256_auth(self, method: str, url: str, request_params: Dict[str, Any],
                     config: Dict[str, Any]) -> Dict[str, Any]:
        """
        HMAC256认证
        
        Args:
            method: 请求方法
            url: 请求URL
            request_params: 请求参数
            config: 认证配置
            
        Returns:
            更新后的请求参数
        """
        api_key = config.get("api_key")
        secret_key = config.get("secret_key")
        
        if not api_key or not secret_key:
            raise ApiTestException("HMAC256认证需要api_key和secret_key")
        
        # 生成时间戳
        timestamp = str(int(time.time() * 1000))
        
        # 构建签名字符串
        signature_string = f"{method}{url}{timestamp}"
        
        # 如果启用了文件MD5参与签名
        if config.get("enable_file_md5", False) and "files" in request_params:
            # 这里简化处理，实际应计算文件MD5
            signature_string += "file_md5"
        
        # 添加请求体（如果有）
        if "json" in request_params:
            body_str = json.dumps(request_params["json"], sort_keys=True)
            signature_string += body_str
        
        # 生成HMAC签名
        signature = hmac.new(
            secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 更新headers
        headers = request_params.get("headers", {}).copy()
        headers["X-API-Key"] = api_key
        headers["X-Timestamp"] = timestamp
        headers["X-Signature"] = signature
        
        return {
            "headers": headers
        }
    
    def api_key_auth(self, method: str, url: str, request_params: Dict[str, Any],
                     config: Dict[str, Any]) -> Dict[str, Any]:
        """
        API Key认证
        
        Args:
            method: 请求方法
            url: 请求URL
            request_params: 请求参数
            config: 认证配置
            
        Returns:
            更新后的请求参数
        """
        api_key = config.get("api_key")
        header_name = config.get("header_name", "X-API-Key")
        
        if not api_key:
            raise ApiTestException("API Key认证需要api_key")
        
        # 更新headers
        headers = request_params.get("headers", {}).copy()
        headers[header_name] = api_key
        
        return {
            "headers": headers
        }
    
    def clear_cache(self):
        """清空认证缓存"""
        self._auth_cache.clear()
        logger.info("已清空认证缓存")
    
    def clear_all(self):
        """清除所有认证配置"""
        self._default_auth_type = None
        self._default_auth_config = {}
        self._auth_configs = {}
        self.clear_cache()
        logger.info("已清除所有认证配置")


# 创建全局认证管理器实例
auth_manager = AuthManager()