"""
测试管理系统工厂函数模块

提供便捷的工厂函数，用于快速创建测试用例、测试套件和测试运行器
"""

from typing import Dict, Any, List, Callable, Optional
from apitestkit.test.test_case import TestCase
from apitestkit.test.test_suite import TestSuite
from apitestkit.test.test_runner import TestRunner
from apitestkit.adapter.api_adapter import ApiAdapter


def create_test_case(name: str = "TestCase", 
                    setup: Optional[Callable] = None,
                    teardown: Optional[Callable] = None,
                    before_each: Optional[Callable] = None,
                    after_each: Optional[Callable] = None,
                    tags: Optional[List[str]] = None,
                    description: str = "") -> TestCase:
    """
    创建测试用例
    
    Args:
        name: 测试用例名称
        setup: 测试用例级别的setup函数
        teardown: 测试用例级别的teardown函数
        before_each: 每个测试步骤前的钩子函数
        after_each: 每个测试步骤后的钩子函数
        tags: 测试标签列表
        description: 测试用例描述
        
    Returns:
        TestCase: 测试用例实例
    """
    test_case = TestCase(name=name)
    
    if setup:
        test_case.setup(setup)
    if teardown:
        test_case.teardown(teardown)
    if before_each:
        test_case.before_each(before_each)
    if after_each:
        test_case.after_each(after_each)
    if tags:
        test_case.add_tags(tags)
    if description:
        test_case.description = description
    
    return test_case


def create_test_suite(name: str = "TestSuite",
                     setup: Optional[Callable] = None,
                     teardown: Optional[Callable] = None,
                     before_each: Optional[Callable] = None,
                     after_each: Optional[Callable] = None,
                     tags: Optional[List[str]] = None,
                     description: str = "") -> TestSuite:
    """
    创建测试套件
    
    Args:
        name: 测试套件名称
        setup: 套件级别的setup函数
        teardown: 套件级别的teardown函数
        before_each: 每个测试用例前的钩子函数
        after_each: 每个测试用例后的钩子函数
        tags: 测试标签列表
        description: 测试套件描述
        
    Returns:
        TestSuite: 测试套件实例
    """
    test_suite = TestSuite(name=name)
    
    if setup:
        test_suite.setup(setup)
    if teardown:
        test_suite.teardown(teardown)
    if before_each:
        test_suite.before_each(before_each)
    if after_each:
        test_suite.after_each(after_each)
    if tags:
        test_suite.add_tags(tags)
    if description:
        test_suite.description = description
    
    return test_suite


def create_test_runner(name: str = "TestRunner",
                      **config_kwargs) -> TestRunner:
    """
    创建测试运行器
    
    Args:
        name: 测试运行器名称
        **config_kwargs: 运行器配置参数
        
    Returns:
        TestRunner: 测试运行器实例
    """
    runner = TestRunner(name=name)
    if config_kwargs:
        runner.configure(**config_kwargs)
    return runner


def create_api_test(name: str,
                    url: str,
                    method: str = "GET",
                    **kwargs) -> TestCase:
    """
    创建API测试用例
    
    Args:
        name: 测试用例名称
        url: API接口URL
        method: HTTP方法
        **kwargs: 其他参数
        
    Returns:
        TestCase: 包含API测试步骤的测试用例
    """
    # 创建测试用例
    test_case = create_test_case(name=name)
    
    # 创建API适配器
    adapter = ApiAdapter()
    
    # 设置HTTP方法和URL
    adapter.set_method(method).set_url(url)
    
    # 添加API测试步骤
    test_case.add_step(
        name=f"{method} {url}",
        func=adapter,
        **kwargs
    )
    
    return test_case


