"""
性能测试运行器模块

提供API性能测试的核心运行功能，支持TPS、QPS测试、并发测试、爬坡测试等多种性能测试模式。
"""

import time
import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, Callable, Union, List, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field

# 避免循环导入
if TYPE_CHECKING:
    from apitestkit.adapter.api_adapter import ApiAdapter

from apitestkit.core.logger import logger_manager
from apitestkit.core.config import config_manager
from apitestkit.performance.load_generator import LoadGenerator
from apitestkit.performance.metrics_collector import MetricsCollector
from apitestkit.performance.report_generator import PerformanceReportGenerator

@dataclass
class TestConfig:
    """
    性能测试配置类
    """
    test_type: str = 'tps'  # tps, qps, concurrent, ramp_up, stability
    duration: int = 60  # 测试持续时间(秒)
    concurrent_users: int = 10  # 并发用户数
    ramp_up_time: int = 0  # 爬坡时间(秒)
    ramp_up_steps: int = 0  # 爬坡步数
    target_tps: Optional[int] = None  # 目标TPS
    target_qps: Optional[int] = None  # 目标QPS
    timeout: int = 30  # 请求超时时间(秒)
    think_time: float = 0  # 思考时间(秒)
    stop_on_error: bool = False  # 遇到错误时是否停止测试
    collect_metrics: bool = True  # 是否收集详细指标
    
    # 线程控制配置
    before_concurrent: int = 1  # before任务并发数
    test_concurrent: Optional[int] = None  # 测试任务并发数（None表示自动计算）
    after_concurrent: int = 1  # after任务并发数
    max_thread_pool_size: int = 1000  # 最大线程池大小
    
    # 错误处理配置
    max_retries: int = 0  # 任务失败最大重试次数
    error_threshold: Optional[int] = None  # 错误数量阈值
    error_rate_threshold: Optional[float] = None  # 错误率阈值
    
    # 长稳测试配置
    stability_duration: int = 3600  # 长稳测试持续时间(秒)，默认1小时
    stability_check_interval: int = 600  # 长稳测试检查间隔(秒)，默认10分钟
    stability_threshold: Dict[str, Any] = field(default_factory=lambda: {
        'error_rate': 0.05,  # 错误率阈值，默认5%
        'response_time_p95': 1.0,  # P95响应时间阈值(秒)
        'response_time_p99': 2.0,  # P99响应时间阈值(秒)
    })  # 长稳测试性能阈值

