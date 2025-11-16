"""
报告生成器主类

提供多种格式的测试报告生成功能，支持HTML、PDF和JSON格式
"""

import os
import time
import json
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path

# 可选导入weasyprint用于PDF生成
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from apitestkit.test.test_runner import RunnerResult
from apitestkit.core.logger import create_user_logger
from apitestkit.report.charts_generator import ChartsGenerator


class ReportFormat(Enum):
    """
    报告格式枚举
    """
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


class ReportGenerator:
    """
    测试报告生成器
    
    提供专业、美观的测试报告生成功能，支持多种格式输出
    """
    
    def __init__(self, output_dir: str = None, template_type: str = "modern"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
            template_type: 模板类型 (modern, professional, simple)
        """
        self.logger = create_user_logger("report_generator")
        # 使用Path对象进行路径处理，确保跨平台兼容性
        default_output_path = Path('reports') / f"report_{time.strftime('%Y%m%d_%H%M%S')}"
        self.output_dir_path = Path(output_dir) if output_dir else default_output_path
        self.output_dir = str(self.output_dir_path)
        self.template_type = template_type
        self.charts_generator = ChartsGenerator()
        
        # 确保输出目录存在
        self.output_dir_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"报告生成器初始化成功，输出目录: {self.output_dir}")
    
    def generate_report(self, result: RunnerResult, formats: List[ReportFormat] = None) -> Dict[str, str]:
        """
        生成测试报告
        
        Args:
            result: 测试运行结果
            formats: 要生成的报告格式列表
            
        Returns:
            Dict[str, str]: 生成的报告文件路径映射
        """
        if formats is None:
            formats = [ReportFormat.HTML, ReportFormat.JSON]
        
        # 准备报告数据
        report_data = self._prepare_report_data(result)
        
        # 生成各格式报告
        output_files = {}
        
        for report_format in formats:
            try:
                if report_format == ReportFormat.HTML:
                    output_files['html'] = self._generate_html_report(report_data)
                elif report_format == ReportFormat.PDF:
                    html_path = output_files.get('html') or self._generate_html_report(report_data)
                    output_files['pdf'] = self._generate_pdf_report(html_path)
                elif report_format == ReportFormat.JSON:
                    output_files['json'] = self._generate_json_report(report_data)
                elif report_format == ReportFormat.CSV:
                    output_files['csv'] = self._generate_csv_report(report_data)
                elif report_format == ReportFormat.EXCEL:
                    output_files['excel'] = self._generate_excel_report(report_data)
                    
                self.logger.info(f"成功生成 {report_format.value.upper()} 格式报告")
            except Exception as e:
                self.logger.error(f"生成 {report_format.value.upper()} 格式报告失败: {str(e)}")
        
        return output_files
    
    def _prepare_report_data(self, result: RunnerResult) -> Dict[str, Any]:
        """
        准备报告数据
        
        Args:
            result: 测试运行结果
            
        Returns:
            Dict[str, Any]: 处理后的报告数据
        """
        # 转换为字典格式
        report_data = {
            'title': f"API测试报告 - {result.runner_id[:8]}",
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.start_time)),
            'summary': {
                'total_suites': result.total_suites,
                'total_tests': result.total_tests,
                'passed': result.passed,
                'failed': result.failed,
                'errors': result.errors,
                'duration': f"{result.duration:.3f}s",
                'pass_rate': f"{((result.passed / result.total_tests) * 100) if result.total_tests > 0 else 0:.2f}%"
            },
            'suite_results': [asdict(suite) for suite in result.suite_results],
            'metadata': result.metadata or {},
            'charts': {}
        }
        
        # 生成图表数据
        report_data['charts'] = self._generate_charts_data(result)
        
        # 添加详细的测试统计
        self._add_detailed_statistics(report_data)
        
        return report_data
    
    def _generate_charts_data(self, result: RunnerResult) -> Dict[str, Any]:
        """
        生成图表数据
        
        Args:
            result: 测试运行结果
            
        Returns:
            Dict[str, Any]: 图表数据
        """
        # 总体统计图表
        overall_stats = {
            'passed': result.passed,
            'failed': result.failed,
            'errors': result.errors
        }
        
        # 套件统计图表
        suite_stats = []
        for suite in result.suite_results:
            suite_stats.append({
                'name': suite.suite_name,
                'total': suite.total_tests,
                'passed': suite.passed,
                'failed': suite.failed,
                'duration': suite.duration
            })
        
        # 响应时间统计
        response_times = []
        for suite in result.suite_results:
            for test in suite.test_results:
                if test.duration > 0:
                    response_times.append({
                        'name': f"{suite.suite_name} - {test.test_name}",
                        'duration': test.duration
                    })
        
        # 按响应时间排序（取前20个）
        response_times = sorted(response_times, key=lambda x: x['duration'], reverse=True)[:20]
        
        return {
            'overall_stats': overall_stats,
            'suite_stats': suite_stats,
            'response_times': response_times
        }
    
    def _add_detailed_statistics(self, report_data: Dict[str, Any]):
        """
        添加详细的测试统计信息
        
        Args:
            report_data: 报告数据
        """
        # 计算成功率趋势
        pass_rates = []
        for suite in report_data['suite_results']:
            if suite['total_tests'] > 0:
                pass_rate = (suite['passed'] / suite['total_tests']) * 100
                pass_rates.append({
                    'name': suite['suite_name'],
                    'pass_rate': pass_rate
                })
        
        report_data['detailed_stats'] = {
            'pass_rates_by_suite': pass_rates,
            'average_test_duration': self._calculate_average_duration(report_data['suite_results']),
            'slowest_tests': self._find_slowest_tests(report_data['suite_results'], limit=10)
        }
    
    def _calculate_average_duration(self, suite_results: List[Dict[str, Any]]) -> float:
        """
        计算平均测试执行时间
        
        Args:
            suite_results: 套件结果列表
            
        Returns:
            float: 平均执行时间
        """
        total_duration = 0
        total_tests = 0
        
        for suite in suite_results:
            total_duration += suite['duration']
            total_tests += suite['total_tests']
        
        return total_duration / total_tests if total_tests > 0 else 0
    
    def _find_slowest_tests(self, suite_results: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        找出最慢的测试用例
        
        Args:
            suite_results: 套件结果列表
            limit: 返回的最大数量
            
        Returns:
            List[Dict[str, Any]]: 最慢的测试用例列表
        """
        slow_tests = []
        
        for suite in suite_results:
            for test in suite['test_results']:
                slow_tests.append({
                    'name': f"{suite['suite_name']} - {test['test_name']}",
                    'duration': test['duration'],
                    'status': test['status']
                })
        
        # 按执行时间排序
        slow_tests.sort(key=lambda x: x['duration'], reverse=True)
        return slow_tests[:limit]
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成HTML格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: HTML文件路径
        """
        # 加载模板
        template_path = self._get_template_path('report.html')
        template_path_obj = Path(template_path)
        if not template_path_obj.exists():
            # 使用内置模板
            template_content = self._get_default_html_template()
            template = Template(template_content)
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = Template(f.read())
        
        # 渲染模板
        html_content = template.render(**report_data)
        
        # 保存文件
        output_path = str(Path(self.output_dir) / 'report.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_pdf_report(self, html_path: str) -> str:
        """
        生成PDF格式报告
        
        Args:
            html_path: HTML文件路径
            
        Returns:
            str: PDF文件路径
        """
        if not WEASYPRINT_AVAILABLE:
            self.logger.warning("WeasyPrint未安装，无法生成PDF报告。请安装: pip install weasyprint")
            return None
            
        output_path = str(Path(self.output_dir) / 'report.pdf')
        
        try:
            HTML(filename=html_path).write_pdf(output_path)
            return output_path
        except Exception as e:
            self.logger.error(f"生成PDF报告失败: {str(e)}")
            return None
    
    def _generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成JSON格式报告，包含更丰富的测试信息和统计数据
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: JSON文件路径
        """
        # 使用Path对象确保跨平台兼容性
        output_path = str(self.output_dir_path / 'report.json')
        
        # 优化报告结构，确保包含所有重要信息
        optimized_report = {
            "report_info": {
                "title": report_data.get('title', 'API测试报告'),
                "generated_at": report_data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S')),
                "generator_version": "1.0.0"
            },
            "summary_statistics": report_data.get('summary', {}),
            "detailed_results": report_data.get('suite_results', []),
            "metadata": report_data.get('metadata', {}),
            "charts_data": report_data.get('charts', {})
        }
        
        # 添加更友好的格式化
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(optimized_report, f, ensure_ascii=False, indent=2, sort_keys=False)
        
        self.logger.info(f"已生成优化格式的JSON报告，路径: {output_path}")
        return output_path
    
    def _generate_csv_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成CSV格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: CSV文件路径
        """
        import csv
        
        # 使用Path对象确保跨平台兼容性
        output_path = str(self.output_dir_path / 'report.csv')
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题行
            writer.writerow(['测试套件', '测试名称', '状态', '执行时间(秒)', '错误信息'])
            
            # 写入测试结果
            for suite in report_data['suite_results']:
                for test in suite['test_results']:
                    error_msg = '; '.join(test['errors']) if test['errors'] else ''
                    writer.writerow([
                        suite['suite_name'],
                        test['test_name'],
                        test['status'],
                        f"{test['duration']:.3f}",
                        error_msg
                    ])
        
        return output_path
    
    def _generate_excel_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成Excel格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: Excel文件路径
        """
        try:
            import openpyxl
        except ImportError:
            self.logger.warning("openpyxl未安装，无法生成Excel报告。请安装: pip install openpyxl")
            return None
        
        # 创建工作簿
        wb = openpyxl.Workbook()
        
        # 概览工作表
        overview_sheet = wb.active
        overview_sheet.title = '概览'
        
        # 写入概览数据
        overview_sheet['A1'] = '统计项'
        overview_sheet['B1'] = '数值'
        overview_sheet.append(['总套件数', report_data['summary']['total_suites']])
        overview_sheet.append(['总测试数', report_data['summary']['total_tests']])
        overview_sheet.append(['通过', report_data['summary']['passed']])
        overview_sheet.append(['失败', report_data['summary']['failed']])
        overview_sheet.append(['错误', report_data['summary']['errors']])
        overview_sheet.append(['总耗时', report_data['summary']['duration']])
        overview_sheet.append(['通过率', report_data['summary']['pass_rate']])
        
        # 详细结果工作表
        details_sheet = wb.create_sheet('详细结果')
        details_sheet['A1'] = '测试套件'
        details_sheet['B1'] = '测试名称'
        details_sheet['C1'] = '状态'
        details_sheet['D1'] = '执行时间(秒)'
        details_sheet['E1'] = '错误信息'
        
        # 写入详细结果
        for suite in report_data['suite_results']:
            for test in suite['test_results']:
                error_msg = '; '.join(test['errors']) if test['errors'] else ''
                details_sheet.append([
                    suite['suite_name'],
                    test['test_name'],
                    test['status'],
                    test['duration'],
                    error_msg
                ])
        
        # 保存文件 - 使用Path对象确保跨平台兼容性
        output_path = str(self.output_dir_path / 'report.xlsx')
        wb.save(output_path)
        
        return output_path
    
    def _get_template_path(self, template_name: str) -> str:
        """
        获取模板文件路径
        
        Args:
            template_name: 模板文件名
            
        Returns:
            模板文件的绝对路径
        """
        # 使用Path对象进行路径处理，确保跨平台兼容性
        
        # 首先检查自定义模板
        custom_template_dir = Path('templates') / self.template_type
        custom_template_path = custom_template_dir / template_name
        
        if custom_template_path.exists():
            return str(custom_template_path)
        
        # 然后使用内置模板
        builtin_template_dir = Path(__file__).parent / 'templates' / self.template_type
        return str(builtin_template_dir / template_name)
    
    def _get_default_html_template(self) -> str:
        """
        获取默认的HTML模板内容
        
        Returns:
            str: HTML模板内容
        """
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/antd@5.12.8/dist/reset.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .summary-card .value {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .summary-card .label {
            color: #666;
            font-size: 0.95rem;
        }
        
        .summary-card.pass .value {
            color: #52c41a;
        }
        
        .summary-card.fail .value {
            color: #f5222d;
        }
        
        .summary-card.error .value {
            color: #fa8c16;
        }
        
        .summary-card.total .value {
            color: #1890ff;
        }
        
        .charts-section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .chart-container {
            height: 400px;
        }
        
        .chart-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }
        
        .suite-results {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: #333;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .suite {
            margin-bottom: 30px;
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .suite-header {
            background-color: #fafafa;
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        .suite-header:hover {
            background-color: #f5f5f5;
        }
        
        .suite-name {
            font-weight: 600;
            font-size: 1.1rem;
            color: #333;
        }
        
        .suite-stats {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
        }
        
        .suite-content {
            padding: 20px;
            display: none;
        }
        
        .suite.expanded .suite-content {
            display: block;
        }
        
        .test-case {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            background-color: #fafafa;
        }
        
        .test-case-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .test-name {
            font-weight: 500;
            color: #333;
        }
        
        .test-status {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .test-status.passed {
            background-color: #f6ffed;
            color: #52c41a;
        }
        
        .test-status.failed {
            background-color: #fff1f0;
            color: #f5222d;
        }
        
        .test-status.error {
            background-color: #fff7e6;
            color: #fa8c16;
        }
        
        .test-details {
            font-size: 0.9rem;
            color: #666;
        }
        
        .error-message {
            background-color: #fff1f0;
            color: #f5222d;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 0.85rem;
            border-left: 3px solid #f5222d;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }
        
        .toggle-icon {
            transition: transform 0.3s ease;
        }
        
        .suite.expanded .toggle-icon {
            transform: rotate(180deg);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="subtitle">生成时间: {{ timestamp }}</div>
        </div>
        
        <div class="summary-cards">
            <div class="summary-card total">
                <div class="value">{{ summary.total_tests }}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="summary-card pass">
                <div class="value">{{ summary.passed }}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card fail">
                <div class="value">{{ summary.failed }}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card error">
                <div class="value">{{ summary.errors }}</div>
                <div class="label">错误</div>
            </div>
        </div>
        
        <div class="charts-section">
            <h2 class="section-title">测试统计图表</h2>
            <div class="charts-grid">
                <div>
                    <div class="chart-title">测试状态分布</div>
                    <div id="statusChart" class="chart-container"></div>
                </div>
                <div>
                    <div class="chart-title">套件执行时间</div>
                    <div id="durationChart" class="chart-container"></div>
                </div>
            </div>
        </div>
        
        <div class="suite-results">
            <h2 class="section-title">测试套件结果</h2>
            
            {% for suite in suite_results %}
            <div class="suite">
                <div class="suite-header" onclick="toggleSuite(this.parentElement)">
                    <div class="suite-name">{{ suite.suite_name }}</div>
                    <div class="suite-stats">
                        <span>测试: {{ suite.total_tests }}</span>
                        <span>通过: {{ suite.passed }}</span>
                        <span>失败: {{ suite.failed }}</span>
                        <span>耗时: {{ "%.3f"|format(suite.duration) }}s</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <div class="suite-content">
                    {% for test in suite.test_results %}
                    <div class="test-case">
                        <div class="test-case-header">
                            <div class="test-name">{{ test.test_name }}</div>
                            <span class="test-status {{ test.status }}">{{ test.status }}</span>
                        </div>
                        <div class="test-details">
                            <div>执行时间: {{ "%.3f"|format(test.duration) }}s</div>
                            {% if test.errors %}
                            {% for error in test.errors %}
                            <div class="error-message">{{ error }}</div>
                            {% endfor %}
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>API测试报告 - 由ApiTestKit生成</p>
        </div>
    </div>
    
    <script>
        // 图表数据
        const chartData = {{ charts|tojson|safe }};
        
        // 初始化状态分布图表
        const statusChart = echarts.init(document.getElementById('statusChart'));
        const statusOption = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                left: 'left'
            },
            series: [
                {
                    name: '测试状态',
                    type: 'pie',
                    radius: '70%',
                    data: [
                        {value: chartData.overall_stats.passed, name: '通过', itemStyle: {color: '#52c41a'}},
                        {value: chartData.overall_stats.failed, name: '失败', itemStyle: {color: '#f5222d'}},
                        {value: chartData.overall_stats.errors, name: '错误', itemStyle: {color: '#fa8c16'}}
                    ],
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
        statusChart.setOption(statusOption);
        
        // 初始化执行时间图表
        const durationChart = echarts.init(document.getElementById('durationChart'));
        const suiteNames = chartData.suite_stats.map(s => s.name);
        const suiteDurations = chartData.suite_stats.map(s => s.duration);
        
        const durationOption = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                formatter: '{b}: {c}s'
            },
            xAxis: {
                type: 'category',
                data: suiteNames,
                axisLabel: {
                    rotate: 45
                }
            },
            yAxis: {
                type: 'value',
                name: '执行时间 (秒)'
            },
            series: [{
                data: suiteDurations,
                type: 'bar',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#667eea'},
                        {offset: 1, color: '#764ba2'}
                    ])
                }
            }]
        };
        durationChart.setOption(durationOption);
        
        // 响应式处理
        window.addEventListener('resize', function() {
            statusChart.resize();
            durationChart.resize();
        });
        
        // 切换套件展开/折叠状态
        function toggleSuite(suiteElement) {
            suiteElement.classList.toggle('expanded');
        }
    </script>
</body>
</html>
        '''
    
    def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成HTML报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: 生成的HTML报告文件路径
        """
        return self._generate_html_report(report_data)
    
    def generate_pdf_report(self, html_path: str) -> str:
        """
        生成PDF报告
        
        Args:
            html_path: HTML报告文件路径
            
        Returns:
            str: 生成的PDF报告文件路径
        
        Raises:
            ImportError: 当weasyprint模块不可用时
        """
        return self._generate_pdf_report(html_path)
    
    def generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成JSON报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: 生成的JSON报告文件路径
        """
        return self._generate_json_report(report_data)
    
    def generate_csv_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成CSV报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: 生成的CSV报告文件路径
        """
        return self._generate_csv_report(report_data)
    
    def generate_excel_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成Excel报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: 生成的Excel报告文件路径
        """
        return self._generate_excel_report(report_data)


def generate_html_report(report_data: Dict[str, Any], output_dir: str = None, template_type: str = "modern") -> str:
    """
    生成HTML报告
    
    Args:
        report_data: 报告数据
        output_dir: 输出目录
        template_type: 模板类型
        
    Returns:
        str: 生成的HTML报告文件路径
    """
    generator = ReportGenerator(output_dir=output_dir, template_type=template_type)
    return generator._generate_html_report(report_data)


def generate_pdf_report(html_path: str, output_dir: str = None) -> str:
    """
    生成PDF报告
    
    Args:
        html_path: HTML报告文件路径
        output_dir: 输出目录
        
    Returns:
        str: 生成的PDF报告文件路径
        
    Raises:
        ImportError: 当weasyprint模块不可用时
    """
    generator = ReportGenerator(output_dir=output_dir)
    return generator._generate_pdf_report(html_path)


def generate_json_report(report_data: Dict[str, Any], output_dir: str = None) -> str:
    """
    生成优化格式的JSON报告
    
    Args:
        report_data: 报告数据
        output_dir: 输出目录
        
    Returns:
        str: JSON文件路径
    """
    # 确保报告数据包含所有必要字段
    if 'test_suite' in report_data and 'results' in report_data:
        # 转换简单格式为优化格式
        optimized_data = {
            "report_info": {
                "title": f"API测试报告 - {report_data.get('test_suite', '未知测试套件')}",
                "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "generator_version": "1.0.0"
            },
            "summary_statistics": {
                "total_tests": len(report_data.get('results', [])),
                "passed": sum(1 for r in report_data.get('results', []) if r.get('status') == 'passed'),
                "failed": sum(1 for r in report_data.get('results', []) if r.get('status') == 'failed'),
                "duration": "0s",
                "pass_rate": f"{(sum(1 for r in report_data.get('results', []) if r.get('status') == 'passed') / len(report_data.get('results', [1]))) * 100:.2f}%"
            },
            "detailed_results": report_data.get('results', []),
            "metadata": {"test_suite": report_data.get('test_suite', '未知测试套件')}
        }
        report_data = optimized_data
    
    generator = ReportGenerator(output_dir)
    return generator._generate_json_report(report_data)


def generate_csv_report(report_data: Dict[str, Any], output_dir: str = None) -> str:
    """
    生成CSV报告
    
    Args:
        report_data: 报告数据
        output_dir: 输出目录
        
    Returns:
        str: 生成的CSV报告文件路径
    """
    generator = ReportGenerator(output_dir=output_dir)
    return generator._generate_csv_report(report_data)


def generate_excel_report(report_data: Dict[str, Any], output_dir: str = None) -> str:
    """
    生成Excel报告
    
    Args:
        report_data: 报告数据
        output_dir: 输出目录
        
    Returns:
        str: 生成的Excel报告文件路径
    """
    generator = ReportGenerator(output_dir=output_dir)
    return generator._generate_excel_report(report_data)