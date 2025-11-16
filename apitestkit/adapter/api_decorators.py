"""
API装饰器模块

提供装饰器风格的API测试功能，简化测试代码编写。
"""

import functools
import time
import re
import requests
from apitestkit.core.logger import logger_manager
from apitestkit.core.config import config_manager


# 存储测试用例结果
_test_results = {}


class TestResult:
    """
    测试结果类
    """
    def __init__(self):
        self.success = True
        self.error = None
        self.response = None
        self.response_time = 0
        self.variables = {}


def api_test(func):
    """
    API测试装饰器，用于标记测试函数
    
    Args:
        func: 测试函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        test_name = func.__name__
        logger_manager.info(f"开始测试: {test_name}")
        
        # 初始化测试结果
        result = TestResult()
        _test_results[test_name] = result
        
        try:
            # 执行测试函数
            start_time = time.time()
            result.variables = func(*args, **kwargs) or {}
            result.response_time = (time.time() - start_time) * 1000
            
            logger_manager.info(f"测试成功: {test_name}, 耗时: {result.response_time:.2f}ms")
        except Exception as e:
            result.success = False
            result.error = str(e)
            logger_manager.error(f"测试失败: {test_name}, 错误: {str(e)}")
            raise
        
        return result.variables
    
    # 添加标记，便于识别
    wrapper._is_api_test = True
    return wrapper


def _make_http_request(method, url, **kwargs):
    """
    发送HTTP请求的内部函数
    
    Args:
        method: HTTP方法
        url: 请求URL
        **kwargs: 其他请求参数
        
    Returns:
        tuple: (response, response_time)
    """
    # 从配置获取基础设置
    base_url = config_manager.get('base_url', '')
    timeout = config_manager.get('default_timeout', 30)
    verify_ssl = config_manager.get('verify_ssl', True)
    proxies = config_manager.get('proxy', None)
    headers = config_manager.get('headers', {}).copy()
    
    # 合并用户提供的请求头
    if 'headers' in kwargs:
        headers.update(kwargs['headers'])
        kwargs['headers'] = headers
    else:
        kwargs['headers'] = headers
    
    # 设置默认超时
    if 'timeout' not in kwargs:
        kwargs['timeout'] = timeout
    
    # 设置SSL验证
    if 'verify' not in kwargs:
        kwargs['verify'] = verify_ssl
    
    # 设置代理
    if proxies and 'proxies' not in kwargs:
        kwargs['proxies'] = proxies
    
    # 构建完整URL
    full_url = url if url.startswith(('http://', 'https://')) else base_url + url
    
    # 记录请求日志
    request_data = kwargs.get('json', kwargs.get('data', None))
    request_params = kwargs.get('params', None)
    logger_manager.log_request(method, full_url, headers=headers, params=request_params, json_data=request_data)
    
    # 发送请求
    start_time = time.time()
    try:
        response = requests.request(method, full_url, **kwargs)
        response_time = (time.time() - start_time) * 1000
        
        # 记录响应日志
        logger_manager.log_response(response.status_code, response_time, text=response.text)
        
        return response, response_time
    except requests.exceptions.RequestException as e:
        logger_manager.error(f"请求失败: {str(e)}")
        raise


def http_get(url, **kwargs):
    """
    GET请求装饰器
    
    Args:
        url: 请求URL
        **kwargs: 其他请求参数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs_func):
            # 执行原始函数获取动态参数
            dynamic_kwargs = func(*args, **kwargs_func) or {}
            
            # 合并静态和动态参数
            merged_kwargs = {**kwargs, **dynamic_kwargs}
            
            # 发送请求
            response, response_time = _make_http_request('GET', url, **merged_kwargs)
            
            # 获取当前测试结果
            test_name = func.__name__
            if test_name in _test_results:
                _test_results[test_name].response = response
                _test_results[test_name].response_time = response_time
            
            return response
        return wrapper
    return decorator


def http_post(url, **kwargs):
    """
    POST请求装饰器
    
    Args:
        url: 请求URL
        **kwargs: 其他请求参数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs_func):
            # 执行原始函数获取动态参数
            dynamic_kwargs = func(*args, **kwargs_func) or {}
            
            # 合并静态和动态参数
            merged_kwargs = {**kwargs, **dynamic_kwargs}
            
            # 发送请求
            response, response_time = _make_http_request('POST', url, **merged_kwargs)
            
            # 获取当前测试结果
            test_name = func.__name__
            if test_name in _test_results:
                _test_results[test_name].response = response
                _test_results[test_name].response_time = response_time
            
            return response
        return wrapper
    return decorator


def http_put(url, **kwargs):
    """
    PUT请求装饰器
    
    Args:
        url: 请求URL
        **kwargs: 其他请求参数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs_func):
            # 执行原始函数获取动态参数
            dynamic_kwargs = func(*args, **kwargs_func) or {}
            
            # 合并静态和动态参数
            merged_kwargs = {**kwargs, **dynamic_kwargs}
            
            # 发送请求
            response, response_time = _make_http_request('PUT', url, **merged_kwargs)
            
            # 获取当前测试结果
            test_name = func.__name__
            if test_name in _test_results:
                _test_results[test_name].response = response
                _test_results[test_name].response_time = response_time
            
            return response
        return wrapper
    return decorator


