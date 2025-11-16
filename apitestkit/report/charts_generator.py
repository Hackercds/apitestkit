"""
图表生成器模块

提供测试报告中的各类数据可视化功能
"""

from typing import Dict, Any, List, Optional
import base64
import io
import json

from apitestkit.core.logger import create_user_logger


class ChartsGenerator:
    """
    图表生成器
    
    负责生成各类统计图表和数据可视化内容
    """
    
    def __init__(self):
        """
        初始化图表生成器
        """
        self.logger = create_user_logger("charts_generator")
        self.logger.info("图表生成器初始化成功")
    
    def generate_pie_chart(self, data: Dict[str, int], title: str = "饼图") -> Dict[str, Any]:
        """
        生成饼图数据
        
        Args:
            data: 饼图数据字典，key为分类，value为数值
            title: 图表标题
            
        Returns:
            Dict[str, Any]: 饼图配置数据
        """
        chart_data = {
            'type': 'pie',
            'title': title,
            'data': []
        }
        
        # 默认颜色配置
        colors = [
            '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1',
            '#13c2c2', '#eb2f96', '#fa541c', '#a0d911', '#fa8c16'
        ]
        
        # 转换数据格式
        for i, (name, value) in enumerate(data.items()):
            chart_data['data'].append({
                'name': name,
                'value': value,
                'itemStyle': {
                    'color': colors[i % len(colors)]
                }
            })
        
        return chart_data
    
    def generate_bar_chart(self, x_data: List[str], y_data: List[float], title: str = "柱状图", 
                         x_axis_name: str = "", y_axis_name: str = "") -> Dict[str, Any]:
        """
        生成柱状图数据
        
        Args:
            x_data: X轴数据列表
            y_data: Y轴数据列表
            title: 图表标题
            x_axis_name: X轴名称
            y_axis_name: Y轴名称
            
        Returns:
            Dict[str, Any]: 柱状图配置数据
        """
        if len(x_data) != len(y_data):
            self.logger.error("柱状图X轴和Y轴数据长度不匹配")
            raise ValueError("柱状图X轴和Y轴数据长度必须一致")
        
        chart_data = {
            'type': 'bar',
            'title': title,
            'xAxis': {
                'type': 'category',
                'name': x_axis_name,
                'data': x_data
            },
            'yAxis': {
                'type': 'value',
                'name': y_axis_name
            },
            'series': [
                {
                    'data': y_data,
                    'type': 'bar',
                    'itemStyle': {
                        'color': '#667eea'
                    }
                }
            ]
        }
        
        return chart_data
    
    def generate_line_chart(self, x_data: List[str], y_data: List[float], title: str = "折线图", 
                          x_axis_name: str = "", y_axis_name: str = "") -> Dict[str, Any]:
        """
        生成折线图数据
        
        Args:
            x_data: X轴数据列表
            y_data: Y轴数据列表
            title: 图表标题
            x_axis_name: X轴名称
            y_axis_name: Y轴名称
            
        Returns:
            Dict[str, Any]: 折线图配置数据
        """
        if len(x_data) != len(y_data):
            self.logger.error("折线图X轴和Y轴数据长度不匹配")
            raise ValueError("折线图X轴和Y轴数据长度必须一致")
        
        chart_data = {
            'type': 'line',
            'title': title,
            'xAxis': {
                'type': 'category',
                'name': x_axis_name,
                'data': x_data
            },
            'yAxis': {
                'type': 'value',
                'name': y_axis_name
            },
            'series': [
                {
                    'data': y_data,
                    'type': 'line',
                    'smooth': True,
                    'symbol': 'circle',
                    'symbolSize': 8,
                    'lineStyle': {
                        'width': 3,
                        'color': '#1890ff'
                    },
                    'itemStyle': {
                        'color': '#1890ff'
                    },
                    'areaStyle': {
                        'color': '#e6f7ff'
                    }
                }
            ]
        }
        
        return chart_data
    
    def generate_radar_chart(self, indicators: List[Dict[str, Any]], data: List[Dict[str, Any]], 
                           title: str = "雷达图") -> Dict[str, Any]:
        """
        生成雷达图数据
        
        Args:
            indicators: 指标配置列表，每个指标包含name和max属性
            data: 数据系列列表，每个系列包含name和value属性
            title: 图表标题
            
        Returns:
            Dict[str, Any]: 雷达图配置数据
        """
        chart_data = {
            'type': 'radar',
            'title': title,
            'radar': {
                'indicator': indicators,
                'shape': 'circle',
                'splitNumber': 5
            },
            'series': [
                {
                    'type': 'radar',
                    'data': data
                }
            ]
        }
        
        return chart_data
    
    def generate_funnel_chart(self, data: List[Dict[str, Any]], title: str = "漏斗图") -> Dict[str, Any]:
        """
        生成漏斗图数据
        
        Args:
            data: 漏斗数据列表，每个元素包含name和value属性
            title: 图表标题
            
        Returns:
            Dict[str, Any]: 漏斗图配置数据
        """
        chart_data = {
            'type': 'funnel',
            'title': title,
            'series': [
                {
                    'type': 'funnel',
                    'data': data,
                    'sort': 'descending',
                    'itemStyle': {
                        'borderColor': '#fff',
                        'borderWidth': 1
                    }
                }
            ]
        }
        
        return chart_data
    
    def generate_test_statistics_charts(self, total_tests: int, passed: int, failed: int, errors: int, 
                                     suite_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成测试统计相关的图表数据
        
        Args:
            total_tests: 总测试数
            passed: 通过测试数
            failed: 失败测试数
            errors: 错误测试数
            suite_stats: 套件统计数据
            
        Returns:
            Dict[str, Any]: 包含多种图表配置的数据字典
        """
        charts = {}
        
        # 1. 测试状态分布饼图
        status_data = {
            '通过': passed,
            '失败': failed,
            '错误': errors
        }
        charts['status_pie'] = self.generate_pie_chart(status_data, "测试状态分布")
        
        # 2. 套件通过率柱状图
        suite_names = [s['name'] for s in suite_stats]
        pass_rates = []
        
        for s in suite_stats:
            if s['total'] > 0:
                pass_rate = (s['passed'] / s['total']) * 100
            else:
                pass_rate = 0
            pass_rates.append(round(pass_rate, 2))
        
        charts['suite_pass_rate'] = self.generate_bar_chart(
            suite_names, pass_rates, 
            "套件通过率统计", 
            "测试套件", 
            "通过率 (%)"
        )
        
        # 3. 套件执行时间柱状图
        durations = [s['duration'] for s in suite_stats]
        charts['suite_duration'] = self.generate_bar_chart(
            suite_names, durations, 
            "套件执行时间", 
            "测试套件", 
            "执行时间 (秒)"
        )
        
        # 4. 生成总体质量雷达图
        quality_indicators = [
            {'name': '通过率', 'max': 100},
            {'name': '套件完成率', 'max': 100},
            {'name': '错误率', 'max': 100},
            {'name': '失败率', 'max': 100}
        ]
        
        # 计算各项质量指标
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        suite_completion_rate = 100  # 假设所有套件都已执行
        error_rate = (errors / total_tests * 100) if total_tests > 0 else 0
        failure_rate = (failed / total_tests * 100) if total_tests > 0 else 0
        
        quality_data = [
            {
                'name': '测试质量',
                'value': [
                    round(pass_rate, 2),
                    round(suite_completion_rate, 2),
                    round(error_rate, 2),
                    round(failure_rate, 2)
                ],
                'areaStyle': {
                    'color': new_echarts_gradient('#1890ff', '#52c41a', opacity_start=0.3)
                }
            }
        ]
        
        charts['quality_radar'] = self.generate_radar_chart(
            quality_indicators, quality_data, "测试质量分析"
        )
        
        return charts
    
    def generate_trend_charts(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成趋势分析图表
        
        Args:
            historical_data: 历史测试数据列表，包含run_id、timestamp、passed、failed、errors等字段
            
        Returns:
            Dict[str, Any]: 趋势分析图表数据
        """
        if not historical_data:
            return {}
        
        charts = {}
        
        # 排序历史数据
        sorted_data = sorted(historical_data, key=lambda x: x['timestamp'])
        
        # 准备时间序列数据
        timestamps = [str(d['timestamp']) for d in sorted_data]
        
        # 通过率趋势
        pass_rates = []
        for d in sorted_data:
            total = d['passed'] + d['failed'] + d['errors']
            if total > 0:
                pass_rate = (d['passed'] / total) * 100
            else:
                pass_rate = 0
            pass_rates.append(round(pass_rate, 2))
        
        charts['pass_rate_trend'] = self.generate_line_chart(
            timestamps, pass_rates,
            "通过率趋势",
            "时间",
            "通过率 (%)"
        )
        
        # 失败率趋势
        failure_rates = []
        for d in sorted_data:
            total = d['passed'] + d['failed'] + d['errors']
            if total > 0:
                failure_rate = (d['failed'] / total) * 100
            else:
                failure_rate = 0
            failure_rates.append(round(failure_rate, 2))
        
        charts['failure_rate_trend'] = self.generate_line_chart(
            timestamps, failure_rates,
            "失败率趋势",
            "时间",
            "失败率 (%)"
        )
        
        return charts
    
    def export_chart_config(self, chart_data: Dict[str, Any], file_path: str) -> bool:
        """
        导出图表配置到文件
        
        Args:
            chart_data: 图表配置数据
            file_path: 导出文件路径
            
        Returns:
            bool: 是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chart_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"图表配置成功导出到: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出图表配置失败: {str(e)}")
            return False


def new_echarts_gradient(color_start: str, color_end: str, direction: str = 'vertical', 
                        opacity_start: float = 1.0, opacity_end: float = 1.0) -> Dict[str, Any]:
    """
    创建ECharts渐变配置
    
    Args:
        color_start: 起始颜色
        color_end: 结束颜色
        direction: 渐变方向 ('horizontal', 'vertical')
        opacity_start: 起始透明度
        opacity_end: 结束透明度
        
    Returns:
        Dict[str, Any]: ECharts渐变配置
    """
    # 内部实现渐变配置，不依赖外部函数
    if direction == 'horizontal':
        x0, y0, x1, y1 = 0, 0, 1, 0  # 从左到右
    else:  # vertical
        x0, y0, x1, y1 = 0, 0, 0, 1  # 从上到下
    
    return {
        'type': 'linear',
        'x': x0,
        'y': y0,
        'x2': x1,
        'y2': y1,
        'colorStops': [
            {'offset': 0, 'color': color_start, 'opacity': opacity_start},
            {'offset': 1, 'color': color_end, 'opacity': opacity_end}
        ]
    }


def generate_thumbnail(chart_config: Dict[str, Any], width: int = 800, height: int = 600) -> Optional[str]:
    """
    生成图表缩略图（base64格式）
    
    Args:
        chart_config: 图表配置
        width: 缩略图宽度
        height: 缩略图高度
        
    Returns:
        Optional[str]: base64编码的图片数据，失败返回None
    """
    try:
        # 尝试使用matplotlib生成图表
        import matplotlib.pyplot as plt
        import numpy as np
        
        plt.figure(figsize=(width/100, height/100), dpi=100)
        
        if chart_config['type'] == 'pie':
            # 生成饼图
            labels = [item['name'] for item in chart_config['data']]
            sizes = [item['value'] for item in chart_config['data']]
            colors = [item['itemStyle']['color'] for item in chart_config['data']]
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title(chart_config['title'])
            
        elif chart_config['type'] == 'bar':
            # 生成柱状图
            x_data = chart_config['xAxis']['data']
            y_data = chart_config['series'][0]['data']
            
            x_pos = np.arange(len(x_data))
            plt.bar(x_pos, y_data, width=0.6, color='#667eea')
            plt.xlabel(chart_config['xAxis'].get('name', ''))
            plt.ylabel(chart_config['yAxis'].get('name', ''))
            plt.title(chart_config['title'])
            plt.xticks(x_pos, x_data, rotation=45, ha='right')
            
        elif chart_config['type'] == 'line':
            # 生成折线图
            x_data = chart_config['xAxis']['data']
            y_data = chart_config['series'][0]['data']
            
            plt.plot(x_data, y_data, marker='o', linewidth=3, markersize=8, color='#1890ff')
            plt.fill_between(x_data, y_data, alpha=0.3, color='#e6f7ff')
            plt.xlabel(chart_config['xAxis'].get('name', ''))
            plt.ylabel(chart_config['yAxis'].get('name', ''))
            plt.title(chart_config['title'])
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # 保存为base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # 转换为base64
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{img_str}"
    
    except ImportError:
        return None
    except Exception:
        return None