def load_tests_from_json(file_path: str) -> List[TestCase]:
    """
    从JSON文件加载测试用例
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        List[TestCase]: 测试用例列表
    """
    import json
    
    test_cases = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # 支持单个测试用例或测试用例列表
        if isinstance(test_data, list):
            test_items = test_data
        else:
            test_items = [test_data]
        
        for item in test_items:
            # 创建测试用例
            test_case = create_test_case(
                name=item.get('name', 'Unnamed Test'),
                description=item.get('description', ''),
                tags=item.get('tags', [])
            )
            
            # 添加测试步骤
            steps = item.get('steps', [])
            for step_data in steps:
                # 创建API适配器
                adapter = ApiAdapter()
                
                # 设置API请求参数
                if 'method' in step_data:
                    adapter.set_method(step_data['method'])
                if 'url' in step_data:
                    adapter.set_url(step_data['url'])
                if 'headers' in step_data:
                    adapter.set_headers(step_data['headers'])
                if 'params' in step_data:
                    adapter.set_params(step_data['params'])
                if 'data' in step_data:
                    adapter.set_data(step_data['data'])
                if 'json' in step_data:
                    adapter.set_json(step_data['json'])
                if 'timeout' in step_data:
                    adapter.set_timeout(step_data['timeout'])
                
                # 添加断言
                assertions = step_data.get('assertions', [])
                for assertion in assertions:
                    assertion_type = assertion.get('type')
                    if assertion_type == 'status_code':
                        adapter.assert_status_code(assertion.get('value'))
                    elif assertion_type == 'json_path':
                        adapter.assert_json_path(
                            assertion.get('path'),
                            assertion.get('value'),
                            assertion.get('comparator', 'eq')
                        )
                    elif assertion_type == 'response_time':
                        adapter.assert_response_time(assertion.get('value'))
                    elif assertion_type == 'contains':
                        adapter.assert_contains(assertion.get('value'))
                
                # 添加步骤到测试用例
                test_case.add_step(
                    name=step_data.get('name', f"{adapter.method} {adapter.url}"),
                    func=adapter,
                    **step_data.get('args', {})
                )
            
            test_cases.append(test_case)
    
    except Exception as e:
        print(f"从JSON文件加载测试失败: {e}")
    
    return test_cases


def create_authorization_test(name: str,
                              auth_url: str,
                              auth_method: str = "POST",
                              auth_payload: Dict[str, Any] = None,
                              token_extractor: Optional[Callable] = None,
                              target_tests: Optional[List[TestCase]] = None) -> TestCase:
    """
    创建授权测试用例
    
    此测试用例用于获取授权令牌，并可将令牌应用到其他测试用例中
    
    Args:
        name: 测试用例名称
        auth_url: 授权接口URL
        auth_method: 授权请求方法
        auth_payload: 授权请求数据
        token_extractor: 令牌提取函数，如果为None，则尝试从响应JSON中提取'token'字段
        target_tests: 要应用令牌的目标测试用例列表
        
    Returns:
        TestCase: 授权测试用例
    """
    # 默认令牌提取函数
    if token_extractor is None:
        def default_token_extractor(response):
            try:
                data = response.json()
                return data.get('token') or data.get('access_token')
            except Exception:
                return None
        token_extractor = default_token_extractor
    
    # 创建授权测试用例
    auth_test = create_test_case(name=name)
    
    # 创建API适配器
    auth_adapter = ApiAdapter()
    auth_adapter.set_method(auth_method).set_url(auth_url)
    
    if auth_payload:
        if isinstance(auth_payload, dict) and auth_method.upper() in ['POST', 'PUT', 'PATCH']:
            auth_adapter.set_json(auth_payload)
        else:
            auth_adapter.set_data(auth_payload)
    
    # 设置断言确保授权成功
    auth_adapter.assert_status_code(200)
    
    # 创建保存令牌的函数
    def save_token(context, response):
        token = token_extractor(response)
        if token:
            context['auth_token'] = token
            # 如果有目标测试，将令牌应用到这些测试中
            if target_tests:
                for test_case in target_tests:
                    # 为每个目标测试添加前置钩子，注入授权令牌
                    test_case.before_each(lambda c: c.update({'auth_token': token}))
    
    # 添加保存令牌的后置处理
    auth_adapter.after_response(save_token)
    
    # 添加授权步骤
    auth_test.add_step(name="授权请求", func=auth_adapter)
    
    return auth_test


