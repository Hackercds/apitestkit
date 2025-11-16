# ApiTestKit 用户使用指南

欢迎使用ApiTestKit，这是一个功能强大、易于使用的API测试框架。本指南将帮助您快速上手并充分利用框架的各种功能。

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 基本用法](#2-基本用法)
- [3. 断言系统](#3-断言系统)
- [4. 变量管理](#4-变量管理)
- [5. 测试组织](#5-测试组织)
- [6. 高级功能](#6-高级功能)
- [7. 报告和监控](#7-报告和监控)
- [8. 配置管理](#8-配置管理)
- [9. 常见问题](#9-常见问题)

## 1. 快速开始

### 1.1 安装

```bash
pip install apitestkit
```

### 1.2 简单测试示例

```python
from apitestkit import api

# 发送GET请求并断言
response = api()\
    .test("测试示例")\
    .get("https://httpbin.org/get")\
    .send()\
    .assert_status_code(200)\
    .assert_contains("origin")

print(f"响应状态码: {response.status_code}")
print(f"响应耗时: {response.time()} 毫秒")
```

## 2. 基本用法

### 2.1 HTTP请求方法

```python
# GET请求
api().get("https://httpbin.org/get").send()

# POST请求
api().post("https://httpbin.org/post").json({"name": "test"}).send()

# PUT请求
api().put("https://httpbin.org/put").json({"name": "updated"}).send()

# DELETE请求
api().delete("https://httpbin.org/delete").send()

# PATCH请求
api().patch("https://httpbin.org/patch").json({"name": "patched"}).send()
```

### 2.2 请求配置

```python
# 设置请求头
api()\
    .get("https://httpbin.org/get")\
    .headers({
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    })\
    .send()

# 设置查询参数
api()\
    .get("https://httpbin.org/get")\
    .params({"key1": "value1", "key2": "value2"})\
    .send()

# 设置表单数据
api()\
    .post("https://httpbin.org/post")\
    .data({"username": "admin", "password": "pass123"})\
    .send()

# 上传文件
api()\
    .post("https://httpbin.org/post")\
    .files({"file": open("test.txt", "rb")})\
    .send()
```

### 2.3 响应处理

```python
response = api().get("https://httpbin.org/get").send()

# 获取状态码
print(response.status_code)  # 输出: 200

# 获取响应头
print(response.headers["Content-Type"])  # 输出: application/json

# 获取响应内容
print(response.text)

# 解析JSON
json_data = response.json()
print(json_data["url"])

# 获取响应耗时
print(response.time())  # 输出毫秒数
```

## 3. 断言系统

### 3.1 基本断言

```python
api()\
    .get("https://httpbin.org/get")\
    .send()\
    # 断言状态码
    .assert_status_code(200)\
    # 断言响应包含文本
    .assert_contains("url")\
    # 断言响应不包含文本
    .assert_not_contains("error")\
    # 断言响应时间小于1000毫秒
    .assert_response_time(1000)
```

### 3.2 JSON路径断言

```python
# JSON路径断言
api()\
    .get("https://httpbin.org/get")\
    .send()\
    # 断言JSON路径存在
    .assert_json_path_exists("headers.Host")\
    # 断言JSON路径不存在
    .assert_json_path_not_exists("error")\
    # 断言JSON路径值
    .assert_json_path("url", "https://httpbin.org/get")
```

### 3.3 通配符支持

```python
# 使用通配符进行断言
response_data = {
    "data": {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"}
        ]
    }
}

# 使用通配符获取所有用户ID
user_ids = api()._extract_json_path(response_data, "data.users[*].id")
print(user_ids)  # 输出: [1, 2, 3]
```

### 3.4 自定义断言

```python
def custom_assertion(response, min_length):
    data = response.json()
    assert len(data) >= min_length, f"响应数据长度不足: {len(data)} < {min_length}"
    return True

api()\
    .get("https://httpbin.org/get")\
    .send()\
    .assert_custom(custom_assertion, 5)  # 断言响应数据至少有5个字段
```

## 4. 变量管理

### 4.1 变量提取

```python
# 从响应中提取变量
api()\
    .test("提取变量测试")\
    .get("https://httpbin.org/uuid")\
    .send()\
    .extract("uuid", "uuid")  # 提取uuid字段

# 在后续请求中使用变量
api()\
    .test("使用变量测试")\
    .get("https://httpbin.org/anything")\
    .params({"id": "{{uuid}}"})\
    .send()
```

### 4.2 会话变量

```python
# 设置会话变量
api()\
    .test("设置会话变量")\
    .set_var("token", "abc123")\
    .send()

# 使用会话变量
api()\
    .test("使用会话变量")\
    .get("https://httpbin.org/anything")\
    .headers({"Authorization": "Bearer {{token}}"})\
    .send()
```

### 4.3 全局变量

```python
from apitestkit import config_manager

# 设置全局变量
config_manager.set("base_url", "https://api.example.com")

# 使用全局变量
api()\
    .test("使用全局变量")\
    .get("{{base_url}}/endpoint")\
    .send()
```

## 5. 测试组织

### 5.1 测试用例类

```python
from apitestkit import TestCase

class UserApiTest(TestCase):
    def setup(self):
        # 测试类级别的设置
        print("测试类开始执行")
    
    def teardown(self):
        # 测试类级别的清理
        print("测试类执行完成")
    
    def set_up(self):
        # 测试方法级别的设置
        print("测试方法开始执行")
    
    def tear_down(self):
        # 测试方法级别的清理
        print("测试方法执行完成")
    
    def test_create_user(self):
        # 测试创建用户
        self.api.test("创建用户")\
            .post("https://httpbin.org/post")\
            .json({"name": "测试用户", "email": "test@example.com"})\
            .send()\
            .assert_status_code(200)
    
    def test_get_user(self):
        # 测试获取用户
        self.api.test("获取用户")\
            .get("https://httpbin.org/get")\
            .send()\
            .assert_status_code(200)
```

### 5.2 测试套件

```python
from apitestkit import TestSuite

# 创建测试套件
suite = TestSuite("用户API测试套件")

# 添加测试用例
suite.add_test(UserApiTest())

# 运行测试套件
results = suite.run()
print(f"测试结果: {results['passed']}/{results['total']} 测试通过")
```

### 5.3 测试场景

```python
from apitestkit import Scenario

# 创建测试场景
scenario = Scenario("用户登录场景")

# 添加步骤
scenario.add_step(
    name="登录",
    method="POST",
    url="https://httpbin.org/post",
    json={"username": "admin", "password": "pass123"},
    assertions=[
        ("status_code", 200),
        ("extract", "token", "json.token")
    ]
)

scenario.add_step(
    name="获取用户信息",
    method="GET",
    url="https://httpbin.org/get",
    headers={"Authorization": "Bearer {{token}}"},
    assertions=[
        ("status_code", 200)
    ]
)

# 执行场景
results = scenario.run()
print(f"场景执行结果: {results['passed_steps']}/{results['total_steps']} 步骤通过")
```

## 6. 高级功能

### 6.1 流式响应处理

```python
# 处理流式响应
def stream_callback(chunk, context):
    if chunk:
        print(f"收到数据块: {chunk}")
        # 可以在这里进行实时处理
    return chunk

# 发送流式请求
api()\
    .test("流式响应测试")\
    .get("https://httpbin.org/stream/5")\
    .stream()\
    .callback(stream_callback)\
    .send()
```

### 6.2 数据驱动测试

```python
import pandas as pd
from apitestkit import TestCase

class DataDrivenTest(TestCase):
    def setup(self):
        # 读取测试数据
        self.test_data = [
            {"username": "user1", "password": "pass1", "expected_status": 200},
            {"username": "user2", "password": "pass2", "expected_status": 401}
        ]
    
    def test_login_with_data(self):
        for data in self.test_data:
            self.api.test(f"登录测试: {data['username']}") \
                .post("https://httpbin.org/post") \
                .json({
                    "username": data["username"],
                    "password": data["password"]
                }) \
                .send() \
                .assert_status_code(data["expected_status"])
```

### 6.3 Agent接口测试

```python
from apitestkit import AgentAdapter

# 创建Agent适配器
agent = AgentAdapter(base_url="https://api.example.com/agent")

# 设置模板
agent.set_template("default", {
    "model": "gpt-4",
    "temperature": 0.7
})

# 发送请求
response = agent.chat(
    template="default",
    messages=[
        {"role": "system", "content": "你是一个API测试助手"},
        {"role": "user", "content": "生成一个API测试用例"}
    ]
)

# 验证响应
print(response.json())
```

## 7. 报告和监控

### 7.1 生成测试报告

```python
from apitestkit import TestSuite
from apitestkit.report import ReportGenerator

# 运行测试套件
suite = TestSuite("示例测试套件")
suite.add_test(UserApiTest())
results = suite.run()

# 生成报告
generator = ReportGenerator()
generator.generate(
    results,
    output_path="./reports/test_report.html",
    title="API测试报告"
)
```

### 7.2 性能测试报告

```python
from apitestkit import api
from apitestkit.report import ChartsGenerator

# 运行性能测试
performance_results = api()\
    .test("性能测试")\
    .get("https://httpbin.org/get")\
    .performance(concurrency=10, requests=100)\
    .send()

# 生成性能图表
charts = ChartsGenerator()
charts.generate_performance_chart(
    performance_results,
    output_path="./reports/performance_chart.png",
    title="API性能测试结果"
)
```

## 8. 配置管理

### 8.1 代码中配置

```python
from apitestkit import config_manager

# 设置配置
config_manager.set("base_url", "https://api.example.com")
config_manager.set("timeout", 30)
config_manager.set("verify_ssl", False)

# 获取配置
base_url = config_manager.get("base_url")
```

### 8.2 配置文件

```python
# 从YAML文件加载配置
config_manager.load("./config/test_config.yaml")

# 从JSON文件加载配置
config_manager.load("./config/test_config.json")

# 保存配置到文件
config_manager.save("./config/saved_config.yaml")
```

### 8.3 配置示例

YAML配置文件示例：

```yaml
# test_config.yaml
base_url: https://api.example.com
timeout: 30
verify_ssl: false
headers:
  Content-Type: application/json
  User-Agent: ApiTestKit/1.0.0
```

JSON配置文件示例：

```json
{
  "base_url": "https://api.example.com",
  "timeout": 30,
  "verify_ssl": false,
  "headers": {
    "Content-Type": "application/json",
    "User-Agent": "ApiTestKit/1.0.0"
  }
}
```

## 9. 常见问题

### 9.1 连接超时

如果遇到连接超时问题，可以增加超时时间：

```python
api()\
    .get("https://slow-api.example.com")\
    .timeout(60)  # 设置60秒超时
    .send()
```

### 9.2 SSL验证错误

如果在测试环境中遇到SSL验证错误，可以禁用SSL验证：

```python
api()\
    .get("https://self-signed-api.example.com")\
    .verify(False)  # 禁用SSL验证
    .send()
```

### 9.3 变量替换不生效

确保变量名称正确，并且变量在使用前已经定义：

```python
# 正确顺序：先设置变量，再使用变量
api().set_var("token", "abc123").send()
api().get("/endpoint", params={"auth": "{{token}}"}).send()
```

### 9.4 JSON路径表达式

使用JSON路径时，请确保路径格式正确：

- 简单属性：`data.name`
- 数组索引：`data.users[0]`
- 通配符：`data.users[*].name`
- 嵌套路径：`data.details.address.city`

## 10. 其他资源

- [安装指南](installation_guide.md) - 详细的安装说明
- [配置指南](configuration_guide.md) - 完整的配置选项
- [快速开始](quick_start.md) - 基础入门教程
- [高级功能](advanced_features.md) - 高级特性说明
- [API参考](api_reference.md) - 完整的API文档