"""请求模块初始化文件"""

from apitestkit.request.http_client import HttpClient
from apitestkit.request.auth.auth_manager import AuthManager

__all__ = ['HttpClient', 'AuthManager']