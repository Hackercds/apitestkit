# apitestkit 用户指南

本文档提供了 apitestkit 的详细使用指南，帮助您快速上手并充分利用框架的各项功能。

## 目录

- [快速开始](#快速开始)
- [基本概念](#基本概念)
- [HTTP 请求](#http-请求)
- [响应断言](#响应断言)
- [配置管理](#配置管理)
- [日志记录](#日志记录)
- [数据提取](#数据提取)
- [测试用例](#测试用例)
- [报告生成](#报告生成)
- [高级功能](#高级功能)

## 快速开始

### 导入模块

首先，导入 apitestkit 的核心模块：

```python
from apitestkit.request.http_client import http_client
from apitestkit.assertion.assertions import response_assertion
```

### 发送请求

发送一个简单的 GET 请求：

```python
response = http_client.get("https://api.example.com/users")
```

### 断言响应

验证响应状态码和内容：

```python
response_assertion.assert_status_code(response, 200)
response_assertion.assert_json_path(response, "$.data.length", 10)
```

## 基本概念

### HTTP 客户端

`http_client` 是 apitestkit 的核心组件，用于发送 HTTP 请求。它支持各种 HTTP 方法，如 GET、POST、PUT、DELETE 等。

### 响应断言

`response_assertion` 提供了丰富的断言方法，用于验证 API 响应的正确性。

### 配置管理

通过配置管理，您可以自定义框架的行为，如超时设置、日志级别等。

### 测试用例

`TestCase` 类用于定义测试用例，支持 setUp、tearDown 和各种测试方法。

## HTTP 请求

### 基本请求

```python
# GET 请求
response = http_client.get("https://api.example.com/users")

# POST 请求
response = http_client.post(
    "https://api.example.com/users",
    json={"name": "John Doe", "email": "john@example.com"}
)

# PUT 请求
response = http_client.put(
    "https://api.example.com/users/1",
    json={"name": "Jane Doe"}
)

# DELETE 请求
response = http_client.delete("https://api.example.com/users/1")
```

### 设置请求头

```python
response = http_client.get(
    "https://api.example.com/users",
    headers={
        "Authorization": "Bearer your_token",
        "Content-Type": "application/json"
    }
)
```

### 设置查询参数

```python
response = http_client.get(
    "https://api.example.com/users",
    params={"page": 1, "limit": 10}
)
```

### 上传文件

```python
response = http_client.post(
    "https://api.example.com/upload",
    files={"file": open("path/to/file.txt", "rb")}
)
```

### 设置超时

```python
response = http_client.get(
    "https://api.example.com/users",
    timeout=30
)
```

## 响应断言

### 状态码断言

```python
response_assertion.assert_status_code(response, 200)
response_assertion.assert_status_code_in(response, [200, 201])
```

### JSON 路径断言

```python
# 断言 JSON 路径的值
response_assertion.assert_json_path(response, "$.data[0].name", "John Doe")

# 断言 JSON 路径存在
response_assertion.assert_json_path_exists(response, "$.data")

# 断言 JSON 路径不存在
response_assertion.assert_json_path_not_exists(response, "$.error")

# 断言 JSON 路径的值包含指定字符串
response_assertion.assert_json_path_contains(response, "$.data[0].description", "test")
```

### 响应时间断言

```python
# 断言响应时间小于 500 毫秒
response_assertion.assert_response_time(response, 500)
```

### 响应头断言

```python
# 断言响应头存在
response_assertion.assert_header_exists(response, "Content-Type")

# 断言响应头的值
response_assertion.assert_header_equal(response, "Content-Type", "application/json")
```

### 响应内容断言

```python
# 断言响应内容包含指定字符串
response_assertion.assert_content_contains(response, "success")

# 断言响应内容不包含指定字符串
response_assertion.assert_content_not_contains(response, "error")
```

## 配置管理

### 配置管理器

```python
from apitestkit.core.config import config_manager

# 设置配置
config_manager.set("base_url", "https://api.example.com")
config_manager.set("timeout", 30)
config_manager.set("log_level", "INFO")

# 获取配置
base_url = config_manager.get("base_url")

# 从配置文件加载
config_manager.load_from_file("config.json")
```

### 配置文件示例

**JSON 格式**:

```json
{
  "base_url": "https://api.example.com",
  "timeout": 30,
  "log_level": "INFO",
  "log_file": "logs/apitestkit.log",
  "ssl_verify": true
}
```

## 日志记录

### 日志管理器

```python
from apitestkit.core.logger import logger_manager

# 获取日志记录器
logger = logger_manager.get_logger("test_logger")

# 记录日志
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.debug("This is a debug message")
```

### 敏感数据过滤

默认情况下，日志记录会过滤敏感数据，如密码、令牌等。您可以自定义需要过滤的关键字：

```python
logger_manager.add_sensitive_keywords(["custom_token", "api_key"])
```

## 数据提取

### 提取 JSON 数据

```python
from apitestkit.extractor.data_extractor import data_extractor

# 从响应中提取数据
user_id = data_extractor.extract_json_path(response, "$.data[0].id")
user_names = data_extractor.extract_json_path(response, "$.data[*].name")
```

### 提取响应头数据

```python
# 从响应头中提取数据
content_type = data_extractor.extract_header(response, "Content-Type")
```

## 测试用例

### 基本测试用例

```python
from apitestkit.test.test_case import TestCase
from apitestkit.test.test_runner import test_runner

class UserManagementTest(TestCase):
    def setUp(self):
        # 测试前的设置
        http_client.base_url = "https://api.example.com"
        http_client.headers = {"Authorization": "Bearer your_token"}
    
    def test_get_user_list(self):
        """测试获取用户列表"""
        response = http_client.get("/users")
        response_assertion.assert_status_code(response, 200)
        response_assertion.assert_json_path_exists(response, "$.data")
    
    def test_create_user(self):
        """测试创建用户"""
        response = http_client.post(
            "/users",
            json={"name": "New User", "email": "new@example.com"}
        )
        response_assertion.assert_status_code(response, 201)
        
        # 提取用户ID用于后续测试
        self.user_id = data_extractor.extract_json_path(response, "$.data.id")
    
    def test_update_user(self):
        """测试更新用户信息"""
        if hasattr(self, 'user_id'):
            response = http_client.put(
                f"/users/{self.user_id}",
                json={"name": "Updated User"}
            )
            response_assertion.assert_status_code(response, 200)
    
    def tearDown(self):
        # 测试后的清理
        if hasattr(self, 'user_id'):
            http_client.delete(f"/users/{self.user_id}")

# 运行测试
if __name__ == "__main__":
    result = test_runner.run_test(UserManagementTest)
    print(f"测试结果: {result.passed}")
    print(f"通过的测试: {result.passed_count}")
    print(f"失败的测试: {result.failed_count}")
```

### 参数化测试

```python
from apitestkit.test.test_case import TestCase
from apitestkit.test.test_runner import test_runner

class ParameterizedTest(TestCase):
    # 参数化测试数据
    test_data = [
        (1, 2, 3),
        (4, 5, 9),
        (10, -5, 5)
    ]
    
    def test_addition(self):
        """参数化测试加法功能"""
        for a, b, expected in self.test_data:
            with self.subTest(f"测试 {a} + {b} = {expected}"):
                result = a + b
                self.assertEqual(result, expected)
```

## 报告生成

### 生成 HTML 报告

```python
from apitestkit.report.report_generator import report_generator

# 运行测试并获取结果
result = test_runner.run_test(UserManagementTest)

# 生成 HTML 报告
report_generator.generate_html_report(
    result,
    output_path="reports",
    title="API 测试报告"
)
```

### 生成 JSON 报告

```python
# 生成 JSON 报告
report_generator.generate_json_report(
    result,
    output_path="reports/test_result.json"
)
```

### 生成 CSV 报告

```python
# 生成 CSV 报告
report_generator.generate_csv_report(
    result,
    output_path="reports/test_result.csv"
)
```

## 高级功能

### 并发测试

```python
from apitestkit.test.concurrent_runner import concurrent_runner

# 并发运行测试
concurrent_result = concurrent_runner.run_concurrent(
    test_cases=[UserManagementTest, ProductManagementTest],
    workers=5
)
```

### 性能测试

```python
from apitestkit.test.performance_runner import performance_runner

# 执行性能测试
performance_result = performance_runner.run_performance_test(
    url="https://api.example.com/users",
    method="GET",
    concurrent_users=100,
    duration=60,  # 秒
    ramp_up=10    # 秒
)

# 生成性能测试报告
performance_runner.generate_performance_report(
    performance_result,
    output_path="reports/performance_report.html"
)
```

### 使用 API 适配器

```python
from apitestkit.adapter.api_adapter import api

# 使用 API 适配器进行链式调用
api()\
    .test("用户管理测试")\
    .step("获取用户列表")\
    .get("/users")\
    .headers({"Authorization": "Bearer your_token"})\
    .send()\
    .assert_status_code(200)\
    .assert_json_path_exists("$.data")\
    .extract("first_user_id", "$.data[0].id")
```

## 最佳实践

### 组织测试用例

- 将相关的测试用例组织在同一个测试类中
- 使用有意义的测试方法名称
- 添加详细的测试文档字符串
- 遵循单一职责原则，每个测试方法只测试一个功能

### 环境管理

- 使用配置文件管理不同环境的设置
- 在测试开始时设置环境，结束时清理
- 避免测试之间的相互依赖

### 日志和报告

- 合理使用日志记录关键操作和错误信息
- 定期生成测试报告以跟踪项目质量
- 在报告中包含足够的上下文信息以便问题定位

### 数据管理

- 使用测试数据工厂或fixture管理测试数据
- 测试后清理创建的测试数据
- 避免使用生产数据进行测试

---

如果您在使用过程中有任何问题或建议，请随时提交 issue 或联系开发团队。祝您使用愉快！