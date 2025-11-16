"""
异常类模块
定义框架中使用的自定义异常类
"""


class ApiTestException(Exception):
    """
    API测试基础异常类
    """
    
    def __init__(self, message: str, cause: Exception = None):
        """
        初始化异常
        
        Args:
            message: 异常信息
            cause: 原始异常
        """
        self.message = message
        self.cause = cause
        super().__init__(message)
        
        if cause:
            self.__cause__ = cause


class ConfigException(ApiTestException):
    """
    配置相关异常
    """
    pass


class RequestException(ApiTestException):
    """
    请求相关异常
    """
    pass


class ResponseException(ApiTestException):
    """
    响应相关异常
    """
    pass


class ValidationException(ApiTestException):
    """
    验证相关异常
    """
    pass


class AuthException(ApiTestException):
    """
    认证相关异常
    """
    pass


class ExtractionException(ApiTestException):
    """
    数据提取相关异常
    """
    pass


class TestCaseException(ApiTestException):
    """
    测试用例相关异常
    """
    pass


class AssertionError(ApiTestException):
    """
    断言错误异常
    """
    pass