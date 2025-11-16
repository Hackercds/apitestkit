"""
数据存储管理模块

提供API测试数据的存储、检索、过滤和导出功能，支持批量请求数据的高效管理。
"""

import json
import csv
import os
import pickle
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path

from apitestkit.core.logger import logger_manager
from apitestkit.core.config import config_manager


class DataStorageManager:
    """
    数据存储管理器类
    
    负责API测试数据的存储、检索、过滤和导出，支持多种存储格式和查询方式。
    """
    
    def __init__(self):
        """
        初始化数据存储管理器
        """
        self._data_store = []
        self._storage_dir = Path(config_manager.get('data_dir', 'data'))
        self._storage_dir.mkdir(exist_ok=True, parents=True)
        self._db_path = self._storage_dir / 'apitestkit.db'
        self._init_database()
        logger_manager.info(f"[框架] 数据存储管理器初始化完成，存储目录: {self._storage_dir}")
    
    def _init_database(self):
        """
        初始化SQLite数据库
        """
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    request_url TEXT,
                    request_method TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    response_data TEXT,
                    request_params TEXT,
                    request_headers TEXT,
                    tags TEXT,
                    metadata TEXT
                )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON api_responses(request_url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON api_responses(status_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_method ON api_responses(request_method)')
                conn.commit()
        except Exception as e:
            logger_manager.error(f"[框架] 初始化数据库失败: {str(e)}")
    
    def store_response(self, response: Any, request_info: Dict[str, Any], 
                      tags: Optional[List[str]] = None, 
                      metadata: Optional[Dict[str, Any]] = None):
        """
        存储API响应数据
        
        Args:
            response: API响应对象或响应数据
            request_info: 请求信息字典，包含url、method、params、headers等
            tags: 数据标签列表，用于分类和检索
            metadata: 附加元数据
            
        Returns:
            int: 存储记录的ID
        """
        try:
            # 准备响应数据
            if hasattr(response, 'json'):
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
            else:
                response_data = response
            
            # 构建存储记录
            record = {
                'timestamp': datetime.now().isoformat(),
                'request_url': request_info.get('url', ''),
                'request_method': request_info.get('method', ''),
                'status_code': getattr(response, 'status_code', None) or request_info.get('status_code'),
                'response_time': request_info.get('response_time', 0),
                'response_data': json.dumps(response_data) if isinstance(response_data, (dict, list)) else str(response_data),
                'request_params': json.dumps(request_info.get('params', {})) if isinstance(request_info.get('params'), dict) else str(request_info.get('params', '')),
                'request_headers': json.dumps(request_info.get('headers', {})) if isinstance(request_info.get('headers'), dict) else str(request_info.get('headers', '')),
                'tags': json.dumps(tags) if tags else '[]',
                'metadata': json.dumps(metadata) if metadata else '{}'
            }
            
            # 内存存储
            record_id = len(self._data_store) + 1
            record['id'] = record_id
            self._data_store.append(record)
            
            # 数据库存储
            try:
                with sqlite3.connect(str(self._db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        '''INSERT INTO api_responses (timestamp, request_url, request_method, status_code, 
                        response_time, response_data, request_params, request_headers, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (record['timestamp'], record['request_url'], record['request_method'], record['status_code'],
                         record['response_time'], record['response_data'], record['request_params'],
                         record['request_headers'], record['tags'], record['metadata'])
                    )
                    conn.commit()
            except Exception as e:
                logger_manager.error(f"[框架] 数据库存储失败: {str(e)}")
            
            logger_manager.debug(f"[框架] 响应数据存储成功，记录ID: {record_id}")
            return record_id
        except Exception as e:
            logger_manager.error(f"[框架] 存储响应数据失败: {str(e)}")
            return -1
    
    def filter_data(self, 
                   condition: Optional[Callable] = None,
                   url_pattern: Optional[str] = None,
                   status_codes: Optional[List[int]] = None,
                   methods: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None,
                   min_response_time: Optional[float] = None,
                   max_response_time: Optional[float] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        根据条件过滤数据
        
        Args:
            condition: 自定义过滤函数
            url_pattern: URL模式匹配
            status_codes: 状态码列表
            methods: HTTP方法列表
            tags: 标签列表
            min_response_time: 最小响应时间
            max_response_time: 最大响应时间
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 过滤后的数据列表
        """
        try:
            # 从内存中获取数据
            filtered_data = []
            
            for record in self._data_store:
                # 应用各种过滤条件
                match = True
                
                if url_pattern and url_pattern not in record['request_url']:
                    match = False
                
                if status_codes and record['status_code'] not in status_codes:
                    match = False
                
                if methods and record['request_method'].upper() not in [m.upper() for m in methods]:
                    match = False
                
                if tags:
                    record_tags = json.loads(record['tags'])
                    if not any(tag in record_tags for tag in tags):
                        match = False
                
                if min_response_time is not None and record['response_time'] < min_response_time:
                    match = False
                
                if max_response_time is not None and record['response_time'] > max_response_time:
                    match = False
                
                if condition and not condition(record):
                    match = False
                
                if match:
                    filtered_data.append(record)
            
            # 限制返回数量
            if limit:
                filtered_data = filtered_data[:limit]
            
            logger_manager.debug(f"[框架] 数据过滤完成，返回 {len(filtered_data)} 条记录")
            return filtered_data
        except Exception as e:
            logger_manager.error(f"[框架] 数据过滤失败: {str(e)}")
            return []
    
    def export_to_json(self, filename: str = None, filter_condition: Optional[Callable] = None) -> str:
        """
        导出数据到JSON文件
        
        Args:
            filename: 导出文件名，不提供则自动生成
            filter_condition: 导出前的数据过滤条件
            
        Returns:
            str: 导出文件的路径
        """
        try:
            # 确定文件名
            if not filename:
                filename = f"api_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # 构建文件路径
            file_path = self._storage_dir / filename
            
            # 获取要导出的数据
            data_to_export = self.filter_data(condition=filter_condition) if filter_condition else self._data_store
            
            # 导出到JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_export, f, ensure_ascii=False, indent=2)
            
            logger_manager.info(f"[框架] 数据成功导出到JSON文件: {file_path}")
            return str(file_path)
        except Exception as e:
            logger_manager.error(f"[框架] 导出JSON失败: {str(e)}")
            return ''
    
    def export_to_csv(self, filename: str = None, filter_condition: Optional[Callable] = None) -> str:
        """
        导出数据到CSV文件
        
        Args:
            filename: 导出文件名，不提供则自动生成
            filter_condition: 导出前的数据过滤条件
            
        Returns:
            str: 导出文件的路径
        """
        try:
            # 确定文件名
            if not filename:
                filename = f"api_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 构建文件路径
            file_path = self._storage_dir / filename
            
            # 获取要导出的数据
            data_to_export = self.filter_data(condition=filter_condition) if filter_condition else self._data_store
            
            if not data_to_export:
                return ''
            
            # CSV字段名
            fieldnames = ['id', 'timestamp', 'request_url', 'request_method', 'status_code', 
                         'response_time', 'response_data', 'tags', 'metadata']
            
            # 导出到CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in data_to_export:
                    # 简化导出数据，避免JSON字段过长
                    writer.writerow({
                        'id': record.get('id', ''),
                        'timestamp': record.get('timestamp', ''),
                        'request_url': record.get('request_url', ''),
                        'request_method': record.get('request_method', ''),
                        'status_code': record.get('status_code', ''),
                        'response_time': record.get('response_time', ''),
                        'response_data': json.dumps(record.get('response_data', '')[:100]) + '...' if isinstance(record.get('response_data', ''), str) and len(record.get('response_data', '')) > 100 else json.dumps(record.get('response_data', '')),
                        'tags': record.get('tags', '[]'),
                        'metadata': record.get('metadata', '{}')
                    })
            
            logger_manager.info(f"[框架] 数据成功导出到CSV文件: {file_path}")
            return str(file_path)
        except Exception as e:
            logger_manager.error(f"[框架] 导出CSV失败: {str(e)}")
            return ''
    
    def clear_memory_data(self):
        """
        清空内存中的数据存储
        """
        self._data_store.clear()
        logger_manager.info(f"[框架] 内存数据存储已清空")
    
    def get_record_count(self) -> int:
        """
        获取当前存储的记录数
        
        Returns:
            int: 记录数量
        """
        return len(self._data_store)
    
    def find_records_by_content(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据内容关键字查找记录
        
        Args:
            keyword: 要查找的关键字
            
        Returns:
            List[Dict[str, Any]]: 匹配的记录列表
        """
        try:
            matching_records = []
            for record in self._data_store:
                # 在响应数据和请求参数中查找
                if (keyword in str(record.get('response_data', '')) or 
                    keyword in str(record.get('request_params', '')) or
                    keyword in str(record.get('request_url', ''))):
                    matching_records.append(record)
            
            logger_manager.debug(f"[框架] 关键字搜索完成，找到 {len(matching_records)} 条匹配记录")
            return matching_records
        except Exception as e:
            logger_manager.error(f"[框架] 内容搜索失败: {str(e)}")
            return []
    
    def batch_process(self, records: List[Dict[str, Any]], processor: Callable) -> List[Any]:
        """
        批量处理记录
        
        Args:
            records: 要处理的记录列表
            processor: 处理函数
            
        Returns:
            List[Any]: 处理结果列表
        """
        try:
            results = []
            for record in records:
                try:
                    result = processor(record)
                    results.append(result)
                except Exception as e:
                    logger_manager.error(f"[框架] 处理记录 {record.get('id')} 失败: {str(e)}")
                    results.append(None)
            
            logger_manager.info(f"[框架] 批量处理完成，处理了 {len(records)} 条记录")
            return results
        except Exception as e:
            logger_manager.error(f"[框架] 批量处理失败: {str(e)}")
            return []


# 创建全局数据存储管理器实例
data_storage_manager = DataStorageManager()


def get_data_storage():
    """
    获取数据存储管理器实例
    
    Returns:
        DataStorageManager: 数据存储管理器实例
    """
    return data_storage_manager