"""
测试用例导入导出示例 - apitestkit框架

此示例展示了如何批量导入测试用例和导出测试结果
"""

import json
import os
from apitestkit.request.http_client import HttpClient
from apitestkit.assertion.response_assertion import ResponseAssertion
from apitestkit.report.report_generator import ReportGenerator
from apitestkit.utils.logger import logger_manager

# 配置日志
logger = logger_manager.get_logger("import_export_example")

def load_test_cases_from_json(file_path):
    """
    从JSON文件加载测试用例
    
    Args:
        file_path: JSON文件路径
    
    Returns:
        list: 测试用例列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        logger.info(f"成功从 {file_path} 加载了 {len(test_cases)} 个测试用例")
        return test_cases
    except Exception as e:
        logger.error(f"加载测试用例文件失败: {str(e)}")
        raise

def save_test_results_to_json(results, file_path):
    """
    保存测试结果到JSON文件
    
    Args:
        results: 测试结果列表
        file_path: 保存路径
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"测试结果已保存到 {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"保存测试结果失败: {str(e)}")
        raise

def run_test_case(test_case):
    """
    执行单个测试用例
    
    Args:
        test_case: 测试用例字典
    
    Returns:
        dict: 测试结果
    """
    test_id = test_case.get("id", "unknown")
    test_name = test_case.get("name", "未命名测试")
    logger.info(f"开始执行测试用例: {test_name} (ID: {test_id})")
    
    # 创建HTTP客户端
    client = HttpClient()
    
    # 准备请求参数
    url = test_case.get("url")
    method = test_case.get("method", "GET").upper()
    headers = test_case.get("headers", {})
    params = test_case.get("params", {})
    body = test_case.get("body")
    
    # 发送请求
    try:
        if method == "GET":
            response = client.get(url=url, headers=headers, params=params)
        elif method == "POST":
            if "Content-Type" in headers and "json" in headers["Content-Type"]:
                response = client.post(url=url, headers=headers, json=body)
            else:
                response = client.post(url=url, headers=headers, data=body)
        elif method == "PUT":
            if "Content-Type" in headers and "json" in headers["Content-Type"]:
                response = client.put(url=url, headers=headers, json=body)
            else:
                response = client.put(url=url, headers=headers, data=body)
        elif method == "DELETE":
            response = client.delete(url=url, headers=headers, params=params)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        # 执行断言
        assertion = ResponseAssertion(response)
        test_result = {
            "test_id": test_id,
            "test_name": test_name,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds() * 1000,
            "assertions": [],
            "status": "passed"
        }
        
        # 执行预期的断言
        expected_status = test_case.get("expected_status", 200)
        try:
            assertion.assert_status_code(expected_status)
            test_result["assertions"].append({
                "type": "status_code",
                "expected": expected_status,
                "actual": response.status_code,
                "result": "passed"
            })
        except AssertionError as e:
            test_result["assertions"].append({
                "type": "status_code",
                "expected": expected_status,
                "actual": response.status_code,
                "result": "failed",
                "error": str(e)
            })
            test_result["status"] = "failed"
        
        # 执行JSON路径断言
        json_path_assertions = test_case.get("json_path_assertions", [])
        for json_assertion in json_path_assertions:
            path = json_assertion.get("path")
            expected_value = json_assertion.get("value")
            try:
                assertion.assert_json_path(path, expected_value)
                test_result["assertions"].append({
                    "type": "json_path",
                    "path": path,
                    "expected": expected_value,
                    "result": "passed"
                })
            except AssertionError as e:
                test_result["assertions"].append({
                    "type": "json_path",
                    "path": path,
                    "expected": expected_value,
                    "result": "failed",
                    "error": str(e)
                })
                test_result["status"] = "failed"
        
        logger.info(f"测试用例 {test_name} 执行完成: {test_result['status']}")
        return test_result
        
    except Exception as e:
        logger.error(f"测试用例 {test_name} 执行异常: {str(e)}")
        return {
            "test_id": test_id,
            "test_name": test_name,
            "status": "error",
            "error": str(e)
        }

def batch_run_test_cases(test_cases):
    """
    批量执行测试用例
    
    Args:
        test_cases: 测试用例列表
    
    Returns:
        list: 测试结果列表
    """
    results = []
    logger.info(f"开始批量执行 {len(test_cases)} 个测试用例")
    
    for test_case in test_cases:
        result = run_test_case(test_case)
        results.append(result)
    
    # 统计结果
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    error = sum(1 for r in results if r["status"] == "error")
    
    logger.info(f"批量执行完成: 总 {len(results)} 个, 通过 {passed} 个, 失败 {failed} 个, 错误 {error} 个")
    
    return results

def export_test_report(results, output_dir="reports"):
    """
    导出测试报告
    
    Args:
        results: 测试结果列表
        output_dir: 输出目录
    
    Returns:
        dict: 报告路径信息
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成报告数据
    report_data = {
        "test_suite": "批量API测试套件",
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "passed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "error": sum(1 for r in results if r["status"] == "error")
        },
        "environment": {
            "framework": "apitestkit",
            "version": "1.0.0"
        }
    }
    
    # 生成报告
    report = ReportGenerator()
    html_path = os.path.join(output_dir, "batch_test_report.html")
    json_path = os.path.join(output_dir, "batch_test_report.json")
    
    html_report = report.generate_html_report(report_data, html_path)
    json_report = report.generate_json_report(report_data, json_path)
    
    logger.info(f"测试报告已生成: HTML={html_report}, JSON={json_report}")
    
    return {
        "html_report": html_report,
        "json_report": json_report
    }

def main():
    """
    主函数 - 演示导入导出流程
    """
    try:
        # 示例测试用例数据
        sample_test_cases = [
            {
                "id": "TC001",
                "name": "获取用户信息",
                "description": "测试获取单个用户信息接口",
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/users/1",
                "headers": {"Content-Type": "application/json"},
                "expected_status": 200,
                "json_path_assertions": [
                    {"path": "$.id", "value": 1},
                    {"path": "$.name", "value": "Leanne Graham"}
                ]
            },
            {
                "id": "TC002",
                "name": "创建帖子",
                "description": "测试创建新帖子接口",
                "method": "POST",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "title": "测试标题",
                    "body": "测试内容",
                    "userId": 1
                },
                "expected_status": 201,
                "json_path_assertions": [
                    {"path": "$.title", "value": "测试标题"},
                    {"path": "$.userId", "value": 1}
                ]
            }
        ]
        
        # 保存示例测试用例到文件
        test_cases_file = "sample_test_cases.json"
        with open(test_cases_file, 'w', encoding='utf-8') as f:
            json.dump(sample_test_cases, f, indent=2, ensure_ascii=False)
        logger.info(f"示例测试用例已保存到 {test_cases_file}")
        
        # 加载测试用例
        test_cases = load_test_cases_from_json(test_cases_file)
        
        # 批量执行测试
        results = batch_run_test_cases(test_cases)
        
        # 保存测试结果
        save_test_results_to_json(results, "test_results.json")
        
        # 生成报告
        export_test_report(results)
        
        logger.info("导入导出流程完成")
        
    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()