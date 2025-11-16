"""
测试运行器类定义

提供高级测试运行功能，支持并行执行、报告生成等
"""

import time
import uuid
import json
import os
import concurrent.futures
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from apitestkit.core.logger import create_user_logger
from apitestkit.test.test_suite import TestSuite, TestSuiteResult


@dataclass
class RunnerResult:
    """
    运行器结果数据类
    """
    runner_id: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_suites: int = 0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    suite_results: List[TestSuiteResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestRunner:
    """
    测试运行器类
    
    提供高级测试运行功能，支持添加多个测试套件，
    并行执行测试，生成综合报告等
    """
    
    def __init__(self, name: str = "TestRunner"):
        self.name = name
        self.runner_id = str(uuid.uuid4())
        self.suites: List[TestSuite] = []
        self.result = RunnerResult(runner_id=self.runner_id)
        self.logger = create_user_logger(f"runner_{name}")
        self.report_dir = str(Path('reports') / f"run_{time.strftime('%Y%m%d_%H%M%S')}")
        
        # 配置项
        self.config = {
            'max_workers': 4,  # 并行执行的最大工作线程数
            'fail_fast': False,  # 是否在第一个失败后停止
            'generate_html_report': True,  # 是否生成HTML报告
            'save_json_results': True,  # 是否保存JSON结果
            'report_dir': self.report_dir  # 报告保存目录
        }
    
    def configure(self, **kwargs):
        """
        配置运行器
        
        Args:
            **kwargs: 配置参数
        """
        self.config.update(kwargs)
        self.logger.info(f"更新运行器配置: {kwargs}")
        
        # 更新报告目录
        self.report_dir = self.config['report_dir']
    
    def add_suite(self, suite: TestSuite):
        """
        添加测试套件
        
        Args:
            suite: 测试套件对象
        """
        if isinstance(suite, TestSuite):
            self.suites.append(suite)
            self.logger.info(f"添加测试套件: {suite.suite_name}")
        else:
            self.logger.error(f"无效的测试套件类型: {type(suite)}")
    
    def add_suites(self, suites: List[TestSuite]):
        """
        批量添加测试套件
        
        Args:
            suites: 测试套件列表
        """
        for suite in suites:
            self.add_suite(suite)
    
    def remove_suite(self, suite_name: str):
        """
        根据名称移除测试套件
        
        Args:
            suite_name: 测试套件名称
        """
        for i, suite in enumerate(self.suites):
            if suite.suite_name == suite_name:
                del self.suites[i]
                self.logger.info(f"移除测试套件: {suite_name}")
                return
        self.logger.warning(f"未找到测试套件: {suite_name}")
    
    def clear_suites(self):
        """
        清空所有测试套件
        """
        self.suites.clear()
        self.logger.info("清空所有测试套件")
    
    def before_run(self):
        """
        运行前钩子
        
        子类可以重写此方法来执行运行前的操作
        """
        # 确保报告目录存在
        if self.config['generate_html_report'] or self.config['save_json_results']:
            Path(self.report_dir).mkdir(exist_ok=True, parents=True)
            self.logger.info(f"创建报告目录: {self.report_dir}")
    
    def after_run(self):
        """
        运行后钩子
        
        子类可以重写此方法来执行运行后的操作
        """
        # 生成报告
        if self.config['generate_html_report']:
            self.generate_html_report()
        
        if self.config['save_json_results']:
            self.save_json_results()
    
    def run(self, parallel: bool = False) -> RunnerResult:
        """
        执行所有测试套件
        
        Args:
            parallel: 是否并行执行测试套件
            
        Returns:
            RunnerResult: 运行器结果
        """
        self.result.start_time = time.time()
        self.logger.info(f"[运行器开始] {self.name} (ID: {self.runner_id})")
        self.logger.info(f"总共包含 {len(self.suites)} 个测试套件")
        
        try:
            # 执行before_run钩子
            self.before_run()
            
            self.result.total_suites = len(self.suites)
            
            if parallel:
                # 并行执行测试套件
                self._run_parallel()
            else:
                # 串行执行测试套件
                self._run_sequential()
            
        except Exception as e:
            error_msg = f"测试运行器执行过程中发生异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            try:
                # 执行after_run钩子
                self.after_run()
            except Exception as e:
                self.logger.error(f"运行器清理过程中发生异常: {str(e)}", exc_info=True)
            
            # 计算总耗时
            self.result.end_time = time.time()
            self.result.duration = self.result.end_time - self.result.start_time
            
            # 记录运行结果统计
            self.logger.info(f"[运行器结束] {self.name}")
            self.logger.info(f"执行统计: 总套件 {self.result.total_suites}, 总测试 {self.result.total_tests}")
            self.logger.info(f"通过 {self.result.passed}, 失败 {self.result.failed}, 错误 {self.result.errors}")
            self.logger.info(f"总耗时: {self.result.duration:.3f}s")
        
        return self.result
    
    def _run_sequential(self):
        """
        串行执行测试套件
        """
        self.logger.info("开始串行执行测试套件")
        
        for suite in self.suites:
            suite_result = suite.run()
            self.result.suite_results.append(suite_result)
            
            # 更新统计信息
            self.result.total_tests += suite_result.total_tests
            self.result.passed += suite_result.passed
            self.result.failed += suite_result.failed
            self.result.errors += suite_result.errors
            
            # 如果设置了fail_fast并且有失败，停止执行
            if self.config['fail_fast'] and (suite_result.failed > 0 or suite_result.errors > 0):
                self.logger.warning("检测到测试失败，根据fail_fast配置停止执行")
                break
    
    def _run_parallel(self):
        """
        并行执行测试套件
        """
        self.logger.info(f"开始并行执行测试套件，最大工作线程数: {self.config['max_workers']}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            # 提交所有测试套件执行任务
            future_to_suite = {executor.submit(suite.run): suite for suite in self.suites}
            
            # 获取执行结果
            for future in concurrent.futures.as_completed(future_to_suite):
                suite = future_to_suite[future]
                try:
                    suite_result = future.result()
                    self.result.suite_results.append(suite_result)
                    
                    # 更新统计信息
                    self.result.total_tests += suite_result.total_tests
                    self.result.passed += suite_result.passed
                    self.result.failed += suite_result.failed
                    self.result.errors += suite_result.errors
                    
                except Exception as e:
                    error_msg = f"测试套件 '{suite.suite_name}' 执行失败: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
    
    def generate_html_report(self):
        """
        生成HTML格式的测试报告
        """
        html_report_path = str(Path(self.report_dir) / 'index.html')
        
        # 生成HTML内容
        html_content = self._generate_html_content()
        
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML报告已生成: {html_report_path}")
    
    def _generate_html_content(self) -> str:
        """
        生成HTML报告内容
        
        Returns:
            str: HTML内容
        """
        # 构建基本的HTML模板
        html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API测试报告 - {self.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
                line-height: 1.6; color: #333; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .summary {{ background-color: white; padding: 20px; margin-bottom: 20px; border-radius: 0 0 8px 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .suite {{ background-color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; 
                  box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .suite-header {{ display: flex; justify-content: space-between; align-items: center; 
                         border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
        .suite-name {{ font-size: 18px; font-weight: bold; }}
        .test {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
        .test:last-child {{ border-bottom: none; }}
        .test-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .test-name {{ font-weight: 500; }}
        .test-status {{ font-size: 14px; padding: 2px 8px; border-radius: 12px; }}
        .status-passed {{ background-color: #d4edda; color: #155724; }}
        .status-failed {{ background-color: #f8d7da; color: #721c24; }}
        .status-error {{ background-color: #f8d7da; color: #721c24; }}
        .metrics {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        .timestamp {{ font-size: 14px; color: #999; }}
        .details {{ margin-top: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 4px; 
                   font-family: 'Courier New', monospace; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>API测试报告</h1>
            <p>{self.name} - 执行时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.result.start_time))}</p>
        </div>
        
        <div class="summary">
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{self.result.total_tests}</div>
                    <div class="metric-label">总测试数</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #28a745;">{self.result.passed}</div>
                    <div class="metric-label">通过</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #dc3545;">{self.result.failed}</div>
                    <div class="metric-label">失败</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #dc3545;">{self.result.errors}</div>
                    <div class="metric-label">错误</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.result.duration:.3f}s</div>
                    <div class="metric-label">总耗时</div>
                </div>
            </div>
            <p class="timestamp">生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
'''
        
        # 添加每个套件的详细信息
        for suite_result in self.result.suite_results:
            html += f'''
        <div class="suite">
            <div class="suite-header">
                <span class="suite-name">{suite_result.suite_name}</span>
                <span>测试: {suite_result.total_tests}, 通过: {suite_result.passed}, 失败: {suite_result.failed}, 耗时: {suite_result.duration:.3f}s</span>
            </div>
'''
            
            # 添加每个测试用例的信息
            for test_result in suite_result.test_results:
                status_class = f"status-{test_result.status}"
                html += f'''
            <div class="test">
                <div class="test-header">
                    <span class="test-name">{test_result.test_name}</span>
                    <span class="test-status {status_class}">{test_result.status} ({test_result.duration:.3f}s)</span>
                </div>
'''
                
                # 添加失败信息
                if test_result.failures:
                    html += '                <div class="details">\n'
                    for failure in test_result.failures[:3]:
                        html += f'                    <p>❌ 失败: {failure}</p>\n'
                    if len(test_result.failures) > 3:
                        html += f'                    <p>... 还有 {len(test_result.failures) - 3} 个失败</p>\n'
                    html += '                </div>\n'
                
                html += '''            </div>\n'''
        
        html += '''
    </div>
</body>
</html>
'''
        
        return html
    
    def save_json_results(self):
        """
        保存JSON格式的测试结果
        """
        json_path = str(Path(self.report_dir) / 'results.json')
        
        # 转换为可序列化的格式
        result_dict = self.export_result()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"JSON结果已保存: {json_path}")
    
    def export_result(self) -> Dict[str, Any]:
        """
        导出运行器结果
        
        Returns:
            Dict[str, Any]: 运行器结果字典
        """
        return {
            'runner_id': self.result.runner_id,
            'name': self.name,
            'start_time': self.result.start_time,
            'end_time': self.result.end_time,
            'duration': self.result.duration,
            'total_suites': self.result.total_suites,
            'total_tests': self.result.total_tests,
            'passed': self.result.passed,
            'failed': self.result.failed,
            'errors': self.result.errors,
            'suite_results': [sr.__dict__ for sr in self.result.suite_results],
            'metadata': self.result.metadata,
            'config': self.config
        }
    
    def generate_summary(self) -> str:
        """
        生成测试运行摘要
        
        Returns:
            str: 摘要文本
        """
        summary = []
        summary.append("=" * 80)
        summary.append(f"API测试运行摘要: {self.name}")
        summary.append(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.result.start_time))}")
        summary.append("=" * 80)
        summary.append(f"总套件数: {self.result.total_suites}")
        summary.append(f"总测试数: {self.result.total_tests}")
        summary.append(f"通过: {self.result.passed}")
        summary.append(f"失败: {self.result.failed}")
        summary.append(f"错误: {self.result.errors}")
        summary.append(f"总耗时: {self.result.duration:.3f}s")
        
        if self.result.suite_results:
            summary.append("-" * 80)
            summary.append("套件详情:")
            
            for suite_result in self.result.suite_results:
                summary.append(f"  - {suite_result.suite_name}: 测试 {suite_result.total_tests}, 通过 {suite_result.passed}, 失败 {suite_result.failed}, 耗时 {suite_result.duration:.3f}s")
        
        summary.append("=" * 80)
        
        summary_str = "\n".join(summary)
        self.logger.info("\n" + summary_str)
        return summary_str