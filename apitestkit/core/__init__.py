"""
核心功能模块

提供配置管理、日志管理等基础功能。
"""

from apitestkit.core.logger import logger_manager
from apitestkit.core.config import config_manager

__all__ = ['logger_manager', 'config_manager']