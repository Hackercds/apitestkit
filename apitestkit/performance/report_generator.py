"""
报告生成器模块

负责生成和保存性能测试的各种格式报告，包括JSON、文本和HTML格式。
"""

import os
import json
import time
from typing import Dict, Any, Optional

from apitestkit.core.logger import logger_manager

class PerformanceReportGenerator:
    """
    性能测试报告生成器
    
    生成和保存性能测试报告，支持多种格式。
    """
    
    def __init__(self, test_results: Dict[str, Any], metrics: Dict[str, Any], test_config: Any):
        """
        初始化报告生成器
        
        Args:
            test_results: 测试结果数据
            metrics: 收集的指标数据
            test_config: 测试配置
        """
        self._test_results = test_results
        self._metrics = metrics
        self._test_config = test_config
        self._report_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    def generate(self, format_type: str = 'json') -> Any:
        """
        生成报告
        
        Args:
            format_type: 报告格式，可选值: json, text, html
            
        Returns:
            Any: 报告内容
        """
        if format_type == 'json':
            return self._generate_json_report()
        elif format_type == 'text':
            return self._generate_text_report()
        elif format_type == 'html':
            return self._generate_html_report()
        else:
            raise ValueError(f"不支持的报告格式: {format_type}")
    
    def save(self, file_path: str, format_type: str = 'json') -> str:
        """
        保存报告到文件
        
        Args:
            file_path: 文件路径
            format_type: 报告格式
            
        Returns:
            str: 保存的文件路径
        """
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # 生成报告内容
        content = self.generate(format_type)
        
        # 根据格式调整文件扩展名
        ext = format_type
        if not file_path.endswith(f'.{ext}'):
            file_path = f"{file_path}.{ext}"
        
        # 保存文件
        try:
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger_manager.info(f"[报告生成器] 报告已保存到: {file_path}")
            return file_path
            
        except Exception as e:
            logger_manager.error(f"[报告生成器] 保存报告失败: {str(e)}")
            raise
    
    def _generate_json_report(self) -> Dict[str, Any]:
        """
        生成JSON格式报告
        
        Returns:
            Dict[str, Any]: JSON格式的报告
        """
        report = {
            'report_info': {
                'generated_at': self._report_time,
                'test_type': self._test_config.test_type,
                'test_duration': self._metrics.get('test_duration', 0),
                'concurrent_users': self._test_config.concurrent_users,
                'environment': self._get_environment_info()
            },
            'test_config': {
                'test_type': self._test_config.test_type,
                'duration': self._test_config.duration,
                'concurrent_users': self._test_config.concurrent_users,
                'ramp_up_time': self._test_config.ramp_up_time,
                'ramp_up_steps': self._test_config.ramp_up_steps,
                'target_tps': self._test_config.target_tps,
                'target_qps': self._test_config.target_qps,
                'timeout': self._test_config.timeout,
                'think_time': self._test_config.think_time,
                'stop_on_error': self._test_config.stop_on_error,
                'connection_timeout': getattr(self._test_config, 'connection_timeout', None),
                'max_retries': getattr(self._test_config, 'max_retries', None)
            },
            'metrics': self._metrics,
            'test_results': self._test_results,
            'analysis': self._generate_performance_analysis()
        }
        
        return report
    
    def _get_environment_info(self) -> Dict[str, str]:
        """
        获取环境信息
        
        Returns:
            Dict[str, str]: 环境信息
        """
        import platform
        import sys
        
        return {
            'os': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    
    def _generate_performance_analysis(self) -> Dict[str, Any]:
        """
        生成性能分析结果
        
        Returns:
            Dict[str, Any]: 性能分析结果
        """
        summary = self._metrics.get('summary', {})
        
        # 分析成功率
        success_rate = summary.get('success_rate', 0)
        success_status = '优秀' if success_rate >= 99.9 else '良好' if success_rate >= 99 else '一般' if success_rate >= 95 else '较差'
        
        # 分析响应时间
        avg_rt = summary.get('avg_response_time', 0)
        rt_status = '优秀' if avg_rt < 100 else '良好' if avg_rt < 300 else '一般' if avg_rt < 1000 else '较差'
        
        # 分析RPS
        rps = summary.get('rps', 0)
        target_rps = getattr(self._test_config, 'target_tps', getattr(self._test_config, 'target_qps', 0))
        rps_status = '未达到目标' if target_rps > 0 and rps < target_rps else '达到目标'
        
        return {
            'success_analysis': {
                'status': success_status,
                'rate': success_rate,
                'suggestion': self._get_success_suggestion(success_rate)
            },
            'response_time_analysis': {
                'status': rt_status,
                'avg_response_time': avg_rt,
                'suggestion': self._get_response_time_suggestion(avg_rt)
            },
            'throughput_analysis': {
                'status': rps_status,
                'actual_rps': rps,
                'target_rps': target_rps,
                'suggestion': self._get_throughput_suggestion(rps, target_rps)
            }
        }
    
    def _get_success_suggestion(self, success_rate: float) -> str:
        """
        根据成功率获取建议
        
        Args:
            success_rate: 成功率
            
        Returns:
            str: 建议
        """
        if success_rate >= 99.9:
            return "服务稳定性优秀，继续保持。"
        elif success_rate >= 99:
            return "服务稳定性良好，建议关注少量失败请求。"
        elif success_rate >= 95:
            return "服务稳定性一般，需要分析失败原因并优化。"
        else:
            return "服务稳定性较差，建议立即分析并修复问题。"
    
    def _get_response_time_suggestion(self, avg_rt: float) -> str:
        """
        根据响应时间获取建议
        
        Args:
            avg_rt: 平均响应时间
            
        Returns:
            str: 建议
        """
        if avg_rt < 100:
            return "响应时间优秀，用户体验良好。"
        elif avg_rt < 300:
            return "响应时间良好，可以考虑进一步优化。"
        elif avg_rt < 1000:
            return "响应时间一般，建议优化数据库查询或服务性能。"
        else:
            return "响应时间较长，需要重点优化服务性能。"
    
    def _get_throughput_suggestion(self, actual_rps: float, target_rps: float) -> str:
        """
        根据吞吐量获取建议
        
        Args:
            actual_rps: 实际RPS
            target_rps: 目标RPS
            
        Returns:
            str: 建议
        """
        if target_rps <= 0:
            return "建议设置性能目标，以便更好地评估系统性能。"
        elif actual_rps >= target_rps:
            return "系统吞吐量满足要求，可以考虑进行更高负载的测试。"
        elif actual_rps >= target_rps * 0.8:
            return "系统吞吐量接近目标，可以通过优化配置提升性能。"
        else:
            return "系统吞吐量未达到目标，建议检查系统瓶颈并优化。"
    
    def _generate_text_report(self) -> str:
        """
        生成文本格式报告
        
        Returns:
            str: 文本格式的报告
        """
        summary = self._metrics.get('summary', {})
        analysis = self._generate_performance_analysis()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("性能测试报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {self._report_time}")
        report_lines.append(f"测试类型: {self._format_test_type(self._test_config.test_type)}")
        
        # 环境信息
        env_info = self._get_environment_info()
        report_lines.append("环境信息:")
        report_lines.append(f"  操作系统: {env_info['os']}")
        report_lines.append(f"  Python版本: {env_info['python_version']}")
        
        report_lines.append(f"测试配置:")
        report_lines.append(f"  持续时间: {self._test_config.duration}秒")
        report_lines.append(f"  并发用户数: {self._test_config.concurrent_users}")
        
        if self._test_config.test_type == 'ramp_up':
            report_lines.append(f"  爬坡时间: {self._test_config.ramp_up_time}秒")
            report_lines.append(f"  爬坡步数: {self._test_config.ramp_up_steps}")
        elif self._test_config.test_type == 'tps':
            report_lines.append(f"  目标TPS: {self._test_config.target_tps}")
        elif self._test_config.test_type == 'qps':
            report_lines.append(f"  目标QPS: {self._test_config.target_qps}")
        
        report_lines.append(f"  超时时间: {self._test_config.timeout}秒")
        report_lines.append(f"  思考时间: {self._test_config.think_time}秒")
        report_lines.append(f"  遇错即停: {'是' if self._test_config.stop_on_error else '否'}")
        if hasattr(self._test_config, 'connection_timeout'):
            report_lines.append(f"  连接超时: {self._test_config.connection_timeout}秒")
        if hasattr(self._test_config, 'max_retries'):
            report_lines.append(f"  最大重试次数: {self._test_config.max_retries}")
        report_lines.append("-" * 80)
        
        # 请求统计
        report_lines.append("请求统计:")
        report_lines.append(f"  总请求数: {summary.get('total_requests', 0)}")
        report_lines.append(f"  成功请求: {summary.get('successful_requests', 0)}")
        report_lines.append(f"  失败请求: {summary.get('failed_requests', 0)}")
        report_lines.append(f"  成功率: {summary.get('success_rate', 0):.2f}%")
        report_lines.append(f"  每秒请求数(RPS): {summary.get('rps', 0):.2f}")
        report_lines.append(f"  RPS最大值: {summary.get('max_rps', 0):.2f}")
        report_lines.append(f"  RPS最小值: {summary.get('min_rps', 0):.2f}")
        report_lines.append(f"  RPS 95%峰值: {summary.get('p95_rps', 0):.2f}")
        report_lines.append(f"  成功RPS: {summary.get('success_rps', 0):.2f}")
        report_lines.append(f"  失败RPS: {summary.get('failed_rps', 0):.2f}")
        report_lines.append("-" * 80)
        
        # 响应时间统计
        report_lines.append("响应时间统计(毫秒):")
        report_lines.append(f"  平均响应时间: {summary.get('avg_response_time', 0):.2f}")
        report_lines.append(f"  最小响应时间: {summary.get('min_response_time', 0):.2f}")
        report_lines.append(f"  最大响应时间: {summary.get('max_response_time', 0):.2f}")
        report_lines.append(f"  50%分位响应时间: {summary.get('p50_response_time', 0):.2f}")
        report_lines.append(f"  90%分位响应时间: {summary.get('p90_response_time', 0):.2f}")
        report_lines.append(f"  95%分位响应时间: {summary.get('p95_response_time', 0):.2f}")
        report_lines.append(f"  99%分位响应时间: {summary.get('p99_response_time', 0):.2f}")
        report_lines.append(f"  99.9%分位响应时间: {summary.get('p99_9_response_time', 0):.2f}")
        report_lines.append(f"  响应时间标准差: {summary.get('response_time_std', 0):.2f}")
        report_lines.append("-" * 80)
        
        # 延迟分布统计
        latency_breakdown = summary.get('latency_breakdown', {})
        if latency_breakdown:
            report_lines.append("延迟分布统计:")
            for latency_range, count in sorted(latency_breakdown.items()):
                percentage = (count / summary.get('total_requests', 1)) * 100
                report_lines.append(f"  {latency_range}: {count} ({percentage:.2f}%)")
            report_lines.append("-" * 80)
        
        # 连接指标
        connection_metrics = summary.get('connection_metrics', {})
        if connection_metrics:
            report_lines.append("连接指标:")
            if 'total_connections' in connection_metrics:
                report_lines.append(f"  总连接数: {connection_metrics['total_connections']}")
            if 'active_connections' in connection_metrics:
                report_lines.append(f"  活跃连接数: {connection_metrics['active_connections']}")
            if 'connection_errors' in connection_metrics:
                report_lines.append(f"  连接错误数: {connection_metrics['connection_errors']}")
            report_lines.append("-" * 80)
        
        # 状态码分布
        status_codes = summary.get('status_codes_distribution', {})
        if status_codes:
            report_lines.append("状态码分布:")
            for code, count in sorted(status_codes.items()):
                percentage = (count / summary.get('total_requests', 1)) * 100
                report_lines.append(f"  {code}: {count} ({percentage:.2f}%)")
            report_lines.append("-" * 80)
        
        # 错误分布
        errors = summary.get('errors_distribution', {})
        if errors:
            report_lines.append("错误分布:")
            for error, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary.get('total_requests', 1)) * 100
                report_lines.append(f"  {error}: {count} ({percentage:.2f}%)")
            report_lines.append("-" * 80)
        
        # 性能分析
        report_lines.append("性能分析:")
        report_lines.append(f"  成功率分析: {analysis['success_analysis']['status']} - {analysis['success_analysis']['suggestion']}")
        report_lines.append(f"  响应时间分析: {analysis['response_time_analysis']['status']} - {analysis['response_time_analysis']['suggestion']}")
        report_lines.append(f"  吞吐量分析: {analysis['throughput_analysis']['status']} - {analysis['throughput_analysis']['suggestion']}")
        report_lines.append("=" * 80)
        
        return '\n'.join(report_lines)
    
    def _generate_html_report(self) -> str:
        """
        生成HTML格式报告
        
        Returns:
            str: HTML格式的报告
        """
        summary = self._metrics.get('summary', {})
        time_series = self._metrics.get('time_series', [])
        
        # HTML模板
        html_template = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        h1 {{
            font-size: 28px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            font-size: 22px;
            margin-top: 30px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .info-box {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 25px;
            border-left: 4px solid #6c757d;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #6c757d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .chart-container {{
            margin-bottom: 30px;
            background-color: #fafafa;
            padding: 20px;
            border-radius: 6px;
        }}
        .highlight {{
            font-weight: bold;
            color: #e74c3c;
        }}
        .success {{
            color: #27ae60;
        }}
        .warning {{
            color: #f39c12;
        }}
        .error {{
            color: #e74c3c;
        }}
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            .container {{
                padding: 15px;
            }}
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>性能测试报告</h1>
        
        <div class="info-box">
            <p><strong>生成时间:</strong> {self._report_time}</p>
            <p><strong>测试类型:</strong> {self._format_test_type(self._test_config.test_type)}</p>
            <p><strong>测试配置:</strong></p>
            <ul>
                <li>持续时间: {self._test_config.duration}秒</li>
                <li>并发用户数: {self._test_config.concurrent_users}</li>
                {'<li>爬坡时间: ' + str(self._test_config.ramp_up_time) + '秒</li><li>爬坡步数: ' + str(self._test_config.ramp_up_steps) + '</li>' if self._test_config.test_type == 'ramp_up' else ''}
                {'<li>目标TPS: ' + str(self._test_config.target_tps) + '</li>' if self._test_config.test_type == 'tps' and self._test_config.target_tps else ''}
                {'<li>目标QPS: ' + str(self._test_config.target_qps) + '</li>' if self._test_config.test_type == 'qps' and self._test_config.target_qps else ''}
                <li>超时时间: {self._test_config.timeout}秒</li>
                <li>思考时间: {self._test_config.think_time}秒</li>
                <li>遇错即停: {'是' if self._test_config.stop_on_error else '否'}</li>
            </ul>
        </div>
        
        <h2>关键指标</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary.get('total_requests', 0)}</div>
                <div class="stat-label">总请求数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {self._get_success_rate_class(summary.get('success_rate', 0))}">{summary.get('success_rate', 0):.2f}%</div>
                <div class="stat-label">成功率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('rps', 0):.2f}</div>
                <div class="stat-label">平均RPS</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('max_rps', 0):.2f}</div>
                <div class="stat-label">最大RPS</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('avg_response_time', 0):.2f}ms</div>
                <div class="stat-label">平均响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('p95_response_time', 0):.2f}ms</div>
                <div class="stat-label">95%响应时间</div>
            </div>
        </div>
        
        <h2>响应时间统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary.get('min_response_time', 0):.2f}ms</div>
                <div class="stat-label">最小响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('p50_response_time', 0):.2f}ms</div>
                <div class="stat-label">50%分位响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('p90_response_time', 0):.2f}ms</div>
                <div class="stat-label">90%分位响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('p95_response_time', 0):.2f}ms</div>
                <div class="stat-label">95%分位响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('p99_response_time', 0):.2f}ms</div>
                <div class="stat-label">99%分位响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('p99_9_response_time', 0):.2f}ms</div>
                <div class="stat-label">99.9%分位响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('max_response_time', 0):.2f}ms</div>
                <div class="stat-label">最大响应时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.get('response_time_std', 0):.2f}ms</div>
                <div class="stat-label">响应时间标准差</div>
            </div>
        </div>
        
        <h2>请求统计详情</h2>
        <table>
            <thead>
                <tr>
                    <th>总请求数</th>
                    <th>成功请求</th>
                    <th>失败请求</th>
                    <th>测试持续时间</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{summary.get('total_requests', 0)}</td>
                    <td class="success">{summary.get('successful_requests', 0)}</td>
                    <td class="error">{summary.get('failed_requests', 0)}</td>
                    <td>{self._metrics.get('test_duration', 0):.2f}秒</td>
                </tr>
            </tbody>
        </table>
        
        {self._generate_status_code_table(summary.get('status_codes_distribution', {}), summary.get('total_requests', 0))}
        
        {self._generate_error_table(summary.get('errors_distribution', {}), summary.get('total_requests', 0))}
        
        {self._generate_time_series_chart(time_series) if time_series else ''}
        
        {self._generate_latency_distribution_chart(summary.get('latency_breakdown', {})) if summary.get('latency_breakdown', {}) else ''}
        
        {self._generate_connection_metrics_section(summary.get('connection_metrics', {})) if summary.get('connection_metrics', {}) else ''}
        
        {self._generate_performance_analysis_section(self._generate_performance_analysis())}
    </div>
    
    <script>
        // 平滑图表动画
        Chart.defaults.animation.easing = 'easeOutQuart';
    </script>
