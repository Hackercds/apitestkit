"""
API适配器模块

提供核心的API测试功能，支持链式调用，包括测试用例管理、HTTP请求发送、响应断言等。
增强版支持复杂接口场景、异步接口测试、大模型流式接口测试和Agent接口参数支持。
"""

import time
import json
import asyncio
import requests
import aiohttp
import re
from typing import Dict, Any, Optional, Callable, Union, List
from apitestkit.core.logger import logger_manager, create_user_logger
from apitestkit.core.config import config_manager
from apitestkit.core.exceptions import ApiTestKitError
from apitestkit.core.data_storage import data_storage_manager
from apitestkit.performance import performance as create_performance_runner
from apitestkit.performance.performance_runner import PerformanceRunner


class ApiAdapter:
    """
    API适配器类，提供链式调用的API测试功能
    支持同步/异步请求、流式接口、Agent接口参数和复杂测试场景
    """
    
    def __init__(self, test_name: str = None, async_mode: bool = False):
        # 重置测试状态
        self._reset_state()
        # 从配置管理器获取默认配置
        self._base_url = config_manager.get('base_url', '')
        self._timeout = config_manager.get('default_timeout', 30)
        self._verify_ssl = config_manager.get('verify_ssl', True)
        self._proxies = config_manager.get('proxy', None)
        self._headers = config_manager.get('headers', {}).copy()
        
        # 新增功能配置
        self._async_mode = async_mode
        self._user_logger = None
        self._auth = None
        self._stream_handler = None
        self._agent_params = {}
        self._pre_request_hooks = []
        self._post_response_hooks = []
        
        # 数据存储相关配置
        self._tags = []
        self._test_context = {}
        self._last_record_id = None
        
        # 性能测试相关配置
        self._performance_runner = None
        self._performance_request_config = None
        
        # 盲顺序调用相关配置
        self._request_queue = []
        self._blind_order_mode = False
        
        if test_name:
            self._test_name = test_name
            self._setup_logger(test_name)
    
    def _reset_state(self):
        """
        重置测试状态
        """
        self._test_name = "Untitled Test"
        self._step_name = "Untitled Step"
        self._url = ""
        self._method = "GET"
        self._headers = {}
        self._params = {}
        self._data = None
        self._json = None
        self._files = None
        self._cookies = {}
        self._response = None
        self._response_time = 0
        self._variables = {}
        
        # 新增状态
        self._auth = None
        self._stream_handler = None
        self._agent_params = {}
        self._is_stream = False
        self._stream_buffer = []
        
        # 数据存储相关状态
        self._tags = []
        self._test_context = {}
        self._last_record_id = None
        
        # 性能测试相关状态
        self._performance_request_config = None
        
        # 盲顺序调用相关状态
        self._request_queue = []
    
    def _setup_logger(self, test_name: str):
        """
        设置测试专属的用户日志记录器
        
        Args:
            test_name: 测试名称
        """
        self._user_logger = create_user_logger(test_name)
    
    def test(self, name):
        """
        设置测试名称
        
        Args:
            name: 测试名称
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_name = name
        self._setup_logger(name)
        logger_manager.info(f"[框架] 开始测试: {name}")
        return self
    
    def step(self, name):
        """
        设置测试步骤名称
        
        Args:
            name: 步骤名称
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._step_name = name
        logger_manager.info(f"[框架] 执行步骤: {name}")
        return self
    
    def step_name(self, name):
        """
        设置测试步骤名称（step方法的别名）
        
        Args:
            name: 步骤名称
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        return self.step(name)
    
    def get(self, url):
        """
        设置GET请求
        
        Args:
            url: 请求URL
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._method = "GET"
        self._url = url
        return self
    
    def post(self, url):
        """
        设置POST请求
        
        Args:
            url: 请求URL
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._method = "POST"
        self._url = url
        return self
    
    def put(self, url):
        """
        设置PUT请求
        
        Args:
            url: 请求URL
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._method = "PUT"
        self._url = url
        return self
    
    def delete(self, url):
        """
        设置DELETE请求
        
        Args:
            url: 请求URL
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._method = "DELETE"
        self._url = url
        return self
    
    def headers(self, headers):
        """
        设置请求头
        
        Args:
            headers: 请求头字典
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._headers.update(headers)
        return self
    
    def params(self, params):
        """
        设置URL参数
        
        Args:
            params: URL参数字典
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._params.update(params)
        return self
    
    def body(self, data):
        """
        设置请求体数据（form-data）
        
        Args:
            data: 请求体数据
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._data = data
        return self
    
    def json(self, json_data):
        """
        设置JSON请求体
        
        Args:
            json_data: JSON数据
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._json = json_data
        return self
    
    def auth(self, auth_tuple):
        """
        设置HTTP认证信息
        
        Args:
            auth_tuple: 认证元组 (username, password)
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._auth = auth_tuple
        return self
    
    def files(self, files_dict):
        """
        设置文件上传
        
        Args:
            files_dict: 文件字典，格式如 {'file': open('file.txt', 'rb')}
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._files = files_dict
        return self
    
    def stream(self, enable: bool = True, handler: Callable = None, format_type: str = 'raw', json_path: str = None):
        """
        启用流式响应处理，增强支持多种流式格式
        
        Args:
            enable: 是否启用流式响应
            handler: 流式响应处理函数，接收chunk参数
            format_type: 流式响应格式类型，可选值: 'raw'(原始), 'sse'(Server-Sent Events), 'json'(JSON chunks)
            json_path: 可选，指定从JSON chunk中提取的路径，如 '$.choices[0].delta.content'
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._is_stream = enable
        self._stream_handler = handler
        self._stream_format = format_type.lower()
        self._stream_json_path = json_path
        self._stream_buffer = []
        self._parsed_stream_content = []  # 存储解析后的内容
        return self
    
    def _process_stream_chunk(self, chunk_str: str):
        """
        处理流式响应块，根据配置的格式进行解析
        
        Args:
            chunk_str: 原始响应块字符串
        
        Returns:
            str: 处理后的内容（如果需要提取）
        """
        processed_content = None
        
        if self._stream_format == 'sse':
            # 处理SSE格式: data: {...}\n\n
            # 修复：将多行文本中的转义字符正确处理，尤其是换行符
            chunk_str = chunk_str.replace('\\n', '\n')
            
            # 分割多行消息
            lines = chunk_str.split('\n')
            for line in lines:
                if line.startswith('data:'):
                    data_part = line[5:].strip()
                    if data_part:
                        try:
                            # 尝试解析JSON数据
                            json_data = json.loads(data_part)
                            processed_content = self._extract_from_json(json_data, self._stream_json_path)
                            if processed_content is not None:
                                self._parsed_stream_content.append(str(processed_content))
                        except json.JSONDecodeError:
                            # 不是有效的JSON，保持原样
                            if not data_part == '[DONE]':  # 忽略OpenAI等API的结束标记
                                self._parsed_stream_content.append(data_part)
                                processed_content = data_part
        
        elif self._stream_format == 'json':
            # 处理JSON chunks格式
            try:
                json_data = json.loads(chunk_str)
                processed_content = self._extract_from_json(json_data, self._stream_json_path)
                if processed_content is not None:
                    self._parsed_stream_content.append(str(processed_content))
            except json.JSONDecodeError:
                # 如果解析失败，可能是部分JSON，尝试简单存储
                logger_manager.warning(f"[框架] 无法解析JSON chunk: {chunk_str[:100]}...")
                self._parsed_stream_content.append(chunk_str)
                processed_content = chunk_str
        
        else:  # raw格式
            processed_content = chunk_str
            self._parsed_stream_content.append(chunk_str)
        
        return processed_content
    
    def _extract_from_json(self, json_data: Any, json_path: str = None):
        """
        从JSON数据中提取指定路径的值
        
        Args:
            json_data: JSON数据
            json_path: JSON路径，如 '$.choices[0].delta.content'
            
        Returns:
            Any: 提取的值，如果路径不存在返回None
        """
        if not json_path:
            return json_data
        
        # 简单的JSON路径解析实现
        try:
            # 移除$前缀
            if json_path.startswith('$'):
                json_path = json_path[1:]
            
            # 分割路径部分
            parts = json_path.split('.')
            result = json_data
            
            for part in parts:
                # 检查是否是数组索引
                if '[' in part and ']' in part:
                    # 提取数组名和索引
                    array_name = part[:part.find('[')]
                    index = int(part[part.find('[')+1:part.find(']')])
                    result = result[array_name][index]
                else:
                    # 普通字段
                    if part in result:
                        result = result[part]
                    else:
                        return None
            
            return result
        except (KeyError, IndexError, ValueError, TypeError):
            logger_manager.warning(f"[框架] 无法从JSON路径 '{json_path}' 提取数据")
            return None
    
    def assert_stream_content(self, expected_content: str, comparator: str = 'contains'):
        """
        断言流式响应内容
        
        Args:
            expected_content: 期望的内容
            comparator: 比较器，可选值: 'eq'(等于), 'contains'(包含), 'startswith'(开头), 'endswith'(结尾)
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        full_content = self.get_full_stream_content()
        
        # 使用与响应断言相同的比较逻辑
        if comparator == 'eq' and full_content != expected_content:
            raise AssertionError(f"流式响应内容不匹配。期望: '{expected_content}', 实际: '{full_content}'")
        elif comparator == 'contains' and expected_content not in full_content:
            raise AssertionError(f"流式响应内容不包含期望文本。期望: '{expected_content}', 实际: '{full_content}'")
        elif comparator == 'startswith' and not full_content.startswith(expected_content):
            raise AssertionError(f"流式响应内容不以期望文本开头。期望: '{expected_content}', 实际: '{full_content}'")
        elif comparator == 'endswith' and not full_content.endswith(expected_content):
            raise AssertionError(f"流式响应内容不以期望文本结尾。期望: '{expected_content}', 实际: '{full_content}'")
        
        logger_manager.info(f"[框架] 流式响应内容断言成功")
        return True
    
    def assert_stream_regex(self, pattern: str):
        """
        使用正则表达式断言流式响应内容
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        full_content = self.get_full_stream_content()
        
        if not re.search(pattern, full_content):
            raise AssertionError(f"正则表达式 '{pattern}' 在流式响应内容中未找到匹配: '{full_content}'")
        
        logger_manager.info(f"[框架] 流式响应正则表达式断言成功")
        return True
    
    def assert_stream_length(self, min_length: int = None, max_length: int = None):
        """
        断言流式响应的长度
        
        Args:
            min_length: 最小长度（可选）
            max_length: 最大长度（可选）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        full_content = self.get_full_stream_content()
        content_length = len(full_content)
        
        if min_length is not None and content_length < min_length:
            raise AssertionError(f"流式响应内容长度小于最小值。期望: >={min_length}, 实际: {content_length}")
        if max_length is not None and content_length > max_length:
            raise AssertionError(f"流式响应内容长度大于最大值。期望: <={max_length}, 实际: {content_length}")
        
        logger_manager.info(f"[框架] 流式响应长度断言成功")
        return True
    
    def agent_params(self, params: Dict[str, Any], merge_to_json: bool = True):
        """
        设置Agent接口参数，增强支持各种AI接口参数格式
        
        Args:
            params: Agent相关参数字典
            merge_to_json: 是否自动合并到请求体json中，默认为True
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._agent_params.update(params)
        
        # 根据需要合并到请求体
        if merge_to_json:
            if self._json is None:
                self._json = {}
            self._json.update(params)
        
        logger_manager.debug(f"[框架] 设置Agent参数: {json.dumps(params, ensure_ascii=False)}")
        return self
    
    def ai_messages(self, messages: List[Dict[str, str]], role_key: str = 'role', content_key: str = 'content'):
        """
        设置AI消息列表，支持各种LLM接口的消息格式
        
        Args:
            messages: 消息列表，每个消息包含角色和内容
            role_key: 角色字段名，默认为'role'
            content_key: 内容字段名，默认为'content'
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        # 标准化消息格式
        standardized_messages = []
        for msg in messages:
            standardized_msg = {
                role_key: msg.get('role', 'user'),
                content_key: msg.get('content', '')
            }
            # 添加其他可能的字段
            for key, value in msg.items():
                if key not in ['role', 'content']:
                    standardized_msg[key] = value
            standardized_messages.append(standardized_msg)
        
        # 设置消息参数
        self.agent_params({'messages': standardized_messages})
        return self
    
    def ai_prompt(self, prompt: str, system_prompt: str = None):
        """
        快速设置AI提示词，自动构建消息格式
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        messages = []
        
        # 添加系统提示词（如果有）
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        # 添加用户提示词
        messages.append({'role': 'user', 'content': prompt})
        
        return self.ai_messages(messages)
    
    def ai_options(self, temperature: float = None, max_tokens: int = None, 
                   top_p: float = None, stop_sequences: List[str] = None, **kwargs):
        """
        设置AI生成参数，如温度、最大token数等
        
        Args:
            temperature: 生成温度，控制输出随机性
            max_tokens: 最大生成token数
            top_p: 核采样参数
            stop_sequences: 停止序列
            **kwargs: 其他生成参数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        options = {}
        if temperature is not None:
            options['temperature'] = temperature
        if max_tokens is not None:
            options['max_tokens'] = max_tokens
        if top_p is not None:
            options['top_p'] = top_p
        if stop_sequences is not None:
            options['stop'] = stop_sequences
        
        # 添加其他参数
        options.update(kwargs)
        
        return self.agent_params(options)
    
    def agent_param_template(self, template_name: str, **template_vars):
        """
        使用预定义的参数模板
        
        Args:
            template_name: 模板名称
            **template_vars: 模板变量
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        # 预定义常用模板
        templates = {
            'openai_chat': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 1000
            },
            'anthropic_chat': {
                'model': 'claude-3-opus-20240229',
                'temperature': 0.5,
                'max_tokens_to_sample': 1000
            },
            'gemini_chat': {
                'model': 'gemini-1.5-flash',
                'temperature': 0.7,
                'max_output_tokens': 1000
            }
        }
        
        # 获取模板并应用变量
        if template_name in templates:
            params = templates[template_name].copy()
            # 替换模板变量
            for key, value in params.items():
                if isinstance(value, str):
                    try:
                        params[key] = value.format(**template_vars)
                    except (KeyError, ValueError):
                        pass
            
            return self.agent_params(params)
        else:
            raise ApiTestKitError(f"未知的参数模板: {template_name}")
    
    def cookies(self, cookies):
        """
        设置Cookies
        
        Args:
            cookies: Cookies字典
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._cookies.update(cookies)
        return self
    
    def timeout(self, seconds):
        """
        设置超时时间
        
        Args:
            seconds: 超时时间（秒）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._timeout = seconds
        return self
    
    def verify(self, verify):
        """
        设置是否验证SSL证书
        
        Args:
            verify: 是否验证SSL证书
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._verify_ssl = verify
        return self
    
    def before_request(self, hook: Callable):
        """
        添加请求前钩子函数
        
        Args:
            hook: 钩子函数，接收request_kwargs参数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._pre_request_hooks.append(hook)
        return self
    
    def after_response(self, hook: Callable):
        """
        添加响应后钩子函数
        
        Args:
            hook: 钩子函数，接收response参数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._post_response_hooks.append(hook)
        return self
    
    def user_log(self, message: str, level: str = 'info'):
        """
        记录用户测试日志
        
        Args:
            message: 日志消息
            level: 日志级别 (debug, info, warning, error, critical)
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if self._user_logger:
            log_method = getattr(self._user_logger, level, self._user_logger.info)
            log_method(message)
        else:
            # 如果没有用户日志器，使用框架日志器但标记为用户日志
            frame_log_method = getattr(logger_manager, level, logger_manager.info)
            frame_log_method(f"[用户] {message}")
        return self
    
    def _enhance_agent_request(self, request_kwargs: Dict[str, Any]):
        """
        增强Agent接口请求，根据不同的接口类型进行特殊处理
        
        Args:
            request_kwargs: 请求参数字典
        """
        # 设置适合AI接口的默认请求头
        if 'Content-Type' not in self._headers:
            self._headers['Content-Type'] = 'application/json'
        
        # 处理特殊的参数映射，确保兼容性
        if 'json' in request_kwargs and request_kwargs['json'] and 'messages' in request_kwargs['json']:
            # 确保消息格式正确
            messages = request_kwargs['json']['messages']
            if isinstance(messages, list):
                for i, msg in enumerate(messages):
                    if 'role' in msg and 'content' in msg:
                        # 确保role是有效的
                        valid_roles = ['system', 'user', 'assistant', 'tool']
                        if msg['role'] not in valid_roles:
                            logger_manager.warning(f"[框架] 消息角色 '{msg['role']}' 可能无效，建议使用: {valid_roles}")
        
        # 记录增强后的Agent请求信息
        if self._agent_params:
            logger_manager.debug(f"[框架] 增强Agent请求，参数: {json.dumps(self._agent_params, ensure_ascii=False)}")
    
    def send(self):
        """
        发送同步请求，增强支持Agent接口参数处理
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        # 构建完整URL
        url = self._url if self._url.startswith(('http://', 'https://')) else self._base_url + self._url
        
        # 准备请求参数
        request_kwargs = {
            'url': url,
            'timeout': self._timeout,
            'verify': self._verify_ssl,
            'headers': self._headers,
            'params': self._params,
            'cookies': self._cookies
        }
        
        if self._proxies:
            request_kwargs['proxies'] = self._proxies
        
        if self._auth:
            request_kwargs['auth'] = self._auth
        
        # 处理Agent特定的请求增强
        if self._agent_params:
            self._enhance_agent_request(request_kwargs)
        
        # 根据请求方法设置相应参数
        if self._method == 'GET':
            pass  # GET请求不需要额外数据
        elif self._method == 'POST':
            if self._json is not None:
                request_kwargs['json'] = self._json
            elif self._data is not None:
                request_kwargs['data'] = self._data
            if self._files:
                request_kwargs['files'] = self._files
        elif self._method in ['PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
            if self._json is not None:
                request_kwargs['json'] = self._json
            elif self._data is not None:
                request_kwargs['data'] = self._data
        
        # 执行请求前钩子
        for hook in self._pre_request_hooks:
            try:
                hook(request_kwargs)
            except Exception as e:
                logger_manager.error(f"请求前钩子执行失败: {str(e)}")
        
        # 记录请求日志
        logger_manager.log_request(
            self._method, url, 
            headers=self._headers,
            params=self._params,
            json_data=self._json or self._data
        )
        
        # 发送请求并记录时间
        start_time = time.time()
        try:
            if self._is_stream:
                # 流式响应处理
                with requests.request(self._method, stream=True, **request_kwargs) as response:
                    self._response = response
                    self._response_time = (time.time() - start_time) * 1000
                    
                    # 记录流式响应开始
                    logger_manager.info(f"[框架] 开始接收流式响应，状态码: {response.status_code}")
                    
                    # 处理流式响应
                    try:
                        for chunk in response.iter_content(chunk_size=None):
                            if chunk:
                                chunk_str = chunk.decode('utf-8', errors='ignore')
                                self._stream_buffer.append(chunk_str)
                                
                                # 处理流式数据
                                processed_content = self._process_stream_chunk(chunk_str)
                                
                                # 调用用户提供的处理器
                                if self._stream_handler:
                                    try:
                                        if processed_content is not None:
                                            self._stream_handler(processed_content)
                                        else:
                                            self._stream_handler(chunk_str)
                                    except Exception as e:
                                        logger_manager.error(f"[框架] 流式响应处理器执行失败: {str(e)}")
                                        # 继续处理，不中断整个流
                    except Exception as stream_error:
                        logger_manager.error(f"[框架] 流式响应处理异常: {str(stream_error)}")
                        # 不抛出异常，允许测试继续进行
                    
                    logger_manager.info(f"[框架] 流式响应接收完成，总块数: {len(self._stream_buffer)}")
                
                # 记录响应日志
                logger_manager.log_response(
                    self._response.status_code, 
                    self._response_time,
                    text='[STREAMING RESPONSE]'
                )
            else:
                # 普通响应处理
                self._response = requests.request(self._method, **request_kwargs)
                self._response_time = (time.time() - start_time) * 1000
                
                # 记录响应日志
                logger_manager.log_response(
                    self._response.status_code, 
                    self._response_time,
                    text=self._response.text
                )
            
            # 执行响应后钩子
            for hook in self._post_response_hooks:
                try:
                    hook(self._response)
                except Exception as e:
                    logger_manager.error(f"响应后钩子执行失败: {str(e)}")
            
            # 存储响应数据
            try:
                response_data = {
                    'test_name': self._test_name,
                    'step_name': self._step_name,
                    'method': self._method,
                    'url': url,
                    'status_code': self._response.status_code,
                    'response_time': self._response_time,
                    'headers': dict(self._response.headers),
                    'request_params': self._params,
                    'request_headers': self._headers,
                    'tags': self._tags,
                    'context': self._test_context
                }
                
                # 尝试解析JSON响应
                try:
                    response_data['response_json'] = self._response.json()
                except (ValueError, TypeError):
                    response_data['response_text'] = self._response.text
                
                # 存储流式响应数据
                if self._is_stream and self._stream_buffer:
                    response_data['stream_chunks'] = self._stream_buffer
                    response_data['stream_content'] = self.get_full_stream_content()
                
                # 保存到数据存储 - 调整参数以匹配store_response方法
                request_info = {
                    'url': url,
                    'method': self._method,
                    'params': self._params,
                    'headers': self._headers,
                    'status_code': self._response.status_code,
                    'response_time': self._response_time
                }
                self._last_record_id = data_storage_manager.store_response(
                    self._response, 
                    request_info,
                    tags=self._tags,
                    metadata={'test_name': self._test_name, 'step_name': self._step_name, 'context': self._test_context}
                )
                logger_manager.debug(f"[框架] 响应数据已保存，记录ID: {self._last_record_id}")
            except Exception as storage_error:
                logger_manager.error(f"[框架] 响应数据存储失败: {str(storage_error)}")
                    
        except requests.exceptions.RequestException as e:
            self._response_time = (time.time() - start_time) * 1000
            logger_manager.error(f"[框架] 请求失败: {str(e)}")
            raise
        
        return self
    
    async def send_async(self):
        """
        发送异步请求，增强支持Agent接口参数处理
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        # 构建完整URL
        url = self._url if self._url.startswith(('http://', 'https://')) else self._base_url + self._url
        
        # 准备请求参数
        request_kwargs = {
            'url': url,
            'timeout': self._timeout,
            'headers': self._headers,
            'params': self._params,
            'cookies': self._cookies
        }
        
        # 处理Agent特定的请求增强
        if self._agent_params:
            self._enhance_agent_request(request_kwargs)
        
        if not self._verify_ssl:
            request_kwargs['ssl'] = False
        
        if self._auth:
            request_kwargs['auth'] = self._auth
        
        # 根据请求方法设置相应参数
        if self._method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if self._json is not None:
                request_kwargs['json'] = self._json
            elif self._data is not None:
                request_kwargs['data'] = self._data
        
        # 执行请求前钩子
        for hook in self._pre_request_hooks:
            try:
                hook(request_kwargs)
            except Exception as e:
                logger_manager.error(f"[框架] 请求前钩子执行失败: {str(e)}")
        
        # 记录请求日志
        logger_manager.log_request(
            self._method, url, 
            headers=self._headers,
            params=self._params,
            json_data=self._json or self._data
        )
        
        # 发送异步请求并记录时间
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                if self._is_stream:
                    # 流式响应处理
                    async with session.request(self._method, **request_kwargs) as response:
                        self._response = response
                        self._response_time = (time.time() - start_time) * 1000
                        
                        # 处理流式响应
                    logger_manager.info(f"[框架] 开始接收异步流式响应，状态码: {response.status}")
                    
                    try:
                        async for chunk in response.content:
                            if chunk:
                                chunk_str = chunk.decode('utf-8', errors='ignore')
                                self._stream_buffer.append(chunk_str)
                                
                                # 处理流式数据
                                processed_content = self._process_stream_chunk(chunk_str)
                                
                                # 调用用户提供的处理器
                                if self._stream_handler:
                                    try:
                                        if processed_content is not None:
                                            self._stream_handler(processed_content)
                                        else:
                                            self._stream_handler(chunk_str)
                                    except Exception as e:
                                        logger_manager.error(f"[框架] 异步流式响应处理器执行失败: {str(e)}")
                                        # 继续处理，不中断整个流
                    except Exception as stream_error:
                        logger_manager.error(f"[框架] 异步流式响应处理异常: {str(stream_error)}")
                        # 不抛出异常，允许测试继续进行
                    
                    logger_manager.info(f"[框架] 异步流式响应接收完成，总块数: {len(self._stream_buffer)}")
                else:
                    # 普通响应处理
                    async with session.request(self._method, **request_kwargs) as response:
                        self._response = response
                        # 读取响应内容
                        self._response._content = await response.read()
                        self._response_time = (time.time() - start_time) * 1000
                
                # 记录响应日志
                logger_manager.log_response(
                    self._response.status, 
                    self._response_time,
                    text='[STREAMING RESPONSE]' if self._is_stream else str(self._response._content)
                )
            
            # 执行响应后钩子
            for hook in self._post_response_hooks:
                try:
                    hook(self._response)
                except Exception as e:
                    logger_manager.error(f"[框架] 响应后钩子执行失败: {str(e)}")
            
            # 存储响应数据
            try:
                response_data = {
                    'test_name': self._test_name,
                    'step_name': self._step_name,
                    'method': self._method,
                    'url': url,
                    'status_code': self._response.status,
                    'response_time': self._response_time,
                    'headers': dict(self._response.headers),
                    'request_params': self._params,
                    'request_headers': self._headers,
                    'tags': self._tags,
                    'context': self._test_context
                }
                
                # 尝试解析JSON响应
                try:
                    import json as json_module
                    response_data['response_json'] = json_module.loads(self._response._content)
                except (ValueError, TypeError):
                    response_data['response_text'] = self._response._content.decode('utf-8', errors='ignore')
                
                # 存储流式响应数据
                if self._is_stream and self._stream_buffer:
                    response_data['stream_chunks'] = self._stream_buffer
                    response_data['stream_content'] = self.get_full_stream_content()
                
                # 保存到数据存储
                self._last_record_id = data_storage_manager.save_response(response_data)
                logger_manager.debug(f"[框架] 异步响应数据已保存，记录ID: {self._last_record_id}")
            except Exception as storage_error:
                logger_manager.error(f"[框架] 异步响应数据存储失败: {str(storage_error)}")
                    
        except Exception as e:
            self._response_time = (time.time() - start_time) * 1000
            logger_manager.error(f"[框架] 异步请求失败: {str(e)}")
            raise
        
        return self
    
    def extract(self, variable_name: str, json_path: str = None, regex: str = None, 
                header: str = None, response_content: str = None):
        """
        提取变量
        
        Args:
            variable_name: 变量名
            json_path: JSON路径（使用点号分隔，如 'data.user.id'）
            regex: 正则表达式
            header: 响应头名称
            response_content: 可选，指定要提取的响应内容
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法提取变量：未发送请求或请求失败")
            return self
        
        value = None
        
        # 从JSON响应中提取
        if json_path:
            try:
                if hasattr(self._response, 'json'):
                    json_data = self._response.json()
                else:
                    # aiohttp响应处理
                    import json as json_module
                    json_data = json_module.loads(self._response._content)
                
                # 支持数组索引访问，如 'data.users[0].name'
                if '[' in json_path:
                    # 解析带有索引的路径
                    value = json_data
                    # 使用正则表达式匹配路径部分
                    parts = re.findall(r'([\w]+)\[([\d]+)\]|([\w]+)', json_path)
                    for part in parts:
                        if part[0] and part[1]:  # 匹配到数组部分
                            key, index = part[0], int(part[1])
                            if isinstance(value, dict) and key in value and isinstance(value[key], list):
                                if index < len(value[key]):
                                    value = value[key][index]
                                else:
                                    value = None
                                    break
                            else:
                                value = None
                                break
                        elif part[2]:  # 匹配到普通键
                            key = part[2]
                            if isinstance(value, dict) and key in value:
                                value = value[key]
                            else:
                                value = None
                                break
                else:
                    # 普通点分隔路径
                    keys = json_path.split('.')
                    value = json_data
                    for key in keys:
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            value = None
                            break
            except (ValueError, TypeError) as e:
                logger_manager.error(f"[框架] 无法从JSON响应中提取路径: {json_path}, 错误: {str(e)}")
        
        # 从响应头中提取
        elif header:
            if hasattr(self._response, 'headers') and header in self._response.headers:
                value = self._response.headers[header]
            else:
                logger_manager.warning(f"[框架] 响应头中未找到: {header}")
        
        # 从响应文本中提取（使用正则表达式）
        elif regex:
            content = response_content or (self._response.text if hasattr(self._response, 'text') else 
                                           self._response._content.decode('utf-8', errors='ignore'))
            match = re.search(regex, content)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
        
        # 保存变量
        if value is not None:
            self._variables[variable_name] = value
            logger_manager.info(f"[框架] 提取变量: {variable_name} = {value}")
        
        return self
    
    def extract_stream(self, variable_name: str, regex: str = None, json_path: str = None, occurrence: int = 0):
        """
        从流式响应中提取变量，增强支持正则和JSON路径提取
        
        Args:
            variable_name: 变量名
            regex: 正则表达式（可选）
            json_path: JSON路径（可选），如果设置了，则尝试从解析后的JSON中提取
            occurrence: 匹配的第几个结果，默认为0（第一个）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._stream_buffer:
            logger_manager.warning(f"[框架] 流式响应缓冲区为空，无法提取变量")
            return self
        
        # 根据提供的参数选择提取方法
        if json_path and hasattr(self, '_parsed_stream_content') and self._parsed_stream_content:
            # 尝试从解析后的内容中提取
            try:
                # 尝试将解析后的内容重新组合成JSON
                # 注意：这只适用于某些特定格式的流式响应
                combined_json_str = ''.join(self._stream_buffer)
                # 处理常见的流式JSON格式，如data: {"id":"1"}\ndata: {"id":"2"}
                if combined_json_str.startswith('data:'):
                    # 提取所有data行
                    data_lines = re.findall(r'data: (.*?)(?:\n|$)', combined_json_str, re.DOTALL)
                    # 尝试合并为有效的JSON数组
                    json_array_str = '[' + ','.join(data_lines) + ']'
                    json_data = json.loads(json_array_str)
                    value = self._extract_from_json(json_data, json_path)
                    if value is not None:
                        self._variables[variable_name] = value
                        logger_manager.info(f"[框架] 从解析后的流式响应提取变量: {variable_name} = {value}")
            except Exception as e:
                logger_manager.warning(f"[框架] 从解析后的流式响应提取变量失败: {str(e)}")
        
        # 使用正则表达式提取（兼容原有功能）
        elif regex:
            # 合并所有流式响应块
            full_content = ''.join(self._stream_buffer)
            matches = re.finditer(regex, full_content)
            match_list = list(matches)
            
            if occurrence < len(match_list):
                match = match_list[occurrence]
                value = match.group(1) if match.groups() else match.group(0)
                self._variables[variable_name] = value
                logger_manager.info(f"[框架] 从流式响应提取变量: {variable_name} = {value} (第{occurrence+1}个匹配)")
            else:
                logger_manager.warning(f"[框架] 正则表达式匹配次数不足，请求第{occurrence+1}个匹配但只有{len(match_list)}个匹配")
        
        return self
    
    def extract_stream_chunks(self, variable_name: str, filter_func: Callable = None):
        """
        提取所有流式响应块到变量
        
        Args:
            variable_name: 变量名
            filter_func: 可选的过滤函数，接收chunk并返回布尔值决定是否包含
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._stream_buffer:
            logger_manager.warning(f"[框架] 流式响应缓冲区为空，无法提取变量")
            self._variables[variable_name] = []
            return self
        
        # 应用过滤函数
        if filter_func:
            filtered_chunks = [chunk for chunk in self._stream_buffer if filter_func(chunk)]
            self._variables[variable_name] = filtered_chunks
            logger_manager.info(f"[框架] 从流式响应提取过滤后的块: {variable_name} (共{len(filtered_chunks)}个块)")
        else:
            self._variables[variable_name] = self._stream_buffer.copy()
            logger_manager.info(f"[框架] 从流式响应提取所有块: {variable_name} (共{len(self._stream_buffer)}个块)")
        
        return self
    
    def stream_until(self, condition_func: Callable, timeout: int = 30):
        """
        持续处理流式响应直到满足条件
        
        Args:
            condition_func: 条件函数，接收当前累积的内容，返回布尔值
            timeout: 超时时间（秒）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        start_time = time.time()
        
        # 等待条件满足或超时
        while time.time() - start_time < timeout:
            current_content = self.get_full_stream_content()
            if condition_func(current_content):
                logger_manager.info(f"[框架] 流式响应条件满足，用时: {time.time() - start_time:.2f}秒")
                return self
            
            # 短暂暂停避免CPU占用过高
            time.sleep(0.1)
        
        logger_manager.warning(f"[框架] 流式响应条件等待超时")
        return self
    
    def use_variable(self, variable_name: str) -> Any:
        """
        使用已提取的变量
        
        Args:
            variable_name: 变量名
            
        Returns:
            Any: 变量值
        """
        if variable_name in self._variables:
            return self._variables[variable_name]
        logger_manager.warning(f"[框架] 变量不存在: {variable_name}")
        return None
    
    def set_variable(self, variable_name: str, value: Any):
        """
        手动设置变量
        
        Args:
            variable_name: 变量名
            value: 变量值
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._variables[variable_name] = value
        logger_manager.info(f"[框架] 设置变量: {variable_name} = {value}")
        return self
    
    def assert_status_code(self, status_code):
        """
        断言状态码
        
        Args:
            status_code: 期望的状态码或状态码列表
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法断言状态码：未发送请求或请求失败")
            raise AssertionError("无法断言状态码：未发送请求或请求失败")
        
        actual_status = self._response.status_code if hasattr(self._response, 'status_code') else self._response.status
        try:
            if isinstance(status_code, list):
                assert actual_status in status_code, \
                    f"状态码断言失败：期望 {status_code} 中的一个，实际 {actual_status}"
                logger_manager.info(f"[框架] 状态码断言成功：{actual_status} in {status_code}")
            else:
                assert actual_status == status_code, \
                    f"状态码断言失败：期望 {status_code}，实际 {actual_status}"
                logger_manager.info(f"[框架] 状态码断言成功：{actual_status} == {status_code}")
        except AssertionError as e:
            logger_manager.error(f"[框架] {str(e)}")
            raise
        
        return self
    
    def assert_json_path(self, json_path: str, expected_value: Any, 
                        comparator: str = 'eq', tolerance: float = None):
        """
        断言JSON路径的值，支持多种比较方式
        
        Args:
            json_path: JSON路径（使用点号分隔，如 'data.user.id'）
            expected_value: 期望的值
            comparator: 比较器类型 ('eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'contains', 'startswith', 'endswith')
            tolerance: 数值比较的容差（用于浮点数比较）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法断言JSON路径：未发送请求或请求失败")
            raise AssertionError("无法断言JSON路径：未发送请求或请求失败")
        
        try:
            # 先使用extract方法获取值，复用其路径解析逻辑
            temp_var = f"_assert_temp_{time.time()}"
            self.extract(temp_var, json_path=json_path)
            
            if temp_var not in self._variables:
                raise AssertionError(f"[框架] JSON路径不存在: {json_path}")
            
            actual_value = self._variables[temp_var]
            
            # 根据比较器执行断言
            passed = False
            error_msg = ""
            
            if comparator == 'eq':
                if tolerance is not None and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
                    passed = abs(actual_value - expected_value) <= tolerance
                    error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望 {expected_value} ± {tolerance}，实际 {actual_value}"
                else:
                    passed = actual_value == expected_value
                    error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望 {expected_value}，实际 {actual_value}"
            
            elif comparator == 'neq':
                passed = actual_value != expected_value
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望不等于 {expected_value}，实际等于 {actual_value}"
            
            elif comparator == 'gt':
                passed = actual_value > expected_value
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望 > {expected_value}，实际 {actual_value}"
            
            elif comparator == 'gte':
                passed = actual_value >= expected_value
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望 >= {expected_value}，实际 {actual_value}"
            
            elif comparator == 'lt':
                passed = actual_value < expected_value
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望 < {expected_value}，实际 {actual_value}"
            
            elif comparator == 'lte':
                passed = actual_value <= expected_value
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望 <= {expected_value}，实际 {actual_value}"
            
            elif comparator == 'contains':
                if isinstance(actual_value, (str, list, dict)):
                    if isinstance(actual_value, dict):
                        passed = expected_value in actual_value
                    else:
                        passed = expected_value in actual_value
                else:
                    passed = False
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望包含 {expected_value}，实际 {actual_value}"
            
            elif comparator == 'startswith':
                if isinstance(actual_value, str):
                    passed = actual_value.startswith(expected_value)
                else:
                    passed = False
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望以 {expected_value} 开头，实际 {actual_value}"
            
            elif comparator == 'endswith':
                if isinstance(actual_value, str):
                    passed = actual_value.endswith(expected_value)
                else:
                    passed = False
                error_msg = f"JSON路径断言失败：路径 '{json_path}'，期望以 {expected_value} 结尾，实际 {actual_value}"
            
            if not passed:
                logger_manager.error(f"[框架] {error_msg}")
                raise AssertionError(error_msg)
            
            logger_manager.info(f"[框架] JSON路径断言成功：路径 '{json_path}' 值为 {actual_value}")
            
        except AssertionError:
            raise
        except (ValueError, TypeError) as e:
            logger_manager.error(f"[框架] JSON解析失败: {str(e)}")
            raise AssertionError(f"JSON解析失败: {str(e)}")
        
        return self
    
    def assert_json_schema(self, schema: Dict[str, Any]):
        """
        断言响应JSON符合指定的schema
        
        Args:
            schema: JSON schema定义
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法断言JSON schema：未发送请求或请求失败")
            raise AssertionError("无法断言JSON schema：未发送请求或请求失败")
        
        try:
            # 简单的schema验证实现
            if hasattr(self._response, 'json'):
                json_data = self._response.json()
            else:
                import json as json_module
                json_data = json_module.loads(self._response._content)
            
            # 递归验证schema
            def validate_schema(data, schema_def):
                if isinstance(schema_def, dict):
                    if not isinstance(data, dict):
                        raise AssertionError(f"期望类型 dict，实际类型 {type(data).__name__}")
                    
                    for key, value_schema in schema_def.items():
                        if key in data:
                            validate_schema(data[key], value_schema)
                        elif value_schema.get('required', False):
                            raise AssertionError(f"缺少必填字段: {key}")
                
                elif isinstance(schema_def, list):
                    if not isinstance(data, list):
                        raise AssertionError(f"期望类型 list，实际类型 {type(data).__name__}")
                    
                    for item in data:
                        validate_schema(item, schema_def[0])
                
                elif isinstance(schema_def, type):
                    if not isinstance(data, schema_def):
                        raise AssertionError(f"期望类型 {schema_def.__name__}，实际类型 {type(data).__name__}")
            
            validate_schema(json_data, schema)
            logger_manager.info(f"[框架] JSON schema断言成功")
            
        except AssertionError:
            raise
        except (ValueError, TypeError) as e:
            logger_manager.error(f"[框架] JSON schema验证失败: {str(e)}")
            raise AssertionError(f"JSON schema验证失败: {str(e)}")
        
        return self
    
    def assert_response_text(self, expected_text: str, comparator: str = 'contains'):
        """
        断言响应文本
        
        Args:
            expected_text: 期望的文本
            comparator: 比较器 ('contains', 'eq', 'startswith', 'endswith')
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法断言响应文本：未发送请求或请求失败")
            raise AssertionError("无法断言响应文本：未发送请求或请求失败")
        
        try:
            response_text = self._response.text if hasattr(self._response, 'text') else \
                          self._response._content.decode('utf-8', errors='ignore')
            
            passed = False
            error_msg = ""
            
            if comparator == 'contains':
                passed = expected_text in response_text
                error_msg = f"响应文本断言失败：期望包含 {expected_text}，实际不包含"
            
            elif comparator == 'eq':
                passed = response_text == expected_text
                error_msg = f"响应文本断言失败：文本不匹配"
            
            elif comparator == 'startswith':
                passed = response_text.startswith(expected_text)
                error_msg = f"响应文本断言失败：期望以 {expected_text} 开头"
            
            elif comparator == 'endswith':
                passed = response_text.endswith(expected_text)
                error_msg = f"响应文本断言失败：期望以 {expected_text} 结尾"
            
            if not passed:
                logger_manager.error(f"[框架] {error_msg}")
                raise AssertionError(error_msg)
            
            logger_manager.info(f"[框架] 响应文本断言成功")
            
        except AssertionError:
            raise
        except Exception as e:
            logger_manager.error(f"[框架] 响应文本断言失败: {str(e)}")
            raise AssertionError(f"响应文本断言失败: {str(e)}")
        
        return self
    
    def assert_response_header(self, header_name: str, expected_value: Any = None,
                             comparator: str = 'eq'):
        """
        断言响应头
        
        Args:
            header_name: 响应头名称
            expected_value: 期望的值（可选，不提供则只检查存在性）
            comparator: 比较器类型 ('eq', 'contains')
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法断言响应头：未发送请求或请求失败")
            raise AssertionError("无法断言响应头：未发送请求或请求失败")
        
        try:
            headers = self._response.headers
            
            if header_name not in headers:
                logger_manager.error(f"[框架] 响应头中未找到: {header_name}")
                raise AssertionError(f"响应头中未找到: {header_name}")
            
            if expected_value is not None:
                actual_value = headers[header_name]
                passed = False
                
                if comparator == 'eq':
                    passed = actual_value == expected_value
                elif comparator == 'contains':
                    passed = expected_value in actual_value
                
                if not passed:
                    error_msg = f"响应头断言失败：{header_name} 期望 {expected_value}，实际 {actual_value}"
                    logger_manager.error(f"[框架] {error_msg}")
                    raise AssertionError(error_msg)
            
            logger_manager.info(f"[框架] 响应头断言成功：{header_name}")
            
        except AssertionError:
            raise
        except Exception as e:
            logger_manager.error(f"[框架] 响应头断言失败: {str(e)}")
            raise AssertionError(f"响应头断言失败: {str(e)}")
        
        return self
    
    def assert_response_time(self, max_time_ms):
        """
        断言响应时间
        
        Args:
            max_time_ms: 最大响应时间（毫秒）
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if self._response_time == 0:
            logger_manager.error("[框架] 无法断言响应时间：未发送请求或请求失败")
            raise AssertionError("无法断言响应时间：未发送请求或请求失败")
        
        try:
            assert self._response_time <= max_time_ms, \
                f"响应时间断言失败：期望 <= {max_time_ms}ms，实际 {self._response_time:.2f}ms"
            logger_manager.info(f"[框架] 响应时间断言成功：{self._response_time:.2f}ms <= {max_time_ms}ms")
        except AssertionError as e:
            logger_manager.error(f"[框架] {str(e)}")
            raise
        
        return self
    
    def assert_custom(self, assertion_func: Callable):
        """
        执行自定义断言函数
        
        Args:
            assertion_func: 断言函数，接收响应对象和变量字典作为参数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if not self._response:
            logger_manager.error("[框架] 无法执行自定义断言：未发送请求或请求失败")
            raise AssertionError("无法执行自定义断言：未发送请求或请求失败")
        
        try:
            result = assertion_func(self._response, self._variables)
            if result is not True:
                error_msg = result if isinstance(result, str) else "自定义断言失败"
                logger_manager.error(f"[框架] {error_msg}")
                raise AssertionError(error_msg)
            logger_manager.info(f"[框架] 自定义断言成功")
        except AssertionError:
            raise
        except Exception as e:
            logger_manager.error(f"[框架] 自定义断言执行失败: {str(e)}")
            raise AssertionError(f"自定义断言执行失败: {str(e)}")
        
        return self
    
    def get_response(self):
        """
        获取响应对象
        
        Returns:
            requests.Response: 响应对象
        """
        return self._response
    
    def get_variables(self):
        """
        获取所有提取的变量
        
        Returns:
            dict: 变量字典
        """
        return self._variables.copy()
    
    def reset(self):
        """
        重置所有状态，开始新的测试
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        logger_manager.info(f"[框架] 重置测试状态")
        self._reset_state()
        return self
    
    def get_stream_buffer(self) -> List[str]:
        """
        获取流式响应缓冲区内容
        
        Returns:
            List[str]: 流式响应块列表
        """
        return self._stream_buffer.copy()
    
    def get_parsed_stream_content(self) -> List[str]:
        """
        获取解析后的流式响应内容（适用于SSE或JSON格式）
        
        Returns:
            List[str]: 解析后的内容块列表
        """
        if hasattr(self, '_parsed_stream_content'):
            return self._parsed_stream_content.copy()
        return []
    
    def get_full_stream_content(self) -> str:
        """
        获取完整的流式响应内容
        
        Returns:
            str: 合并后的流式响应内容
        """
        return ''.join(self._stream_buffer)
    
    def get_full_parsed_stream_content(self) -> str:
        """
        获取完整的解析后流式响应内容
        
        Returns:
            str: 合并后的解析后内容
        """
        if hasattr(self, '_parsed_stream_content'):
            return ''.join(self._parsed_stream_content)
        return ''
    
    def reset_stream(self):
        """
        重置流式响应缓冲区
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._stream_buffer = []
        if hasattr(self, '_parsed_stream_content'):
            self._parsed_stream_content = []
        logger_manager.info(f"[框架] 流式响应缓冲区已重置")
        return self
    
    def tag(self, *tags):
        """
        为请求添加标签，用于后续过滤和查询
        
        Args:
            *tags: 要添加的标签列表
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        for tag in tags:
            if tag not in self._tags:
                self._tags.append(tag)
        return self
    
    def set_test_context(self, key: str, value: Any):
        """
        设置测试上下文，用于存储与测试相关的额外信息
        
        Args:
            key: 上下文键名
            value: 上下文值
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_context[key] = value
        return self
    
    def get_last_record_id(self):
        """
        获取最近一次请求的记录ID
        
        Returns:
            int: 记录ID
        """
        return self._last_record_id
    
    def enable_async(self):
        """
        启用异步模式
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._async_mode = True
        return self
    
    def disable_async(self):
        """
        禁用异步模式
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._async_mode = False
        return self
        
    def _save_request_config(self):
        """
        保存当前请求配置，用于性能测试
        
        Returns:
            Dict[str, Any]: 请求配置字典
        """
        self._performance_request_config = {
            'url': self._url,
            'method': self._method,
            'headers': self._headers.copy(),
            'params': self._params.copy(),
            'data': self._data,
            'json': self._json,
            'files': self._files,
            'cookies': self._cookies.copy(),
            'auth': self._auth,
            'timeout': self._timeout,
            'verify': self._verify_ssl,
            'proxies': self._proxies,
            'stream': self._is_stream,
            'stream_handler': self._stream_handler,
            'agent_params': self._agent_params.copy(),
            'pre_request_hooks': self._pre_request_hooks.copy(),
            'post_response_hooks': self._post_response_hooks.copy(),
            'base_url': self._base_url
        }
        return self._performance_request_config
        
    def enable_blind_order(self):
        """
        启用盲顺序调用模式
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._blind_order_mode = True
        logger_manager.info(f"[框架] 盲顺序调用模式已启用")
        return self
        
    def disable_blind_order(self):
        """
        禁用盲顺序调用模式
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._blind_order_mode = False
        logger_manager.info(f"[框架] 盲顺序调用模式已禁用")
        return self
        
    def queue_request(self):
        """
        将当前请求加入队列，用于盲顺序执行
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        request_config = self._save_request_config()
        self._request_queue.append({
            'config': request_config,
            'step_name': self._step_name
        })
        logger_manager.info(f"[框架] 请求已加入队列: {self._step_name} - {self._method} {self._url}")
        # 重置状态以便配置下一个请求
        self._reset_state()
        return self
        
    def execute_queue(self):
        """
        执行队列中的所有请求（盲顺序执行）
        
        Returns:
            self: 返回实例自身以支持链式调用
        """
        results = []
        logger_manager.info(f"[框架] 开始执行请求队列，共 {len(self._request_queue)} 个请求")
        
        for i, req in enumerate(self._request_queue):
            logger_manager.info(f"[框架] 执行队列请求 {i+1}/{len(self._request_queue)}: {req['step_name']}")
            
            # 恢复请求配置
            config = req['config']
            self._url = config['url']
            self._method = config['method']
            self._headers = config['headers'].copy()
            self._params = config['params'].copy()
            self._data = config['data']
            self._json = config['json']
            self._files = config['files']
            self._cookies = config['cookies'].copy()
            self._auth = config['auth']
            self._timeout = config['timeout']
            self._verify_ssl = config['verify']
            self._proxies = config['proxies']
            self._is_stream = config['stream']
            self._stream_handler = config['stream_handler']
            self._agent_params = config['agent_params'].copy()
            self._pre_request_hooks = config['pre_request_hooks'].copy()
            self._post_response_hooks = config['post_response_hooks'].copy()
            self._base_url = config['base_url']
            
            # 发送请求
            result = self.send()
            results.append(result)
        
        logger_manager.info(f"[框架] 请求队列执行完成")
        # 清空队列
        self._request_queue = []
        return self
        
    def performance(self):
        """
        创建性能测试运行器并配置
        
        Returns:
            PerformanceRunner: 配置好的性能测试运行器
        """
        # 保存当前请求配置
        request_config = self._save_request_config()
        
        # 创建性能测试运行器
        runner = create_performance_runner()
        
        # 配置性能测试运行器的请求信息
        runner.set_request(
            method=self._method,
            url=self._url,
            headers=self._headers,
            params=self._params,
            data=self._data,
            json=self._json,
            cookies=self._cookies,
            auth=self._auth,
            timeout=self._timeout,
            verify=self._verify_ssl,
            proxies=self._proxies,
            base_url=self._base_url
        )
        
        logger_manager.info(f"[框架] 性能测试运行器已创建，配置请求: {self._method} {self._url}")
        return runner


def api():
    """
    创建一个新的API适配器实例
    
    Returns:
        ApiAdapter: 新的适配器实例
    """
    return ApiAdapter()

def ai_api(model: str = None, system_prompt: str = None):
    """
    创建专门用于AI接口测试的API适配器实例
    
    Args:
        model: 默认使用的模型名称
        system_prompt: 默认的系统提示词
        
    Returns:
        ApiAdapter: 配置好的API适配器实例，适合AI接口测试
    """
    adapter = ApiAdapter()
    
    # 设置默认的AI相关配置
    if model:
        adapter.agent_params({'model': model})
    
    # 设置默认的系统提示词（如果提供）
    if system_prompt:
        adapter.ai_prompt("", system_prompt)
        # 清空用户提示词，只保留系统提示词
        if adapter._json and 'messages' in adapter._json:
            for msg in adapter._json['messages']:
                if msg.get('role') == 'user':
                    msg['content'] = ""
    
    # 从配置中获取默认的AI API密钥（如果有）
    api_key = config_manager.get('default_ai_api_key', '')
    if api_key:
        adapter.headers({'Authorization': f'Bearer {api_key}'})
    
    # 从配置中获取默认的AI API URL（如果有）
    api_url = config_manager.get('default_ai_api_url', '')
    if api_url:
        adapter._url = api_url
    
    return adapter

# 导出数据存储相关的便捷函数
def filter_response_data(**filters):
    """
    根据条件过滤响应数据
    
    Args:
        **filters: 过滤条件，如status_code=200, test_name="API测试"
        
    Returns:
        List[Dict]: 过滤后的响应数据列表
    """
    return data_storage_manager.filter_responses(**filters)

def export_responses(output_file: str, format_type: str = 'json', **filters):
    """
    导出响应数据到文件
    
    Args:
        output_file: 输出文件路径
        format_type: 输出格式，支持'json'或'csv'
        **filters: 过滤条件
        
    Returns:
        str: 导出文件的路径
    """
    # 使用Path对象处理文件路径，确保跨平台兼容性
    from pathlib import Path
    output_path = Path(output_file)
    
    # 根据格式类型调用相应的导出方法
    if format_type.lower() == 'csv':
        result = data_storage_manager.export_to_csv(filename=output_path.name, filter_condition=lambda record: _filter_record(record, **filters))
    else:  # 默认使用json格式
        result = data_storage_manager.export_to_json(filename=output_path.name, filter_condition=lambda record: _filter_record(record, **filters))
    
    return result

def _filter_record(record: Dict[str, Any], **filters) -> bool:
    """
    根据过滤条件筛选记录
    
    Args:
        record: 要筛选的记录
        **filters: 过滤条件
        
    Returns:
        bool: 是否满足过滤条件
    """
    # 实现过滤逻辑
    for key, value in filters.items():
        if key in record and record[key] != value:
            return False
    return True

def clear_storage():
    """
    清空所有存储的响应数据
    """
    return data_storage_manager.clear_all()