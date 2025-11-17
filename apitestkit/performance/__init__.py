"""
性能测试模块

提供API性能测试功能，支持TPS、QPS测试、并发测试、爬坡测试等。
"""

from apitestkit.performance.performance_runner import PerformanceRunner
from apitestkit.performance.load_generator import LoadGenerator
from apitestkit.performance.metrics_collector import MetricsCollector
from apitestkit.performance.report_generator import PerformanceReportGenerator

__all__ = [
    'PerformanceRunner',
    'LoadGenerator', 
    'MetricsCollector',
    'PerformanceReportGenerator',
    'performance'
]

def performance():
    """
    创建性能测试运行器实例
    
    Returns:
        PerformanceRunner: 性能测试运行器实例
    """
    return PerformanceRunner()