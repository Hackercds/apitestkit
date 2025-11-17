"""
指标收集器模块

负责收集和存储性能测试过程中的各项指标数据，如响应时间、状态码、错误率等。
"""

import time
from typing import Dict, List, Optional, Any
from collections import defaultdict

from apitestkit.core.logger import logger_manager

class MetricsCollector:
    """
    性能测试指标收集器
    
    收集和存储性能测试过程中的各项指标数据。
    """
    
    def __init__(self):
        """
        初始化指标收集器
        """
        self._start_time = time.time()
        self._end_time = None
        self._requests = []  # 存储所有请求的详细信息
        self._metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'status_codes': defaultdict(int),
            'errors': defaultdict(int),
            'time_series': [],  # 时间序列数据
            'transaction_metrics': defaultdict(lambda: {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'response_times': []
            }),  # 事务级指标
            'concurrent_users': 0,  # 最大并发用户数
            'throughput_data': [],  # 吞吐量数据点
            'resource_usage': {
                'cpu_usage': [],  # CPU使用率
                'memory_usage': []  # 内存使用率
            },
            'latency_breakdown': defaultdict(list),  # 延迟分布
            'connection_metrics': {
                'total_connections': 0,
                'failed_connections': 0,
                'connection_errors': defaultdict(int)
            }
        }
        self._lock = None  # 线程锁，需要时创建
        self._test_config = None  # 测试配置信息
        self._last_per_second_data = defaultdict(int)  # 每秒数据计数
    
    def record_request(self, 
                      start_time: float, 
                      end_time: float, 
                      response_time: float, 
                      status_code: Optional[int] = None,
                      success: bool = True,
                      error: Optional[str] = None,
                      additional_data: Optional[Dict[str, Any]] = None,
                      latency_breakdown: Optional[Dict[str, float]] = None,
                      connection_info: Optional[Dict[str, Any]] = None):
        """
        记录单个请求的指标
        
        Args:
            start_time: 请求开始时间戳
            end_time: 请求结束时间戳
            response_time: 响应时间(毫秒)
            status_code: HTTP状态码
            success: 请求是否成功
            error: 错误信息
            additional_data: 额外的数据
            latency_breakdown: 延迟分布详情（dns, connect, tls, request, response等）
            connection_info: 连接相关信息
        """
        # 如果是首次记录请求，创建线程锁
        if not self._lock:
            import threading
            self._lock = threading.Lock()
        
        # 创建请求记录
        request_record = {
            'start_time': start_time,
            'end_time': end_time,
            'response_time': response_time,
            'status_code': status_code,
            'success': success,
            'error': error,
            'additional_data': additional_data or {},
            'latency_breakdown': latency_breakdown or {},
            'connection_info': connection_info or {}
        }
        
        # 线程安全地更新指标
        with self._lock:
            self._requests.append(request_record)
            self._metrics['total_requests'] += 1
            
            # 如果有事务信息，记录事务级指标
            if additional_data and 'transaction_name' in additional_data:
                transaction_name = additional_data['transaction_name']
                tx_metrics = self._metrics['transaction_metrics'][transaction_name]
                tx_metrics['total_requests'] += 1
                
                if success:
                    tx_metrics['successful_requests'] += 1
                    tx_metrics['response_times'].append(response_time)
                else:
                    tx_metrics['failed_requests'] += 1
            
            if success:
                self._metrics['successful_requests'] += 1
                self._metrics['response_times'].append(response_time)
                if status_code:
                    self._metrics['status_codes'][status_code] += 1
            else:
                self._metrics['failed_requests'] += 1
                if error:
                    # 简化错误信息，避免过多不同的错误键
                    error_key = self._simplify_error(error)
                    self._metrics['errors'][error_key] += 1
            
            # 记录延迟分布
            if latency_breakdown:
                for latency_type, latency_value in latency_breakdown.items():
                    self._metrics['latency_breakdown'][latency_type].append(latency_value)
            
            # 记录连接指标
            if connection_info:
                self._metrics['connection_metrics']['total_connections'] += 1
                if not success and 'connection_error' in connection_info:
                    self._metrics['connection_metrics']['failed_connections'] += 1
                    conn_error = connection_info['connection_error']
                    self._metrics['connection_metrics']['connection_errors'][conn_error] += 1
            
            # 记录时间序列数据（每秒汇总）
            timestamp = int(start_time)
            self._record_time_series_data(timestamp, success, response_time, status_code)
            
            # 记录吞吐量数据点
            self._metrics['throughput_data'].append({
                'timestamp': start_time,
                'response_time': response_time,
                'success': success
            })
            
            # 更新每秒计数
            second_key = int(start_time)
            if success:
                self._last_per_second_data[('success', second_key)] += 1
            else:
                self._last_per_second_data[('failed', second_key)] += 1
    
    def _record_time_series_data(self, timestamp: int, success: bool, response_time: float, status_code: Optional[int] = None):
        """
        记录时间序列数据
        
        Args:
            timestamp: 时间戳（秒）
            success: 请求是否成功
            response_time: 响应时间
            status_code: HTTP状态码
        """
        # 查找或创建当前时间戳的记录
        existing_record = None
        for record in reversed(self._metrics['time_series']):
            if record['timestamp'] == timestamp:
                existing_record = record
                break
        
        if existing_record:
            # 更新现有记录
            existing_record['total_requests'] += 1
            if success:
                existing_record['successful_requests'] += 1
                existing_record['response_times'].append(response_time)
            else:
                existing_record['failed_requests'] += 1
        else:
            # 创建新记录
            new_record = {
                'timestamp': timestamp,
                'total_requests': 1,
                'successful_requests': 1 if success else 0,
                'failed_requests': 0 if success else 1,
                'response_times': [response_time] if success else []
            }
            self._metrics['time_series'].append(new_record)
    
    def _simplify_error(self, error: str) -> str:
        """
        简化错误信息，提取关键部分
        
        Args:
            error: 原始错误信息
            
        Returns:
            str: 简化后的错误信息
        """
        # 常见错误模式
        error_patterns = [
            ('timeout', '请求超时'),
            ('Connection refused', '连接被拒绝'),
            ('Connection reset', '连接重置'),
            ('Name or service not known', '域名解析失败'),
            ('no route to host', '无法路由到主机'),
            ('ssl', 'SSL错误'),
            ('certificate', '证书错误'),
            ('400', '400错误请求'),
            ('401', '401未授权'),
            ('403', '403禁止访问'),
            ('404', '404未找到'),
            ('500', '500服务器错误'),
            ('502', '502错误网关'),
            ('503', '503服务不可用'),
            ('504', '504网关超时'),
        ]
        
        error_lower = error.lower()
        for pattern, simplified in error_patterns:
            if pattern in error_lower:
                return simplified
        
        # 如果没有匹配的模式，返回前50个字符
        return error[:50] + ('...' if len(error) > 50 else '')
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        获取汇总指标
        
        Returns:
            Dict[str, Any]: 汇总指标
        """
        # 计算测试持续时间
        test_duration = self._calculate_test_duration()
        
        # 计算吞吐量（每秒请求数）
        total_requests = self._metrics['total_requests']
        successful_requests = self._metrics['successful_requests']
        failed_requests = self._metrics['failed_requests']
        
        if test_duration > 0:
            rps = total_requests / test_duration
            successful_rps = successful_requests / test_duration
            failed_rps = failed_requests / test_duration
        else:
            rps = successful_rps = failed_rps = 0
        
        # 计算响应时间统计
        response_times = self._metrics['response_times']
        response_times.sort()
        
        if response_times:
            count = len(response_times)
            avg_response_time = sum(response_times) / count
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # 计算百分位数
            p50 = self._calculate_percentile(response_times, 50)
            p90 = self._calculate_percentile(response_times, 90)
            p95 = self._calculate_percentile(response_times, 95)
            p99 = self._calculate_percentile(response_times, 99)
            p999 = self._calculate_percentile(response_times, 99.9)  # 添加99.9%百分位
            
            # 计算标准差
            mean = avg_response_time
            variance = sum((x - mean) ** 2 for x in response_times) / count
            std_dev = variance ** 0.5
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50 = p90 = p95 = p99 = p999 = 0
            std_dev = 0
        
        # 计算成功率
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # 计算吞吐量波动
        throughput_variation = self._calculate_throughput_variation()
        
        # 按秒计算吞吐量数据，用于后续计算最大值、最小值等
        second_data = defaultdict(int)
        success_second_data = defaultdict(int)
        failed_second_data = defaultdict(int)
        
        for data_point in self._metrics['throughput_data']:
            second_key = int(data_point['timestamp'])
            second_data[second_key] += 1
            if data_point['success']:
                success_second_data[second_key] += 1
            else:
                failed_second_data[second_key] += 1
        
        # 计算吞吐量的最大值、最小值、平均值和峰值
        if second_data:
            rps_values = list(second_data.values())
            max_rps = max(rps_values)
            min_rps = min(rps_values)
            avg_second_rps = sum(rps_values) / len(rps_values)
            
            # 计算95%峰值RPS
            rps_values.sort()
            p95_rps = self._calculate_percentile(rps_values, 95)
        else:
            max_rps = min_rps = avg_second_rps = p95_rps = 0
        
        # 计算成功和失败请求的RPS统计
        if success_second_data:
            success_rps_values = list(success_second_data.values())
            max_success_rps = max(success_rps_values)
            avg_success_rps = sum(success_rps_values) / len(success_rps_values)
        else:
            max_success_rps = avg_success_rps = 0
        
        if failed_second_data:
            failed_rps_values = list(failed_second_data.values())
            max_failed_rps = max(failed_rps_values)
            avg_failed_rps = sum(failed_rps_values) / len(failed_rps_values)
        else:
            max_failed_rps = avg_failed_rps = 0
        
        # 获取最大并发用户数
        max_concurrent_users = self._metrics['concurrent_users']
        
        # 计算延迟分布统计
        latency_stats = {}
        for latency_type, latencies in self._metrics['latency_breakdown'].items():
            if latencies:
                latency_stats[latency_type] = {
                    'avg': sum(latencies) / len(latencies),
                    'min': min(latencies),
                    'max': max(latencies),
                    'p50': self._calculate_percentile(sorted(latencies), 50),
                    'p95': self._calculate_percentile(sorted(latencies), 95),
                    'count': len(latencies)
                }
            else:
                latency_stats[latency_type] = {
                    'avg': 0,
                    'min': 0,
                    'max': 0,
                    'p50': 0,
                    'p95': 0,
                    'count': 0
                }
        
        # 连接指标
        connection_metrics = {
            'total_connections': self._metrics['connection_metrics']['total_connections'],
            'failed_connections': self._metrics['connection_metrics']['failed_connections'],
            'connection_success_rate': (
                (1 - self._metrics['connection_metrics']['failed_connections'] / 
                self._metrics['connection_metrics']['total_connections']) * 100 
                if self._metrics['connection_metrics']['total_connections'] > 0 else 100
            ),
            'connection_errors': dict(self._metrics['connection_metrics']['connection_errors'])
        }
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': success_rate,
            'test_duration': test_duration,
            
            # RPS指标
            'rps': rps,  # 平均每秒请求数
            'successful_rps': successful_rps,  # 成功请求的平均RPS
            'failed_rps': failed_rps,  # 失败请求的平均RPS
            'max_rps': max_rps,  # 最大RPS
            'min_rps': min_rps,  # 最小RPS
            'avg_second_rps': avg_second_rps,  # 每秒平均RPS
            'p95_rps': p95_rps,  # 95%峰值RPS
            'max_success_rps': max_success_rps,  # 最大成功RPS
            'avg_success_rps': avg_success_rps,  # 平均成功RPS
            'max_failed_rps': max_failed_rps,  # 最大失败RPS
            'avg_failed_rps': avg_failed_rps,  # 平均失败RPS
            'throughput_variation': throughput_variation,  # 吞吐量波动
            
            # 响应时间指标
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'p50_response_time': p50,
            'p90_response_time': p90,
            'p95_response_time': p95,
            'p99_response_time': p99,
            'p999_response_time': p999,  # 99.9%响应时间
            'response_time_std_dev': std_dev,  # 响应时间标准差
            
            # 并发指标
            'max_concurrent_users': max_concurrent_users,
            
            # 延迟分布统计
            'latency_stats': latency_stats,
            
            # 连接指标
            'connection_metrics': connection_metrics,
            
            # 保留原有返回的状态码和错误分布
            'status_codes_distribution': dict(self._metrics['status_codes']),
            'errors_distribution': dict(self._metrics['errors'])
        }
    
    def _calculate_test_duration(self) -> float:
        """
        计算测试持续时间
        
        Returns:
            float: 持续时间(秒)
        """
        if not self._requests:
            return 0.0
        
        if self._end_time:
            return self._end_time - self._start_time
        
        # 根据请求的时间计算
        first_request_time = min(r['start_time'] for r in self._requests)
        last_request_time = max(r['end_time'] for r in self._requests)
        
        return last_request_time - first_request_time
    
    def _calculate_percentile(self, sorted_list: List[float], percentile: int) -> float:
        """
        计算百分位数
        
        Args:
            sorted_list: 已排序的列表
            percentile: 百分位数(0-100)
            
        Returns:
            float: 百分位数值
        """
        if not sorted_list:
            return 0.0
        
        index = int(len(sorted_list) * percentile / 100)
        if index >= len(sorted_list):
            index = len(sorted_list) - 1
        
        return sorted_list[index]
    
    def get_time_series_metrics(self, interval: int = 1) -> List[Dict[str, Any]]:
        """
        获取时间序列指标
        
        Args:
            interval: 时间间隔(秒)
            
        Returns:
            List[Dict[str, Any]]: 时间序列指标列表
        """
        if not self._metrics['time_series']:
            return []
        
        # 确保时间序列按时间戳排序
        sorted_time_series = sorted(self._metrics['time_series'], key=lambda x: x['timestamp'])
        
        # 计算每个时间点的统计数据
        result = []
        for record in sorted_time_series:
            ts_record = {
                'timestamp': record['timestamp'],
                'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record['timestamp'])),
                'total_requests': record['total_requests'],
                'successful_requests': record['successful_requests'],
                'failed_requests': record['failed_requests'],
                'success_rate': (record['successful_requests'] / record['total_requests'] * 100) if record['total_requests'] > 0 else 0.0,
                'rps': record['total_requests'] / interval,
                'tps': record['total_requests'] / interval,
                'qps': record['total_requests'] / interval,
                'successful_rps': record['successful_requests'] / interval if record['total_requests'] > 0 else 0.0,
                'failed_rps': record['failed_requests'] / interval if record['total_requests'] > 0 else 0.0
            }
            
            # 添加响应时间统计
            if record['response_times']:
                ts_record['avg_response_time'] = sum(record['response_times']) / len(record['response_times'])
                ts_record['min_response_time'] = min(record['response_times'])
                ts_record['max_response_time'] = max(record['response_times'])
            else:
                ts_record['avg_response_time'] = 0.0
                ts_record['min_response_time'] = 0.0
                ts_record['max_response_time'] = 0.0
            
            result.append(ts_record)
        
        return result
    
    def get_requests_summary(self) -> Dict[str, Any]:
        """
        获取请求汇总信息
        
        Returns:
            Dict[str, Any]: 请求汇总信息
        """
        return {
            'total_requests': self._metrics['total_requests'],
            'successful_requests': self._metrics['successful_requests'],
            'failed_requests': self._metrics['failed_requests'],
            'success_rate': (self._metrics['successful_requests'] / self._metrics['total_requests'] * 100) if self._metrics['total_requests'] > 0 else 0.0
        }
    
    def get_response_time_distribution(self, buckets: int = 10) -> Dict[str, List[Any]]:
        """
        获取响应时间分布
        
        Args:
            buckets: 分桶数量
            
        Returns:
            Dict[str, List[Any]]: 响应时间分布
        """
        response_times = self._metrics['response_times']
        
        if not response_times:
            return {'buckets': [], 'counts': []}
        
        min_rt = min(response_times)
        max_rt = max(response_times)
        range_rt = max_rt - min_rt
        
        if range_rt == 0:
            # 所有响应时间相同
            return {
                'buckets': [f"{min_rt}"],
                'counts': [len(response_times)]
            }
        
        bucket_size = range_rt / buckets
        bucket_ranges = [(min_rt + i * bucket_size, min_rt + (i + 1) * bucket_size) for i in range(buckets)]
        bucket_counts = [0] * buckets
        
        for rt in response_times:
            # 找到响应时间所在的桶
            for i, (start, end) in enumerate(bucket_ranges):
                if start <= rt < end or (i == buckets - 1 and rt <= end):
                    bucket_counts[i] += 1
                    break
        
        # 格式化桶标签
        bucket_labels = [f"{start:.2f}-{end:.2f}" for start, end in bucket_ranges]
        
        return {
            'buckets': bucket_labels,
            'counts': bucket_counts
        }
    
    def get_status_code_distribution(self) -> Dict[int, int]:
        """
        获取状态码分布
        
        Returns:
            Dict[int, int]: 状态码分布
        """
        return dict(self._metrics['status_codes'])
    
    def get_error_distribution(self) -> Dict[str, int]:
        """
        获取错误分布
        
        Returns:
            Dict[str, int]: 错误分布
        """
        return dict(self._metrics['errors'])
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标数据
        
        Returns:
            Dict[str, Any]: 所有指标
        """
        return {
            'summary': self.get_summary_metrics(),
            'requests_info': self.get_requests_summary(),
            'time_series': self.get_time_series_metrics(),
            'response_time_distribution': self.get_response_time_distribution(),
            'status_code_distribution': self.get_status_code_distribution(),
            'error_distribution': self.get_error_distribution(),
            'test_duration': self._calculate_test_duration(),
            'transaction_metrics': self._get_transaction_metrics()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标数据（get_all_metrics的别名）
        
        Returns:
            Dict[str, Any]: 所有指标
        """
        return self.get_all_metrics()
    
    def reset(self):
        """
        重置指标收集器
        """
        self._start_time = time.time()
        self._end_time = None
        self._requests = []
        self._metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'status_codes': defaultdict(int),
            'errors': defaultdict(int),
            'time_series': [],
            'transaction_metrics': defaultdict(lambda: {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'response_times': []
            }),
            'concurrent_users': 0,
            'throughput_data': [],
            'resource_usage': {
                'cpu_usage': [],
                'memory_usage': []
            },
            'latency_breakdown': defaultdict(list),
            'connection_metrics': {
                'total_connections': 0,
                'failed_connections': 0,
                'connection_errors': defaultdict(int)
            }
        }
        self._test_config = None
        self._last_per_second_data = defaultdict(int)
    
    def set_test_config(self, config: Dict[str, Any]):
        """
        设置测试配置信息
        
        Args:
            config: 测试配置字典
        """
        self._test_config = config
    
    def update_concurrent_users(self, current_users: int):
        """
        更新当前并发用户数
        
        Args:
            current_users: 当前并发用户数
        """
        if not self._lock:
            import threading
            self._lock = threading.Lock()
        
        with self._lock:
            if current_users > self._metrics['concurrent_users']:
                self._metrics['concurrent_users'] = current_users
    
    def _calculate_throughput_variation(self) -> float:
        """
        计算吞吐量波动
        
        Returns:
            float: 吞吐量标准差
        """
        if len(self._metrics['throughput_data']) < 2:
            return 0.0
        
        # 按秒聚合数据
        second_data = defaultdict(int)
        for data_point in self._metrics['throughput_data']:
            second_key = int(data_point['timestamp'])
            second_data[second_key] += 1
        
        # 计算标准差
        counts = list(second_data.values())
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        return variance ** 0.5
    
    def _get_transaction_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取事务级别的指标
        
        Returns:
            Dict[str, Dict[str, Any]]: 事务指标
        """
        transaction_metrics = {}
        
        for tx_name, tx_data in self._metrics['transaction_metrics'].items():
            response_times = tx_data['response_times']
            
            if response_times:
                response_times.sort()
                count = len(response_times)
                
                tx_metrics = {
                    'total_requests': tx_data['total_requests'],
                    'successful_requests': tx_data['successful_requests'],
                    'failed_requests': tx_data['failed_requests'],
                    'success_rate': (tx_data['successful_requests'] / tx_data['total_requests'] * 100) if tx_data['total_requests'] > 0 else 0.0,
                    'avg_response_time': sum(response_times) / count,
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'p50_response_time': self._calculate_percentile(response_times, 50),
                    'p90_response_time': self._calculate_percentile(response_times, 90),
                    'p95_response_time': self._calculate_percentile(response_times, 95),
                    'p99_response_time': self._calculate_percentile(response_times, 99)
                }
            else:
                tx_metrics = {
                    'total_requests': tx_data['total_requests'],
                    'successful_requests': tx_data['successful_requests'],
                    'failed_requests': tx_data['failed_requests'],
                    'success_rate': 0.0,
                    'avg_response_time': 0.0,
                    'min_response_time': 0.0,
                    'max_response_time': 0.0,
                    'p50_response_time': 0.0,
                    'p90_response_time': 0.0,
                    'p95_response_time': 0.0,
                    'p99_response_time': 0.0
                }
            
            transaction_metrics[tx_name] = tx_metrics
        
        return transaction_metrics
    
    def finalize(self):
        """
        完成指标收集，设置结束时间
        """
        self._end_time = time.time()
        logger_manager.info(f"[指标收集器] 已收集 {self._metrics['total_requests']} 个请求的指标数据")