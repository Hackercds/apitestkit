"""
API测试工具包的异常类定义

该模块包含ApiTestKit中使用的所有自定义异常类，用于提供清晰的错误信息和异常处理机制。
"""


class ApiTestKitError(Exception):
    """
    API测试工具包的基础异常类
    
    所有ApiTestKit特定的异常都应该继承自这个类，以提供一致的异常处理机制。
    """
    def __init__(self, message: str = "ApiTestKit基础错误"):
        self.message = message
        super().__init__(self.message)


class RequestError(ApiTestKitError):
    """
    HTTP请求相关的异常
    
    当发送HTTP请求失败或请求参数无效时抛出。
    """
    def __init__(self, message: str = "请求失败", url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        if url:
            message = f"请求 '{url}' 失败: {message}"
        if status_code:
            message = f"{message} (状态码: {status_code})"
        super().__init__(message)


class ResponseError(ApiTestKitError):
    """
    HTTP响应相关的异常
    
    当处理HTTP响应失败或响应内容不符合预期时抛出。
    """
    def __init__(self, message: str = "响应处理失败", url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        if url:
            message = f"响应 '{url}' 处理失败: {message}"
        if status_code:
            message = f"{message} (状态码: {status_code})"
        super().__init__(message)


class AssertionError(ApiTestKitError):
    """
    断言失败的异常
    
    当测试断言失败时抛出，提供详细的失败信息。
    """
    def __init__(self, message: str = "断言失败", expected=None, actual=None):
        self.expected = expected
        self.actual = actual
        detail_message = f"{message}"
        if expected is not None or actual is not None:
            detail_message += f"\n期望: {expected}\n实际: {actual}"
        super().__init__(detail_message)


class ConfigurationError(ApiTestKitError):
    """
    配置相关的异常
    
    当配置无效、缺失或格式错误时抛出。
    """
    def __init__(self, message: str = "配置错误", config_key: str = None):
        self.config_key = config_key
        if config_key:
            message = f"配置项 '{config_key}' 错误: {message}"
        super().__init__(message)


class DataStorageError(ApiTestKitError):
    """
    数据存储相关的异常
    
    当数据存储或检索操作失败时抛出。
    """
    def __init__(self, message: str = "数据存储操作失败", operation: str = None):
        self.operation = operation
        if operation:
            message = f"数据存储操作 '{operation}' 失败: {message}"
        super().__init__(message)


class ReportGenerationError(ApiTestKitError):
    """
    报告生成相关的异常
    
    当测试报告生成失败时抛出。
    """
    def __init__(self, message: str = "报告生成失败", report_type: str = None):
        self.report_type = report_type
        if report_type:
            message = f"{report_type} 报告生成失败: {message}"
        super().__init__(message)


class ValidationError(ApiTestKitError):
    """
    数据验证相关的异常
    
    当请求数据或响应数据验证失败时抛出。
    """
    def __init__(self, message: str = "数据验证失败", validation_errors: list = None):
        self.validation_errors = validation_errors or []
        if validation_errors:
            error_details = "\n".join([f"- {err}" for err in validation_errors])
            message = f"{message}:\n{error_details}"
        super().__init__(message)


class TimeoutError(ApiTestKitError):
    """
    超时相关的异常
    
    当操作超时（如请求超时）时抛出。
    """
    def __init__(self, message: str = "操作超时", timeout: float = None):
        self.timeout = timeout
        if timeout:
            message = f"{message} (超时时间: {timeout}秒)"
        super().__init__(message)