def http_delete(url, **kwargs):
    """
    DELETE请求装饰器
    
    Args:
        url: 请求URL
        **kwargs: 其他请求参数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs_func):
            # 执行原始函数获取动态参数
            dynamic_kwargs = func(*args, **kwargs_func) or {}
            
            # 合并静态和动态参数
            merged_kwargs = {**kwargs, **dynamic_kwargs}
            
            # 发送请求
            response, response_time = _make_http_request('DELETE', url, **merged_kwargs)
            
            # 获取当前测试结果
            test_name = func.__name__
            if test_name in _test_results:
                _test_results[test_name].response = response
                _test_results[test_name].response_time = response_time
            
            return response
        return wrapper
    return decorator


def assert_response(status_code=None, response_time=None):
    """
    响应断言装饰器
    
    Args:
        status_code: 期望的状态码
        response_time: 最大响应时间（毫秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原始函数，获取响应
            response = func(*args, **kwargs)
            
            # 获取响应时间
            test_name = func.__name__
            resp_time = _test_results.get(test_name, TestResult()).response_time
            
            # 断言状态码
            if status_code is not None:
                actual_status = response.status_code
                try:
                    assert actual_status == status_code, \
                        f"状态码断言失败：期望 {status_code}，实际 {actual_status}"
                    logger_manager.info(f"状态码断言成功：{actual_status} == {status_code}")
                except AssertionError as e:
                    logger_manager.error(str(e))
                    if test_name in _test_results:
                        _test_results[test_name].success = False
                        _test_results[test_name].error = str(e)
                    raise
            
            # 断言响应时间
            if response_time is not None:
                try:
                    assert resp_time <= response_time, \
                        f"响应时间断言失败：期望 <= {response_time}ms，实际 {resp_time:.2f}ms"
                    logger_manager.info(f"响应时间断言成功：{resp_time:.2f}ms <= {response_time}ms")
                except AssertionError as e:
                    logger_manager.error(str(e))
                    if test_name in _test_results:
                        _test_results[test_name].success = False
                        _test_results[test_name].error = str(e)
                    raise
            
            return response
        return wrapper
    return decorator


def extract_variables(**extract_rules):
    """
    变量提取装饰器
    
    Args:
        **extract_rules: 提取规则，格式为 var_name=(extraction_type, extraction_value)
                        extraction_type 可以是 'json_path', 'regex', 'header'
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原始函数，获取响应
            response = func(*args, **kwargs)
            
            # 获取当前测试结果
            test_name = func.__name__
            result = _test_results.get(test_name, TestResult())
            
            # 提取变量
            for var_name, (extraction_type, extraction_value) in extract_rules.items():
                value = None
                
                if extraction_type == 'json_path':
                    try:
                        json_data = response.json()
                        keys = extraction_value.split('.')
                        value = json_data
                        for key in keys:
                            if isinstance(value, dict) and key in value:
                                value = value[key]
                            else:
                                value = None
                                break
                    except (ValueError, TypeError):
                        logger_manager.error(f"无法从JSON响应中提取变量: {var_name}")
                
                elif extraction_type == 'header':
                    if extraction_value in response.headers:
                        value = response.headers[extraction_value]
                    else:
                        logger_manager.warning(f"响应头中未找到: {extraction_value}")
                
                elif extraction_type == 'regex':
                    match = re.search(extraction_value, response.text)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
                
                # 保存变量
                if value is not None:
                    result.variables[var_name] = value
                    logger_manager.info(f"提取变量: {var_name} = {value}")
            
            return response
        return wrapper
    return decorator


def quick_assert(url, method='GET', status_code=200, **kwargs):
    """
    快速断言函数，用于简单的API测试
    
    Args:
        url: 请求URL
        method: HTTP方法
        status_code: 期望的状态码
        **kwargs: 其他请求参数
        
    Returns:
        bool: 测试是否成功
    """
    try:
        response, response_time = _make_http_request(method, url, **kwargs)
        
        # 断言状态码
        assert response.status_code == status_code, \
            f"状态码断言失败：期望 {status_code}，实际 {response.status_code}"
        
        logger_manager.info(f"快速断言成功：{method} {url} 返回状态码 {status_code}")
        return True
    except Exception as e:
        logger_manager.error(f"快速断言失败：{str(e)}")
        return False


def quick_test(test_func, *args, **kwargs):
    """
    快速测试函数，用于执行测试函数并返回结果
    
    Args:
        test_func: 测试函数
        *args: 测试函数参数
        **kwargs: 测试函数关键字参数
        
    Returns:
        TestResult: 测试结果
    """
    test_name = test_func.__name__
    result = TestResult()
    _test_results[test_name] = result
    
    try:
        start_time = time.time()
        test_func(*args, **kwargs)
        result.response_time = (time.time() - start_time) * 1000
        logger_manager.info(f"快速测试成功: {test_name}, 耗时: {result.response_time:.2f}ms")
    except Exception as e:
        result.success = False
        result.error = str(e)
        logger_manager.error(f"快速测试失败: {test_name}, 错误: {str(e)}")
    
    return result