def create_multi_api_test(name: str,
                          steps: List[Dict[str, Any]]) -> TestCase:
    """
    创建多API测试用例
    
    用于测试涉及多个API调用的业务流程
    
    Args:
        name: 测试用例名称
        steps: 测试步骤配置列表
        
    Returns:
        TestCase: 多API测试用例
    """
    test_case = create_test_case(name=name)
    
    for step_config in steps:
        # 创建API适配器
        adapter = ApiAdapter()
        
        # 设置基本参数
        if 'method' in step_config:
            adapter.set_method(step_config['method'])
        if 'url' in step_config:
            adapter.set_url(step_config['url'])
        if 'headers' in step_config:
            adapter.set_headers(step_config['headers'])
        if 'params' in step_config:
            adapter.set_params(step_config['params'])
        if 'data' in step_config:
            adapter.set_data(step_config['data'])
        if 'json' in step_config:
            adapter.set_json(step_config['json'])
        if 'timeout' in step_config:
            adapter.set_timeout(step_config['timeout'])
        
        # 设置变量提取
        extractors = step_config.get('extract', [])
        for extractor in extractors:
            if extractor.get('type') == 'json_path':
                adapter.extract_json_path(
                    extractor.get('path'),
                    extractor.get('name')
                )
            elif extractor.get('type') == 'regex':
                adapter.extract_regex(
                    extractor.get('pattern'),
                    extractor.get('name')
                )
            elif extractor.get('type') == 'header':
                adapter.extract_header(
                    extractor.get('header'),
                    extractor.get('name')
                )
        
        # 设置断言
        assertions = step_config.get('assertions', [])
        for assertion in assertions:
            assertion_type = assertion.get('type')
            if assertion_type == 'status_code':
                adapter.assert_status_code(assertion.get('value'))
            elif assertion_type == 'json_path':
                adapter.assert_json_path(
                    assertion.get('path'),
                    assertion.get('value'),
                    assertion.get('comparator', 'eq')
                )
            elif assertion_type == 'response_time':
                adapter.assert_response_time(assertion.get('value'))
            elif assertion_type == 'contains':
                adapter.assert_contains(assertion.get('value'))
        
        # 添加前置和后置处理函数
        if 'before_request' in step_config:
            adapter.before_request(step_config['before_request'])
        if 'after_response' in step_config:
            adapter.after_response(step_config['after_response'])
        
        # 添加步骤到测试用例
        test_case.add_step(
            name=step_config.get('name', f"{adapter.method} {adapter.url}"),
            func=adapter
        )
    
    return test_case


def create_async_test(name: str,
                      async_steps: List[Dict[str, Any]]) -> TestCase:
    """
    创建异步测试用例
    
    用于测试异步API和复杂的异步场景
    
    Args:
        name: 测试用例名称
        async_steps: 异步测试步骤配置列表
        
    Returns:
        TestCase: 异步测试用例
    """
    import asyncio
    from functools import wraps
    
    test_case = create_test_case(name=name)
    
    # 创建异步测试函数包装器
    def async_test_wrapper(func):
        @wraps(func)
        def wrapper(context, **kwargs):
            return asyncio.run(func(context, **kwargs))
        return wrapper
    
    # 创建异步测试函数
    async def async_test_function(context):
        # 执行所有异步步骤
        for step_config in async_steps:
            adapter = ApiAdapter()
            
            # 设置基本参数
            if 'method' in step_config:
                adapter.set_method(step_config['method'])
            if 'url' in step_config:
                adapter.set_url(step_config['url'])
            # 设置其他参数...
            
            # 异步发送请求
            response = await adapter.send_async(context)
            
            # 处理响应
            if response:
                # 提取变量
                extractors = step_config.get('extract', [])
                for extractor in extractors:
                    if extractor.get('type') == 'json_path':
                        value = adapter._extract_json_path(response, extractor.get('path'))
                        if value is not None:
                            context[extractor.get('name')] = value
                
                # 执行断言
                assertions = step_config.get('assertions', [])
                for assertion in assertions:
                    if assertion.get('type') == 'status_code':
                        expected = assertion.get('value')
                        actual = response.status_code
                        assert actual == expected, f"状态码断言失败: 期望 {expected}, 实际 {actual}"
    
    # 添加异步测试步骤
    test_case.add_step(
        name=f"异步测试: {name}",
        func=async_test_wrapper(async_test_function)
    )
    
    return test_case