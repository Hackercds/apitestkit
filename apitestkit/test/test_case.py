"""
测试用例类定义

提供测试用例的基本结构和生命周期管理
"""

import time
import uuid
import json
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from apitestkit.core.logger import create_user_logger
from apitestkit.adapter.api_adapter import api


@dataclass
class TestResult:
    """
    测试结果数据类
    """
    test_id: str
    test_name: str
    status: str = 'pending'
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    steps: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestCase:
    """
    测试用例基类
    
    提供测试用例的基本结构和生命周期管理，支持before/after钩子函数
    以及测试变量管理和断言
    """
    
    def __init__(self, test_name: str = None):
        self.test_name = test_name or self.__class__.__name__
        self.test_id = str(uuid.uuid4())
        self.variables = {}
        self.result = TestResult(test_id=self.test_id, test_name=self.test_name)
        self.logger = create_user_logger(self.test_name)
        
        # 钩子函数字典
        self._hooks = {
            'before_test': [],
            'after_test': [],
            'before_step': [],
            'after_step': []
        }
    
    def setup(self):
        """
        测试用例设置方法
        
        子类可以重写此方法来进行测试前的准备工作
        """
        pass
    
    def teardown(self):
        """
        测试用例清理方法
        
        子类可以重写此方法来进行测试后的清理工作
        """
        pass
    
    def before_test(self):
        """
        测试前钩子
        
        子类可以重写此方法来执行测试前的操作
        """
        pass
    
    def after_test(self):
        """
        测试后钩子
        
        子类可以重写此方法来执行测试后的操作
        """
        pass
    
    def before_step(self, step_name: str):
        """
        步骤前钩子
        
        子类可以重写此方法来执行步骤前的操作
        
        Args:
            step_name: 步骤名称
        """
        pass
    
    def after_step(self, step_name: str, step_result: Dict[str, Any]):
        """
        步骤后钩子
        
        子类可以重写此方法来执行步骤后的操作
        
        Args:
            step_name: 步骤名称
            step_result: 步骤执行结果
        """
        pass
    
    def run(self):
        """
        运行测试用例的完整流程
        
        包括设置、钩子函数执行、测试逻辑执行和清理等完整生命周期
        
        Returns:
            TestResult: 测试结果
        """
        self.result.start_time = time.time()
        self.logger.info(f"[测试开始] {self.test_name} (ID: {self.test_id})")
        
        try:
            # 执行setup方法
            self.setup()
            
            # 执行before_test钩子
            self.before_test()
            for hook in self._hooks['before_test']:
                hook()
            
            # 执行测试方法
            self.execute()
            
            # 设置默认成功状态
            if not self.result.errors and not self.result.failures:
                self.result.status = 'passed'
                self.logger.info(f"[测试通过] {self.test_name}")
            else:
                self.result.status = 'failed'
                self.logger.error(f"[测试失败] {self.test_name}")
        
        except Exception as e:
            error_msg = f"测试执行过程中发生异常: {str(e)}"
            self.result.errors.append(error_msg)
            self.result.status = 'error'
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            try:
                # 执行after_test钩子
                self.after_test()
                for hook in self._hooks['after_test']:
                    hook()
                
                # 执行teardown方法
                self.teardown()
            except Exception as e:
                error_msg = f"清理过程中发生异常: {str(e)}"
                self.result.errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True)
            
            # 计算测试耗时
            self.result.end_time = time.time()
            self.result.duration = self.result.end_time - self.result.start_time
            self.result.variables = self.variables
            
            self.logger.info(f"[测试结束] {self.test_name} - 耗时: {self.result.duration:.3f}s - 状态: {self.result.status}")
        
        return self.result
    
    def execute(self):
        """
        测试用例的核心测试逻辑
        
        子类必须重写此方法来实现具体的测试步骤和断言
        这是测试用例的核心方法，包含实际的测试步骤定义
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def step(self, name: str, func: Callable[[], Any]):
        """
        执行测试步骤
        
        Args:
            name: 步骤名称
            func: 步骤执行函数
            
        Returns:
            Any: 步骤执行结果
        """
        step_result = {
            'name': name,
            'status': 'success',
            'start_time': time.time(),
            'result': None,
            'error': None
        }
        
        self.logger.info(f"[步骤开始] {name}")
        
        # 执行步骤前钩子
        self.before_step(name)
        for hook in self._hooks['before_step']:
            hook(name)
        
        try:
            # 执行步骤函数
            result = func()
            step_result['result'] = result
            
            self.logger.info(f"[步骤成功] {name}")
        except Exception as e:
            step_result['status'] = 'failed'
            step_result['error'] = str(e)
            self.result.failures.append(f"步骤 '{name}' 失败: {str(e)}")
            self.logger.error(f"[步骤失败] {name}: {str(e)}", exc_info=True)
        
        # 计算步骤耗时
        step_result['end_time'] = time.time()
        step_result['duration'] = step_result['end_time'] - step_result['start_time']
        
        # 执行步骤后钩子
        self.after_step(name, step_result)
        for hook in self._hooks['after_step']:
            hook(name, step_result)
        
        # 添加到测试结果中
        self.result.steps.append(step_result)
        
        return step_result.get('result')
    
    def api(self, url: str = None):
        """
        创建API适配器实例
        
        Args:
            url: API URL
            
        Returns:
            ApiAdapter: API适配器实例
        """
        adapter = api(url)
        adapter.user_log = self.logger
        return adapter
    
    def set_var(self, name: str, value: Any):
        """
        设置测试变量
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.variables[name] = value
        self.logger.debug(f"设置变量: {name} = {value}")
    
    def get_var(self, name: str, default: Any = None) -> Any:
        """
        获取测试变量
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            Any: 变量值或默认值
        """
        value = self.variables.get(name, default)
        self.logger.debug(f"获取变量: {name} = {value}")
        return value
    
    def assert_equal(self, actual: Any, expected: Any, message: str = None):
        """
        断言相等
        
        Args:
            actual: 实际值
            expected: 期望值
            message: 错误消息
        """
        if actual != expected:
            error_msg = message or f"断言失败: 预期 {expected}, 实际 {actual}"
            self.result.failures.append(error_msg)
            self.logger.error(error_msg)
            raise AssertionError(error_msg)
        else:
            self.logger.info(f"断言成功: {actual} == {expected}")
    
    def assert_true(self, condition: bool, message: str = None):
        """
        断言为真
        
        Args:
            condition: 条件
            message: 错误消息
        """
        if not condition:
            error_msg = message or f"断言失败: 预期为True, 实际为False"
            self.result.failures.append(error_msg)
            self.logger.error(error_msg)
            raise AssertionError(error_msg)
        else:
            self.logger.info(f"断言成功: {condition} 为真")
    
    def assert_false(self, condition: bool, message: str = None):
        """
        断言为假
        
        Args:
            condition: 条件
            message: 错误消息
        """
        if condition:
            error_msg = message or f"断言失败: 预期为False, 实际为True"
            self.result.failures.append(error_msg)
            self.logger.error(error_msg)
            raise AssertionError(error_msg)
        else:
            self.logger.info(f"断言成功: {condition} 为假")
    
    def assert_contains(self, container: Any, item: Any, message: str = None):
        """
        断言包含
        
        Args:
            container: 容器
            item: 项目
            message: 错误消息
        """
        if item not in container:
            error_msg = message or f"断言失败: {container} 不包含 {item}"
            self.result.failures.append(error_msg)
            self.logger.error(error_msg)
            raise AssertionError(error_msg)
        else:
            self.logger.info(f"断言成功: {container} 包含 {item}")
    
    def add_hook(self, hook_name: str, callback: Callable):
        """
        添加钩子函数
        
        Args:
            hook_name: 钩子名称 (before_test, after_test, before_step, after_step)
            callback: 回调函数
        """
        if hook_name in self._hooks:
            self._hooks[hook_name].append(callback)
            self.logger.debug(f"添加钩子: {hook_name}")
        else:
            self.logger.warning(f"未知的钩子名称: {hook_name}")
    
    def log(self, level: str, message: str):
        """
        记录用户日志
        
        Args:
            level: 日志级别 (debug, info, warning, error, critical)
            message: 日志消息
        """
        if hasattr(self.logger, level):
            getattr(self.logger, level)(message)
        else:
            self.logger.info(message)
    
    def export_result(self) -> Dict[str, Any]:
        """
        导出测试结果
        
        Returns:
            Dict[str, Any]: 测试结果字典
        """
        return {
            'test_id': self.result.test_id,
            'test_name': self.result.test_name,
            'status': self.result.status,
            'start_time': self.result.start_time,
            'end_time': self.result.end_time,
            'duration': self.result.duration,
            'steps': self.result.steps,
            'errors': self.result.errors,
            'failures': self.result.failures,
            'variables': self.result.variables,
            'metadata': self.result.metadata
        }
    
    def save_result(self, file_path: str = None):
        """
        保存测试结果到文件
        
        Args:
            file_path: 文件路径，默认使用测试名称
        """
        if not file_path:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            file_path = f"test_result_{self.test_name}_{timestamp}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.export_result(), f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试结果已保存到: {file_path}")