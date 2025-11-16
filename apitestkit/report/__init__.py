"""
报告生成模块

提供专业、美观的测试报告生成功能，支持多种格式输出
"""

from .report_generator import (
    ReportGenerator,
    ReportFormat,
    generate_html_report,
    generate_pdf_report,
    generate_json_report,
    generate_csv_report,
    generate_excel_report
)
from .charts_generator import ChartsGenerator

__all__ = [
    'ReportGenerator',
    'ReportFormat',
    'ChartsGenerator',
    'generate_html_report',
    'generate_pdf_report',
    'generate_json_report',
    'generate_csv_report',
    'generate_excel_report'
]