class PerformanceRunner:
    """
    性能测试运行器
    
    提供API性能测试的核心运行功能，支持多种性能测试模式。
    """
    
    def __init__(self):
        """
        初始化性能测试运行器
        """
        self._test_config = TestConfig()
        self._api_adapter = None
        self._test_func = None
        self._before_func = None
        self._after_func = None
        self._metrics_collector = None
        self._load_generator = None
        self._report_generator = None
        self._results = None
        self._running = False
        self._method = "GET"  # 初始化_method属性
        self._url = ""  # 初始化_url属性
        
    def test_type(self, test_type: str):
        """
        设置测试类型
        
        Args:
            test_type: 测试类型，可选值: tps, qps, concurrent, ramp_up, stability
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        if test_type not in ['tps', 'qps', 'concurrent', 'ramp_up', 'stability']:
            raise ValueError(f"不支持的测试类型: {test_type}")
        self._test_config.test_type = test_type
        return self
    
    def duration(self, seconds: int):
        """
        设置测试持续时间
        
        Args:
            seconds: 测试持续时间(秒)
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.duration = seconds
        return self
    
    def concurrent(self, concurrent_users, duration=60, ramp_up_time=0):
        """
        设置并发用户数测试参数
        
        Args:
            concurrent_users: 并发用户数
            duration: 测试持续时间(秒)
            ramp_up_time: 爬升时间(秒)
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当参数不合法时
        """
        # 参数验证
        if concurrent_users <= 0:
            raise ValueError("并发用户数必须大于0")
            
        if duration <= 0:
            raise ValueError("测试持续时间必须大于0")
            
        if ramp_up_time < 0:
            raise ValueError("爬升时间不能为负数")
            
        self._test_config.test_type = 'concurrent'
        self._test_config.concurrent_users = concurrent_users
        self._test_config.duration = duration
        self._test_config.ramp_up_time = ramp_up_time
        return self
    
    def concurrent_users(self, users: int):
        """
        设置并发用户数
        
        Args:
            users: 并发用户数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.concurrent_users = users
        return self
    
    def ramp_up(self, time_seconds: int, steps: int = 1):
        """
        设置爬坡配置
        
        Args:
            time_seconds: 爬坡总时间(秒)
            steps: 爬坡步数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.ramp_up_time = time_seconds
        self._test_config.ramp_up_steps = steps
        self._test_config.test_type = 'ramp_up'
        return self
    
    def target_tps(self, tps: int):
        """
        设置目标TPS
        
        Args:
            tps: 目标TPS值
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.target_tps = tps
        self._test_config.test_type = 'tps'
        return self
    
    def tps(self, target_tps, duration=60, ramp_up_time=0, ramp_up_steps=1):
        """
        设置TPS(每秒事务数)测试参数
        
        Args:
            target_tps: 目标TPS值
            duration: 测试持续时间(秒)
            ramp_up_time: 爬升时间(秒)
            ramp_up_steps: 爬升步数
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当参数不合法时
        """
        # 参数验证
        if target_tps < 0:
            raise ValueError("TPS值不能为负数")
            
        if duration <= 0:
            raise ValueError("测试持续时间必须大于0")
            
        if ramp_up_time < 0:
            raise ValueError("爬升时间不能为负数")
            
        if ramp_up_steps < 1:
            raise ValueError("爬升到步数必须大于等于1")
            
        self._test_config.test_type = 'tps'
        self._test_config.target_tps = target_tps
        self._test_config.duration = duration
        self._test_config.ramp_up_time = ramp_up_time
        self._test_config.ramp_up_steps = ramp_up_steps
        return self
    
    def target_qps(self, qps: int):
        """
        设置目标QPS
        
        Args:
            qps: 目标QPS值
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.target_qps = qps
        self._test_config.test_type = 'qps'
        return self
    
    def qps(self, target_qps, duration=60, ramp_up_time=0, ramp_up_steps=1):
        """
        设置QPS(每秒查询数)测试参数
        
        Args:
            target_qps: 目标QPS值
            duration: 测试持续时间(秒)
            ramp_up_time: 爬升时间(秒)
            ramp_up_steps: 爬升步数
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当参数不合法时
        """
        # 参数验证
        if target_qps < 0:
            raise ValueError("QPS值不能为负数")
            
        if duration <= 0:
            raise ValueError("测试持续时间必须大于0")
            
        if ramp_up_time < 0:
            raise ValueError("爬升时间不能为负数")
            
        if ramp_up_steps < 1:
            raise ValueError("爬升到步数必须大于等于1")
            
        self._test_config.test_type = 'qps'
        self._test_config.target_qps = target_qps
        self._test_config.duration = duration
        self._test_config.ramp_up_time = ramp_up_time
        self._test_config.ramp_up_steps = ramp_up_steps
        return self
    
    def stability(self, duration=3600, concurrent_users=10, check_interval=600, **thresholds):
        """
        设置长稳测试参数
        
        Args:
            duration: 长稳测试持续时间(秒)，默认3600秒(1小时)
            concurrent_users: 并发用户数
            check_interval: 检查间隔(秒)，默认600秒(10分钟)
            **thresholds: 性能阈值参数
                error_rate: 错误率阈值，默认0.05(5%)
                response_time_p95: P95响应时间阈值(秒)，默认1.0秒
                response_time_p99: P99响应时间阈值(秒)，默认2.0秒
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当参数不合法时
        """
        # 参数验证
        if duration <= 0:
            raise ValueError("测试持续时间必须大于0")
            
        if concurrent_users <= 0:
            raise ValueError("并发用户数必须大于0")
            
        if check_interval <= 0:
            raise ValueError("检查间隔必须大于0")
            
        # 设置基础参数
        self._test_config.test_type = 'stability'
        self._test_config.stability_duration = duration
        self._test_config.concurrent_users = concurrent_users
        self._test_config.stability_check_interval = check_interval
        
        # 更新阈值配置
        threshold_config = self._test_config.stability_threshold.copy()
        if thresholds:
            threshold_config.update(thresholds)
            
        # 验证阈值参数
        if 'error_rate' in threshold_config and (threshold_config['error_rate'] < 0 or threshold_config['error_rate'] > 1):
            raise ValueError("错误率阈值必须在0到1之间")
            
        if 'response_time_p95' in threshold_config and threshold_config['response_time_p95'] < 0:
            raise ValueError("P95响应时间阈值不能为负数")
            
        if 'response_time_p99' in threshold_config and threshold_config['response_time_p99'] < 0:
            raise ValueError("P99响应时间阈值不能为负数")
            
        self._test_config.stability_threshold = threshold_config
        return self
    
    def timeout(self, seconds: int):
        """
        设置请求超时时间
        
        Args:
            seconds: 请求超时时间(秒)
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.timeout = seconds
        return self
    
    def think_time(self, seconds: float):
        """
        设置思考时间
        
        Args:
            seconds: 思考时间(秒)
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.think_time = seconds
        return self
    
    def stop_on_error(self, stop: bool = True):
        """
        设置遇到错误时是否停止测试
        
        Args:
            stop: 是否停止
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.stop_on_error = stop
        return self
    
    def ramp_up_steps(self, steps: int):
        """
        设置爬坡步数
        
        Args:
            steps: 爬坡步数
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当步数小于1时
        """
        if steps < 1:
            raise ValueError("爬坡步数必须大于等于1")
        self._test_config.ramp_up_steps = steps
        return self
    
    def ramp_up_time(self, seconds: int):
        """
        设置爬坡总时间
        
        Args:
            seconds: 爬坡总时间(秒)
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当时间小于0时
        """
        if seconds < 0:
            raise ValueError("爬坡时间不能为负数")
        self._test_config.ramp_up_time = seconds
        return self
    
    def collect_metrics(self, collect: bool = True):
        """
        设置是否收集详细指标
        
        Args:
            collect: 是否收集详细指标
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_config.collect_metrics = collect
        return self
    
    def set_request(self, method: str = 'GET', url: str = None, **kwargs):
        """
        设置HTTP请求参数
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        # 延迟导入以避免循环导入
        from apitestkit.adapter.api_adapter import ApiAdapter
        
        # 创建新的ApiAdapter实例并设置参数
        self._api_adapter = ApiAdapter()
        
        # 确保_method属性被正确设置
        self._api_adapter._method = method.upper()
        self._method = method.upper()
        
        # 确保_url属性被正确设置
        if url:
            self._api_adapter._url = url
            self._url = url
        
        # 根据ApiAdapter的实际接口调整方法调用
        if hasattr(self._api_adapter, 'get') and method.upper() == 'GET':
            self._api_adapter.get(url)
        elif hasattr(self._api_adapter, 'post') and method.upper() == 'POST':
            self._api_adapter.post(url)
        elif hasattr(self._api_adapter, 'put') and method.upper() == 'PUT':
            self._api_adapter.put(url)
        elif hasattr(self._api_adapter, 'delete') and method.upper() == 'DELETE':
            self._api_adapter.delete(url)
        else:
            # 如果没有特定HTTP方法的方法，尝试通用方法
            if url:
                if hasattr(self._api_adapter, 'url'):
                    self._api_adapter.url(url)
                elif hasattr(self._api_adapter, 'set_url'):
                    self._api_adapter.set_url(url)
            
            # 设置method属性（如果存在）
            if hasattr(self._api_adapter, 'method'):
                self._api_adapter.method(method)
            elif hasattr(self._api_adapter, 'set_method'):
                self._api_adapter.set_method(method)
        
        # 尝试设置其他参数
        for key, value in kwargs.items():
            setter_name = f'set_{key}'
            if hasattr(self._api_adapter, setter_name):
                getattr(self._api_adapter, setter_name)(value)
            elif hasattr(self._api_adapter, key):
                getattr(self._api_adapter, key)(value)
        
        return self
    
    def api_call(self, adapter):
        """
        设置API调用适配器
        
        Args:
            adapter: ApiAdapter实例
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._api_adapter = adapter
        return self
    
    def test_function(self, func: Callable, *args, **kwargs):
        """
        设置测试函数
        
        Args:
            func: 测试函数
            *args: 测试函数的位置参数
            **kwargs: 测试函数的关键字参数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._test_func = func
        self._test_args = args
        self._test_kwargs = kwargs
        self._test_case = None  # 清除之前可能设置的测试用例
        return self
        
    def test_case(self, test_case):
        """
        设置apitest用例作为测试事务
        
        Args:
            test_case: TestCase实例，作为事务进行性能测试
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        from apitestkit.test.test_case import TestCase
        
        if not isinstance(test_case, TestCase):
            raise TypeError("test_case必须是TestCase类型的实例")
        
        self._test_case = test_case
        self._test_func = None  # 清除之前可能设置的测试函数
        self._test_args = ()
        self._test_kwargs = {}
        return self
    
    def before_task(self, func: Callable):
        """
        设置测试前执行的任务函数
        
        Args:
            func: 测试前任务函数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._before_func = func
        return self
    
    def after_task(self, func: Callable):
        """
        设置测试后执行的任务函数
        
        Args:
            func: 测试后任务函数
            
        Returns:
            self: 返回实例自身以支持链式调用
        """
        self._after_func = func
        return self
    
    def set_before_concurrent(self, concurrent: int):
        """
        设置before任务的并发数
        
        Args:
            concurrent: 并发数
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当并发数小于等于0时
        """
        if concurrent <= 0:
            raise ValueError("并发数必须大于0")
        self._test_config.before_concurrent = concurrent
        return self
    
    def set_after_concurrent(self, concurrent: int):
        """
        设置after任务的并发数
        
        Args:
            concurrent: 并发数
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当并发数小于等于0时
        """
        if concurrent <= 0:
            raise ValueError("并发数必须大于0")
        self._test_config.after_concurrent = concurrent
        return self
    
    def set_max_thread_pool_size(self, size: int):
        """
        设置最大线程池大小
        
        Args:
            size: 线程池大小
            
        Returns:
            self: 返回实例自身以支持链式调用
            
        Raises:
            ValueError: 当线程池大小小于等于0时
        """
        if size <= 0:
            raise ValueError("线程池大小必须大于0")
        self._test_config.max_thread_pool_size = size
        return self
    

    
    def run(self):
        """
        执行性能测试
        
        Returns:
            Dict[str, Any]: 测试结果，包含主测试结果和before/after任务结果
        """
        if not self._api_adapter and not self._test_func and not self._test_case:
            raise ValueError("必须设置api_call、test_function或test_case")
        
        # 初始化指标收集器
        self._metrics_collector = MetricsCollector()
        
        # 初始化负载生成器
        self._load_generator = LoadGenerator(self._test_config)
        
        # 根据测试类型执行测试
        try:
            if self._test_case:
                # 使用测试用例作为事务
                logger_manager.info(f"[性能测试] 使用apitest用例作为事务: {self._test_case.test_name}")
                test_func = self._create_test_case_func()
            elif self._api_adapter:
                test_func = self._create_api_test_func()
            else:
                test_func = self._test_func
            
            logger_manager.info(f"[性能测试] 开始执行{self._test_config.test_type}测试")
            logger_manager.info(f"[性能测试] 配置: {self._test_config}")
            
            self._running = True
            start_time = time.time()
            
            # 执行测试并收集结果
            if self._test_config.test_type == 'ramp_up':
                self._results = self._run_ramp_up_test(test_func)
            elif self._test_config.test_type == 'tps':
                self._results = self._run_tps_test(test_func)
            elif self._test_config.test_type == 'qps':
                self._results = self._run_qps_test(test_func)
            elif self._test_config.test_type == 'stability':
                self._results = self._run_stability_test(test_func)
            else:  # concurrent
                self._results = self._run_concurrent_test(test_func)
            
            duration = time.time() - start_time
            logger_manager.info(f"[性能测试] 测试完成，总耗时: {duration:.2f}秒")
            
            # 生成测试报告
            self._report_generator = PerformanceReportGenerator(
                self._results, 
                self._metrics_collector.get_all_metrics(),
                self._test_config
            )
            
            return self._results
            
        except Exception as e:
            logger_manager.error(f"[性能测试] 测试失败: {str(e)}")
            raise
        finally:
            self._running = False
    
    def _create_api_test_func(self):
        """
        创建API测试函数
        
        Returns:
            Callable: 测试函数
        """
        def api_test_func():
            start_time = time.time()
            try:
                # 克隆一个新的适配器实例以避免状态冲突
                adapter = ApiAdapter()
                # 复制配置
                adapter._url = self._api_adapter._url
                adapter._method = self._api_adapter._method
                adapter._headers = self._api_adapter._headers.copy()
                adapter._params = self._api_adapter._params.copy()
                adapter._data = self._api_adapter._data
                adapter._json = self._api_adapter._json
                adapter._cookies = self._api_adapter._cookies.copy()
                adapter._auth = self._api_adapter._auth
                adapter._timeout = self._api_adapter._timeout or self._test_config.timeout
                adapter._verify_ssl = self._api_adapter._verify_ssl
                
                # 执行请求
                result = adapter.send()
                
                # 记录指标
                response_time = adapter._response_time
                status_code = adapter._response.status_code
                
                self._metrics_collector.record_request(
                    start_time, 
                    time.time(),
                    response_time, 
                    status_code,
                    success=200 <= status_code < 400
                )
                
                return {
                    'success': True,
                    'response_time': response_time,
                    'status_code': status_code,
                    'error': None
                }
                
            except Exception as e:
                self._metrics_collector.record_request(
                    start_time, 
                    time.time(),
                    (time.time() - start_time) * 1000, 
                    None,
                    success=False,
                    error=str(e)
                )
                return {
                    'success': False,
                    'response_time': (time.time() - start_time) * 1000,
                    'status_code': None,
                    'error': str(e)
                }
        
        return api_test_func
        
    def _create_test_case_func(self):
        """
        创建测试用例执行函数，将TestCase作为事务执行
        
        Returns:
            Callable: 测试用例执行函数
        """
        import time
        import copy
        from apitestkit.test.test_case import TestCase
        
        # 创建测试用例的副本，确保每个线程都有独立的测试用例实例
        original_test_case = self._test_case
        
        def test_func():
            """
            测试用例执行函数
            
            Returns:
                Dict[str, Any]: 测试结果
            """
            start_time = time.time()
            result = {
                'success': False,
                'start_time': start_time,
                'end_time': 0,
                'duration': 0,
                'error': None,
                'error_type': None,
                'transaction_name': original_test_case.test_name,
                'api_calls': []  # 记录事务中的API调用
            }
            
            try:
                # 为每个请求创建一个新的测试用例实例，避免线程安全问题
                test_case = copy.deepcopy(original_test_case)
                
                # 保存原始的step方法，用于拦截步骤执行
                original_step = test_case.step
                
                # 重写step方法以收集API调用性能数据
                def wrapped_step(name, func):
                    step_start = time.time()
                    step_result = original_step(name, func)
                    step_duration = time.time() - step_start
                    
                    # 记录步骤信息
                    result['api_calls'].append({
                        'name': name,
                        'duration': step_duration,
                        'success': step_result.get('status') == 'success' if isinstance(step_result, dict) else True
                    })
                    
                    return step_result
                
                test_case.step = wrapped_step
                
                # 执行测试用例
                test_result = test_case.run()
                
                # 根据测试结果设置事务结果
                if test_result.status == 'passed':
                    result['success'] = True
                else:
                    result['success'] = False
                    result['error'] = '; '.join(test_result.errors + test_result.failures[:3])  # 限制错误信息长度
                    result['error_type'] = 'business_error'
                
            except Exception as e:
                result['error'] = str(e)
                result['error_type'] = 'other_error'
            finally:
                # 计算执行时间
                result['end_time'] = time.time()
                result['duration'] = result['end_time'] - result['start_time']
                
                # 调用思考时间
                if self._think_time > 0:
                    time.sleep(self._think_time)
            
            return result
        
        return test_func
    
    def _run_concurrent_test(self, test_func: Callable):
        """
        运行并发测试
        
        Args:
            test_func: 测试函数
            
        Returns:
            Dict[str, Any]: 测试结果，包含主测试结果和before/after任务结果
        """
        # 使用LoadGenerator执行测试，支持before/after任务
        results = self._load_generator.generate_concurrent_load(
            test_func=test_func,
            duration=self._test_config.duration,
            concurrent_users=self._test_config.concurrent_users,
            before_func=self._before_func,
            after_func=self._after_func,
            stop_on_error=self._test_config.stop_on_error
        )
        
        # 计算结果
        calculated_results = self._calculate_results(results.get('test_results', []))
        
        # 添加before/after任务结果
        if 'before_results' in results:
            calculated_results['before_task_results'] = results['before_results']
        if 'after_results' in results:
            calculated_results['after_task_results'] = results['after_results']
        
        return calculated_results
    
    def _run_tps_test(self, test_func: Callable):
        """
        运行TPS测试，支持ramup时间控制和before/after任务
        
        Args:
            test_func: 测试函数
            
        Returns:
            Dict[str, Any]: 测试结果，包含主测试结果和before/after任务结果
        """
        # 使用LoadGenerator执行TPS测试，支持before/after任务
        results = self._load_generator.generate_load(
            test_type='tps',
            test_func=test_func,
            duration=self._test_config.duration,
            target_tps=self._test_config.target_tps,
            ramp_up_time=self._test_config.ramp_up_time,
            ramp_up_steps=self._test_config.ramp_up_steps,
            before_func=self._before_func,
            after_func=self._after_func,
            stop_on_error=self._test_config.stop_on_error
        )
        
        # 计算结果
        calculated_results = self._calculate_results(results.get('test_results', []))
        
        # 添加before/after任务结果
        if 'before_results' in results:
            calculated_results['before_task_results'] = results['before_results']
        if 'after_results' in results:
            calculated_results['after_task_results'] = results['after_results']
        
        return calculated_results
    
    def _run_qps_test(self, test_func: Callable):
        """
        运行QPS测试，支持ramup时间控制和before/after任务
        
        Args:
            test_func: 测试函数
            
        Returns:
            Dict[str, Any]: 测试结果，包含主测试结果和before/after任务结果
        """
        # 使用LoadGenerator执行QPS测试，支持before/after任务
        results = self._load_generator.generate_load(
            test_type='qps',
            test_func=test_func,
            duration=self._test_config.duration,
            target_tps=self._test_config.target_qps,  # QPS测试使用target_qps
            ramp_up_time=self._test_config.ramp_up_time,
            ramp_up_steps=self._test_config.ramp_up_steps,
            before_func=self._before_func,
            after_func=self._after_func,
            stop_on_error=self._test_config.stop_on_error
        )
        
        # 计算结果
        calculated_results = self._calculate_results(results.get('test_results', []))
        
        # 添加before/after任务结果
        if 'before_results' in results:
            calculated_results['before_task_results'] = results['before_results']
        if 'after_results' in results:
            calculated_results['after_task_results'] = results['after_results']
        
        return calculated_results
    
    def _run_ramp_up_test(self, test_func: Callable):
        """
        运行爬坡测试，增强版支持更灵活的配置和before/after任务
        
        Args:
            test_func: 测试函数
            
        Returns:
            Dict[str, Any]: 测试结果，包含主测试结果、步骤指标和before/after任务结果
        """
        # 使用LoadGenerator执行爬坡测试，支持before/after任务
        results = self._load_generator.generate_load(
            test_type='ramp_up',
            test_func=test_func,
            duration=self._test_config.duration,
            concurrent_users=self._test_config.concurrent_users,
            ramp_up_time=self._test_config.ramp_up_time,
            ramp_up_steps=self._test_config.ramp_up_steps,
            before_func=self._before_func,
            after_func=self._after_func,
            stop_on_error=self._test_config.stop_on_error
        )
        
        # 计算结果
        calculated_results = self._calculate_results(results.get('test_results', []))
        
        # 添加步骤指标
        if 'step_metrics' in results:
            calculated_results['step_metrics'] = results['step_metrics']
        
        # 添加before/after任务结果
        if 'before_results' in results:
            calculated_results['before_task_results'] = results['before_results']
        if 'after_results' in results:
            calculated_results['after_task_results'] = results['after_results']
        
        return calculated_results
    
    def _run_stability_test(self, test_func: Callable):
        """
        运行长稳测试
        
        Args:
            test_func: 测试函数
            
        Returns:
            Dict[str, Any]: 测试结果，包含主测试结果和before/after任务结果
        """
        # 使用LoadGenerator执行长稳测试，支持before/after任务
        results = self._load_generator.generate_load(
            test_type='stability',
            test_func=test_func,
            duration=self._test_config.stability_duration,
            concurrent_users=self._test_config.concurrent_users,
            check_interval=self._test_config.stability_check_interval,
            before_func=self._before_func,
            after_func=self._after_func,
            stop_on_error=self._test_config.stop_on_error,
            stability_threshold=self._test_config.stability_threshold
        )
        
        # 计算结果
        calculated_results = self._calculate_results(results.get('test_results', []))
        
        # 添加检查间隔结果
        if 'interval_results' in results:
            calculated_results['interval_results'] = results['interval_results']
        
        # 添加before/after任务结果
        if 'before_results' in results:
            calculated_results['before_task_results'] = results['before_results']
        if 'after_results' in results:
            calculated_results['after_task_results'] = results['after_results']
        
        return calculated_results
        
    def _calculate_results(self, results: List[Dict[str, Any]]):
        """
        计算测试结果统计信息
        
        Args:
            results: 测试结果列表
            
        Returns:
            Dict[str, Any]: 统计结果
        """
        # 从指标收集器获取汇总指标
        summary_metrics = self._metrics_collector.get_summary_metrics()
        
        # 获取所有指标数据
        all_metrics = self._metrics_collector.get_all_metrics()
        
        # 基础结果统计（兼容原逻辑）
        if not results:
            base_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0
            }
        else:
            successful = [r for r in results if r['success']]
            base_stats = {
                'total_requests': len(results),
                'successful_requests': len(successful),
                'failed_requests': len(results) - len(successful),
                'success_rate': len(successful) / len(results) * 100
            }
        
        # 构建完整结果字典，结合基础统计和新指标
        combined_results = {
            # 基础指标
            **base_stats,
            'test_config': self._test_config.__dict__,
            
            # RPS相关指标
            'rps': summary_metrics.get('rps', 0),
            'successful_rps': summary_metrics.get('successful_rps', 0),
            'failed_rps': summary_metrics.get('failed_rps', 0),
            'max_rps': summary_metrics.get('max_rps', 0),
            'min_rps': summary_metrics.get('min_rps', 0),
            'avg_second_rps': summary_metrics.get('avg_second_rps', 0),
            'p95_rps': summary_metrics.get('p95_rps', 0),
            'max_success_rps': summary_metrics.get('max_success_rps', 0),
            'avg_success_rps': summary_metrics.get('avg_success_rps', 0),
            'max_failed_rps': summary_metrics.get('max_failed_rps', 0),
            'avg_failed_rps': summary_metrics.get('avg_failed_rps', 0),
            'throughput_variation': summary_metrics.get('throughput_variation', 0),
            
            # 响应时间指标
            'avg_response_time': summary_metrics.get('avg_response_time', 0),
            'min_response_time': summary_metrics.get('min_response_time', 0),
            'max_response_time': summary_metrics.get('max_response_time', 0),
            'p50_response_time': summary_metrics.get('p50_response_time', 0),
            'p90_response_time': summary_metrics.get('p90_response_time', 0),
            'p95_response_time': summary_metrics.get('p95_response_time', 0),
            'p99_response_time': summary_metrics.get('p99_response_time', 0),
            'p999_response_time': summary_metrics.get('p999_response_time', 0),
            'response_time_std_dev': summary_metrics.get('response_time_std_dev', 0),
            
            # 并发指标
            'max_concurrent_users': summary_metrics.get('max_concurrent_users', 0),
            
            # 其他指标
            'status_codes_distribution': summary_metrics.get('status_codes_distribution', {}),
            'errors_distribution': summary_metrics.get('errors_distribution', {}),
            'test_duration': summary_metrics.get('test_duration', 0),
            
            # 扩展指标
            'latency_stats': summary_metrics.get('latency_stats', {}),
            'connection_metrics': summary_metrics.get('connection_metrics', {}),
            
            # 事务指标
            'transaction_metrics': all_metrics.get('transaction_metrics', {})
        }
        
        # 添加特定测试类型的结果
        if self._test_config.test_type == 'concurrent':
            combined_results['concurrent_users'] = self._test_config.concurrent_users
        elif self._test_config.test_type == 'tps':
            combined_results['target_tps'] = self._test_config.target_tps
            combined_results['achieved_tps'] = summary_metrics.get('tps', summary_metrics.get('rps', 0))
        elif self._test_config.test_type == 'qps':
            combined_results['target_qps'] = self._test_config.target_qps
            combined_results['achieved_qps'] = summary_metrics.get('qps', summary_metrics.get('rps', 0))
        elif self._test_config.test_type == 'ramp_up':
            combined_results['ramp_up_steps'] = self._test_config.ramp_up_steps
            combined_results['step_duration'] = getattr(self._test_config, 'step_duration', 0)
            combined_results['start_users'] = getattr(self._test_config, 'start_users', 0)
            combined_results['target_users'] = getattr(self._test_config, 'target_users', self._test_config.concurrent_users)
        elif self._test_config.test_type == 'stability':
            combined_results['target_duration'] = self._test_config.stability_duration
            combined_results['check_interval'] = self._test_config.stability_check_interval
            combined_results['stability_threshold'] = self._test_config.stability_threshold
        
        # 添加时间序列数据和其他高级指标
        combined_results['time_series_data'] = all_metrics.get('time_series', [])
        combined_results['response_time_distribution'] = all_metrics.get('response_time_distribution', {})
        combined_results['requests_summary'] = all_metrics.get('requests_info', {})
        
        return combined_results
    
    def get_report(self, format_type: str = 'json'):
        """
        获取测试报告
        
        Args:
            format_type: 报告格式，可选值: json, text, html
            
        Returns:
            Any: 报告内容
        """
        if not self._report_generator:
            raise ValueError("请先执行测试")
        
        return self._report_generator.generate(format_type)
    
    def save_report(self, file_path: str, format_type: str = 'json'):
        """
        保存测试报告到文件
        
        Args:
            file_path: 文件路径
            format_type: 报告格式，可选值: json, text, html
            
        Returns:
            str: 保存的文件路径
        """
        if not self._report_generator:
            raise ValueError("请先执行测试")
        
        return self._report_generator.save(file_path, format_type)
    
    def is_running(self):
        """
        检查测试是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return self._running