</body>
</html>
'''
        
        return html_template
    
    def _format_test_type(self, test_type: str) -> str:
        """
        格式化测试类型为中文
        
        Args:
            test_type: 测试类型
            
        Returns:
            str: 中文测试类型名称
        """
        type_map = {
            'tps': 'TPS测试',
            'qps': 'QPS测试',
            'concurrent': '并发测试',
            'ramp_up': '爬坡测试'
        }
        return type_map.get(test_type, test_type)
    
    def _get_success_rate_class(self, success_rate: float) -> str:
        """
        根据成功率返回对应的CSS类
        
        Args:
            success_rate: 成功率
            
        Returns:
            str: CSS类名
        """
        if success_rate >= 99:
            return 'success'
        elif success_rate >= 95:
            return 'warning'
        else:
            return 'error'
    
    def _generate_status_code_table(self, status_codes: Dict[int, int], total: int) -> str:
        """
        生成状态码分布表格
        
        Args:
            status_codes: 状态码分布
            total: 总请求数
            
        Returns:
            str: HTML表格
        """
        if not status_codes:
            return ''
        
        rows = []
        for code, count in sorted(status_codes.items()):
            percentage = (count / total * 100) if total > 0 else 0
            class_name = 'success' if 200 <= code < 400 else 'error' if code >= 500 else 'warning'
            rows.append(f"""
                <tr>
                    <td>{code}</td>
                    <td class="{class_name}">{count}</td>
                    <td>{percentage:.2f}%</td>
                </tr>
            """)
        
        return f"""
        <h2>状态码分布</h2>
        <table>
            <thead>
                <tr>
                    <th>状态码</th>
                    <th>数量</th>
                    <th>百分比</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _generate_error_table(self, errors: Dict[str, int], total: int) -> str:
        """
        生成错误分布表格
        
        Args:
            errors: 错误分布
            total: 总请求数
            
        Returns:
            str: HTML表格
        """
        if not errors:
            return ''
        
        rows = []
        for error, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            rows.append(f"""
                <tr>
                    <td>{error}</td>
                    <td class="error">{count}</td>
                    <td>{percentage:.2f}%</td>
                </tr>
            """)
        
        return f"""
        <h2>错误分布</h2>
        <table>
            <thead>
                <tr>
                    <th>错误类型</th>
                    <th>数量</th>
                    <th>百分比</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _generate_time_series_chart(self, time_series: list) -> str:
        """
        生成时间序列图表
        
        Args:
            time_series: 时间序列数据
            
        Returns:
            str: HTML图表代码
        """
        if not time_series:
            return ''
        
        # 准备图表数据
        labels = [item['datetime'] for item in time_series]
        rps_data = [item['rps'] for item in time_series]
        success_rps_data = [item.get('success_rps', 0) for item in time_series]
        failed_rps_data = [item.get('failed_rps', 0) for item in time_series]
        success_rate_data = [item['success_rate'] for item in time_series]
        avg_response_time_data = [item['avg_response_time'] for item in time_series]
        p95_response_time_data = [item.get('p95_response_time', 0) for item in time_series]
        concurrent_users_data = [item.get('concurrent_users', 0) for item in time_series]
        
        return f"""
        <h2>性能趋势图</h2>
        <div class="chart-container">
            <canvas id="rpsChart" width="400" height="200"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="responseTimeChart" width="400" height="200"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="usersChart" width="400" height="200"></canvas>
        </div>
        
        <script>
            // RPS图表
            const rpsCtx = document.getElementById('rpsChart').getContext('2d');
            const rpsChart = new Chart(rpsCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [
                        {{
                            label: '总RPS',
                            data: {json.dumps(rps_data)},
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false
                        }},
                        {{
                            label: '成功RPS',
                            data: {json.dumps(success_rps_data)},
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false
                        }},
                        {{
                            label: '失败RPS',
                            data: {json.dumps(failed_rps_data)},
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false
                        }},
                        {{
                            label: '成功率(%)',
                            data: {json.dumps(success_rate_data)},
                            borderColor: '#9b59b6',
                            backgroundColor: 'rgba(155, 89, 182, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false,
                            yAxisID: 'y1',
                            borderDash: [5, 5]
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'RPS和成功率趋势'
                        }},
                        tooltip: {{
                            mode: 'index',
                            intersect: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: '每秒请求数'
                            }}
                        }},
                        y1: {{
                            beginAtZero: true,
                            max: 100,
                            position: 'right',
                            title: {{
                                display: true,
                                text: '成功率(%)'
                            }},
                            grid: {{
                                drawOnChartArea: false
                            }}
                        }}
                    }}
                }}
            }});
            
            // 响应时间图表
            const rtCtx = document.getElementById('responseTimeChart').getContext('2d');
            const rtChart = new Chart(rtCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [
                        {{
                            label: '平均响应时间(ms)',
                            data: {json.dumps(avg_response_time_data)},
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false
                        }},
                        {{
                            label: '95%响应时间(ms)',
                            data: {json.dumps(p95_response_time_data)},
                            borderColor: '#f39c12',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false,
                            borderDash: [3, 3]
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '响应时间趋势'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: '响应时间(ms)'
                            }}
                        }}
                    }}
                }}
            }});
            
            // 并发用户数图表
            const usersCtx = document.getElementById('usersChart').getContext('2d');
            const usersChart = new Chart(usersCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: '并发用户数',
                        data: {json.dumps(concurrent_users_data)},
                        borderColor: '#1abc9c',
                        backgroundColor: 'rgba(26, 188, 156, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '并发用户数趋势'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: '并发用户数'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
        """
    
    def _generate_latency_distribution_chart(self, latency_breakdown: Dict[str, int]) -> str:
        """
        生成延迟分布图表
        
        Args:
            latency_breakdown: 延迟分布数据
            
        Returns:
            str: HTML图表代码
        """
        if not latency_breakdown:
            return ''
        
        labels = list(latency_breakdown.keys())
        data = list(latency_breakdown.values())
        
        # 定义颜色
        colors = [
            '#27ae60', '#2ecc71', '#3498db', '#34495e', 
            '#9b59b6', '#f39c12', '#e67e22', '#e74c3c'
        ]
        
        return f"""
        <h2>延迟分布</h2>
        <div class="chart-container">
            <canvas id="latencyChart" width="400" height="300"></canvas>
        </div>
        
        <script>
            const latencyCtx = document.getElementById('latencyChart').getContext('2d');
            const latencyChart = new Chart(latencyCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: '请求数量',
                        data: {json.dumps(data)},
                        backgroundColor: {json.dumps(colors[:len(labels)])},
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '响应时间分布'
                        }},
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: '请求数量'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: '响应时间范围(ms)'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
        """
    
    def _generate_connection_metrics_section(self, connection_metrics: Dict[str, Any]) -> str:
        """
        生成连接指标部分
        
        Args:
            connection_metrics: 连接指标数据
            
        Returns:
            str: HTML代码
        """
        if not connection_metrics:
            return ''
        
        return f"""
        <h2>连接指标</h2>
        <div class="stats-grid">
            {f'<div class="stat-card"><div class="stat-value">{connection_metrics.get("total_connections", 0)}</div><div class="stat-label">总连接数</div></div>' if "total_connections" in connection_metrics else ''}
            {f'<div class="stat-card"><div class="stat-value">{connection_metrics.get("active_connections", 0)}</div><div class="stat-label">活跃连接数</div></div>' if "active_connections" in connection_metrics else ''}
            {f'<div class="stat-card"><div class="stat-value {"error" if connection_metrics.get("connection_errors", 0) > 0 else "success"}">{connection_metrics.get("connection_errors", 0)}</div><div class="stat-label">连接错误数</div></div>' if "connection_errors" in connection_metrics else ''}
        </div>
        """
    
    def _generate_performance_analysis_section(self, analysis: Dict[str, Any]) -> str:
        """
        生成性能分析部分
        
        Args:
            analysis: 性能分析结果
            
        Returns:
            str: HTML代码
        """
        
        def get_analysis_class(status: str) -> str:
            if status in ['优秀', '良好']:
                return 'success'
            elif status == '一般':
                return 'warning'
            else:
                return 'error'
        
        return f"""
        <h2>性能分析</h2>
        <div class="analysis-container">
            <div class="analysis-card">
                <h3>成功率分析</h3>
                <div class="analysis-status {get_analysis_class(analysis['success_analysis']['status'])} ">{analysis['success_analysis']['status']}</div>
                <p class="analysis-rate">成功率: {analysis['success_analysis']['rate']:.2f}%</p>
                <p class="analysis-suggestion">{analysis['success_analysis']['suggestion']}</p>
            </div>
            
            <div class="analysis-card">
                <h3>响应时间分析</h3>
                <div class="analysis-status {get_analysis_class(analysis['response_time_analysis']['status'])} ">{analysis['response_time_analysis']['status']}</div>
                <p class="analysis-rate">平均响应时间: {analysis['response_time_analysis']['avg_response_time']:.2f}ms</p>
                <p class="analysis-suggestion">{analysis['response_time_analysis']['suggestion']}</p>
            </div>
            
            <div class="analysis-card">
                <h3>吞吐量分析</h3>
                <div class="analysis-status {get_analysis_class(analysis['throughput_analysis']['status'])} ">{analysis['throughput_analysis']['status']}</div>
                <p class="analysis-rate">实际RPS: {analysis['throughput_analysis']['actual_rps']:.2f}</p>
                {f'<p class="analysis-target">目标RPS: {analysis["throughput_analysis"]["target_rps"]}</p>' if analysis['throughput_analysis']['target_rps'] > 0 else ''}
                <p class="analysis-suggestion">{analysis['throughput_analysis']['suggestion']}</p>
            </div>
        </div>
        
        <style>
            .analysis-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .analysis-card {{
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 25px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #3498db;
            }}
            
            .analysis-card h3 {{
                margin-top: 0;
                margin-bottom: 15px;
                color: #2c3e50;
                font-size: 18px;
            }}
            
            .analysis-status {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 4px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            
            .analysis-rate, .analysis-target {{
                font-size: 16px;
                margin-bottom: 10px;
                color: #495057;
            }}
            
            .analysis-suggestion {{
                font-size: 14px;
                line-height: 1.6;
                color: #6c757d;
            }}
        </style>
        """