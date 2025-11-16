"""
测试套件类定义

提供测试套件管理功能，支持批量执行测试用例
"""

import time
import uuid
import json
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from apitestkit.core.logger import create_user_logger
from apitestkit.test.test_case import TestCase, TestResult


@dataclass
class TestSuiteResult:
    """
    测试套件结果数据类
    """
    suite_id: str
    suite_name: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    test_results: List[TestResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestSuite:
    """
    测试套件类
    
    提供测试套件的管理功能，支持添加、移除、执行测试用例，
    以及套件级别的钩子函数
    """
    
    def __init__(self, suite_name: str = "TestSuite"):
        self.suite_name = suite_name
        self.suite_id = str(uuid.uuid4())
        self.test_cases: List[TestCase] = []
        self.suite_variables: Dict[str, Any] = {}
        self.result = TestSuiteResult(suite_id=self.suite_id, suite_name=self.suite_name)
        self.logger = create_user_logger(f"suite_{suite_name}")
        
        # 钩子函数字典
        self._hooks = {
            'before_suite': [],
            'after_suite': [],
            'before_test': [],
            'after_test': []
        }
    
    def add_test(self, test_case: TestCase):
        """
        添加测试用例到套件
        
        Args:
            test_case: 测试用例对象
        """
        if isinstance(test_case, TestCase):
            # 共享套件变量
            test_case.variables.update(self.suite_variables)
            self.test_cases.append(test_case)
            self.logger.info(f"添加测试用例: {test_case.test_name}")
        else:
            self.logger.error(f"无效的测试用例类型: {type(test_case)}")
    
    def add_tests(self, test_cases: List[TestCase]):
        """
        批量添加测试用例
        
        Args:
            test_cases: 测试用例列表
        """
        for test_case in test_cases:
            self.add_test(test_case)
    
    def remove_test(self, test_name: str):
        """
        根据名称移除测试用例
        
        Args:
            test_name: 测试用例名称
        """
        for i, test_case in enumerate(self.test_cases):
            if test_case.test_name == test_name:
                del self.test_cases[i]
                self.logger.info(f"移除测试用例: {test_name}")
                return
        self.logger.warning(f"未找到测试用例: {test_name}")
    
    def clear_tests(self):
        """
        清空所有测试用例
        """
        self.test_cases.clear()
        self.logger.info("清空所有测试用例")
    
    def set_variable(self, name: str, value: Any):
        """
        设置套件变量
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.suite_variables[name] = value
        self.logger.debug(f"设置套件变量: {name} = {value}")
        
        # 更新所有测试用例的变量
        for test_case in self.test_cases:
            test_case.set_var(name, value)
    
    def set_variables(self, variables: Dict[str, Any]):
        """
        批量设置套件变量
        
        Args:
            variables: 变量字典
        """
        self.suite_variables.update(variables)
        
        # 更新所有测试用例的变量
        for test_case in self.test_cases:
            test_case.variables.update(variables)
    
    def before_suite(self):
        """
        套件执行前钩子
        
        子类可以重写此方法来执行套件前的操作
        """
        pass
    
    def after_suite(self):
        """
        套件执行后钩子
        
        子类可以重写此方法来执行套件后的操作
        """
        pass
    
    def before_test(self, test_case: TestCase):
        """
        测试用例执行前钩子
        
        子类可以重写此方法来执行测试用例前的操作
        
        Args:
            test_case: 测试用例对象
        """
        pass
    
    def after_test(self, test_case: TestCase, test_result: TestResult):
        """
        测试用例执行后钩子
        
        子类可以重写此方法来执行测试用例后的操作
        
        Args:
            test_case: 测试用例对象
            test_result: 测试结果
        """
        pass
    
    def run(self, test_names: List[str] = None) -> TestSuiteResult:
        """
        执行测试套件
        
        Args:
            test_names: 要执行的测试用例名称列表，None表示执行所有
            
        Returns:
            TestSuiteResult: 测试套件结果
        """
        self.result.start_time = time.time()
        self.logger.info(f"[套件开始] {self.suite_name} (ID: {self.suite_id})")
        self.logger.info(f"总共包含 {len(self.test_cases)} 个测试用例")
        
        try:
            # 执行before_suite钩子
            self.before_suite()
            for hook in self._hooks['before_suite']:
                hook()
            
            # 确定要执行的测试用例
            if test_names:
                tests_to_run = [tc for tc in self.test_cases if tc.test_name in test_names]
                self.logger.info(f"将执行 {len(tests_to_run)} 个指定的测试用例")
            else:
                tests_to_run = self.test_cases
                self.logger.info(f"将执行所有 {len(tests_to_run)} 个测试用例")
            
            self.result.total_tests = len(tests_to_run)
            
            # 执行测试用例
            for test_case in tests_to_run:
                self.logger.info(f"[测试准备] {test_case.test_name}")
                
                # 执行before_test钩子
                self.before_test(test_case)
                for hook in self._hooks['before_test']:
                    hook(test_case)
                
                # 执行测试用例
                test_result = test_case.run()
                self.result.test_results.append(test_result)
                
                # 更新统计信息
                if test_result.status == 'passed':
                    self.result.passed += 1
                elif test_result.status == 'failed':
                    self.result.failed += 1
                elif test_result.status == 'error':
                    self.result.errors += 1
                
                # 执行after_test钩子
                self.after_test(test_case, test_result)
                for hook in self._hooks['after_test']:
                    hook(test_case, test_result)
                
                # 将测试用例的变量更新到套件变量中
                self.suite_variables.update(test_case.variables)
            
        except Exception as e:
            error_msg = f"测试套件执行过程中发生异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            try:
                # 执行after_suite钩子
                self.after_suite()
                for hook in self._hooks['after_suite']:
                    hook()
            except Exception as e:
                self.logger.error(f"套件清理过程中发生异常: {str(e)}", exc_info=True)
            
            # 计算总耗时
            self.result.end_time = time.time()
            self.result.duration = self.result.end_time - self.result.start_time
            
            # 记录测试结果统计
            self.logger.info(f"[套件结束] {self.suite_name}")
            self.logger.info(f"执行统计: 总测试 {self.result.total_tests}, 通过 {self.result.passed}, 失败 {self.result.failed}, 错误 {self.result.errors}")
            self.logger.info(f"总耗时: {self.result.duration:.3f}s")
        
        return self.result
    
    def add_hook(self, hook_name: str, callback: Callable):
        """
        添加钩子函数
        
        Args:
            hook_name: 钩子名称 (before_suite, after_suite, before_test, after_test)
            callback: 回调函数
        """
        if hook_name in self._hooks:
            self._hooks[hook_name].append(callback)
            self.logger.debug(f"添加套件钩子: {hook_name}")
        else:
            self.logger.warning(f"未知的套件钩子名称: {hook_name}")
    
    def filter_tests(self, condition: Callable[[TestCase], bool]) -> List[TestCase]:
        """
        根据条件过滤测试用例
        
        Args:
            condition: 过滤条件函数
            
        Returns:
            List[TestCase]: 过滤后的测试用例列表
        """
        filtered = [tc for tc in self.test_cases if condition(tc)]
        self.logger.info(f"过滤后剩余 {len(filtered)} 个测试用例")
        return filtered
    
    def get_test_by_name(self, test_name: str) -> Optional[TestCase]:
        """
        根据名称获取测试用例
        
        Args:
            test_name: 测试用例名称
            
        Returns:
            Optional[TestCase]: 测试用例对象或None
        """
        for test_case in self.test_cases:
            if test_case.test_name == test_name:
                return test_case
        return None
    
    def export_result(self) -> Dict[str, Any]:
        """
        导出测试套件结果
        
        Returns:
            Dict[str, Any]: 测试套件结果字典
        """
        return {
            'suite_id': self.result.suite_id,
            'suite_name': self.result.suite_name,
            'start_time': self.result.start_time,
            'end_time': self.result.end_time,
            'duration': self.result.duration,
            'total_tests': self.result.total_tests,
            'passed': self.result.passed,
            'failed': self.result.failed,
            'errors': self.result.errors,
            'test_results': [tr.__dict__ for tr in self.result.test_results],
            'metadata': self.result.metadata
        }
    
    def save_result(self, file_path: str = None):
        """
        保存测试套件结果到文件
        
        Args:
            file_path: 文件路径，默认使用套件名称
        """
        if not file_path:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            file_path = f"test_suite_result_{self.suite_name}_{timestamp}.json"
        
        # 转换为可序列化的格式
        result_dict = self.export_result()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试套件结果已保存到: {file_path}")
    
    def generate_report(self) -> str:
        """
        生成简单的测试报告
        
        Returns:
            str: 测试报告文本
        """
        report = []
        report.append("=" * 60)
        report.append(f"测试套件报告: {self.suite_name}")
        report.append(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.result.start_time))}")
        report.append("=" * 60)
        report.append(f"总测试数: {self.result.total_tests}")
        report.append(f"通过: {self.result.passed}")
        report.append(f"失败: {self.result.failed}")
        report.append(f"错误: {self.result.errors}")
        report.append(f"总耗时: {self.result.duration:.3f}s")
        report.append("-" * 60)
        
        # 详细的测试结果
        for test_result in self.result.test_results:
            status_color = "✓" if test_result.status == "passed" else "✗"
            report.append(f"{status_color} {test_result.test_name} - {test_result.status} ({test_result.duration:.3f}s)")
            
            # 显示失败信息
            if test_result.failures:
                for failure in test_result.failures[:3]:  # 只显示前3个失败
                    report.append(f"  - 失败: {failure}")
                if len(test_result.failures) > 3:
                    report.append(f"  - ... 还有 {len(test_result.failures) - 3} 个失败")
            
            # 显示错误信息
            if test_result.errors:
                for error in test_result.errors[:3]:  # 只显示前3个错误
                    report.append(f"  - 错误: {error}")
                if len(test_result.errors) > 3:
                    report.append(f"  - ... 还有 {len(test_result.errors) - 3} 个错误")
        
        report.append("=" * 60)
        
        report_str = "\n".join(report)
        self.logger.info("\n" + report_str)
        return report_str