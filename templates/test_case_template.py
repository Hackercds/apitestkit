"""
测试用例模板 - apitestkit框架

此模板展示了如何使用apitestkit框架创建API测试用例
"""

from apitestkit.request.http_client import HttpClient
from apitestkit.assertion.response_assertion import ResponseAssertion
from apitestkit.report.report_generator import ReportGenerator
from apitestkit.core.config import ConfigManager
from apitestkit.utils.logger import logger_manager

# 配置日志
logger = logger_manager.get_logger("example_test")

# 加载配置
config = ConfigManager()
config.load_config("config.json")

def test_get_request_example():
    """
    GET请求示例测试
    """
    # 创建HTTP客户端实例
    client = HttpClient()
    
    # 设置请求参数
    url = "https://jsonplaceholder.typicode.com/posts/1"
    headers = {"Content-Type": "application/json"}
    params = {"userId": 1}
    
    try:
        # 发送GET请求
        logger.info(f"发送GET请求到: {url}")
        response = client.get(url=url, headers=headers, params=params)
        
        # 创建断言实例
        assertion = ResponseAssertion(response)
        
        # 执行断言
        assertion.assert_status_code(200)
        assertion.assert_response_time(2000)  # 响应时间小于2000ms
        assertion.assert_json_path("$.id", 1)
        assertion.assert_json_path_not_empty("$.title")
        assertion.assert_contains("title")
        
        logger.info("GET请求测试通过")
        return {
            "status": "passed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "status_code": response.status_code
        }
    except Exception as e:
        logger.error(f"GET请求测试失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

def test_post_request_example():
    """
    POST请求示例测试
    """
    # 创建HTTP客户端实例
    client = HttpClient()
    
    # 设置请求参数
    url = "https://jsonplaceholder.typicode.com/posts"
    headers = {"Content-Type": "application/json"}
    data = {
        "title": "foo",
        "body": "bar",
        "userId": 1
    }
    
    try:
        # 发送POST请求
        logger.info(f"发送POST请求到: {url}")
        response = client.post(url=url, headers=headers, json=data)
        
        # 创建断言实例
        assertion = ResponseAssertion(response)
        
        # 执行断言
        assertion.assert_status_code(201)
        assertion.assert_response_time(3000)
        assertion.assert_json_path("$.title", "foo")
        assertion.assert_json_path("$.userId", 1)
        
        logger.info("POST请求测试通过")
        return {
            "status": "passed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "status_code": response.status_code
        }
    except Exception as e:
        logger.error(f"POST请求测试失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

def test_with_report_generation():
    """
    生成测试报告示例
    """
    # 执行测试
    results = []
    results.append(test_get_request_example())
    results.append(test_post_request_example())
    
    # 生成报告
    report = ReportGenerator()
    report_data = {
        "test_suite": "API测试示例套件",
        "results": results,
        "environment": {
            "framework_version": "1.0.0",
            "python_version": "3.10+"
        }
    }
    
    # 生成HTML报告
    html_report_path = report.generate_html_report(report_data, "api_test_report.html")
    logger.info(f"HTML报告已生成: {html_report_path}")
    
    # 生成JSON报告
    json_report_path = report.generate_json_report(report_data, "api_test_report.json")
    logger.info(f"JSON报告已生成: {json_report_path}")
    
    return {
        "html_report": html_report_path,
        "json_report": json_report_path,
        "total_tests": len(results),
        "passed_tests": sum(1 for r in results if r["status"] == "passed")
    }

if __name__ == "__main__":
    # 运行测试并生成报告
    test_with_report_generation()