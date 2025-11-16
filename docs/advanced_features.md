# 高级功能指南

本文档介绍ApiTestKit框架的高级特性和使用方法，帮助您充分利用框架的强大功能。

## 1. 变量管理系统

### 1.1 变量作用域

ApiTestKit提供了多级变量作用域：

```python
from apitestkit import api, config_manager

# 1. 全局变量（可在所有测试中使用）
config_manager.set("global_var", "全局值")

# 2. 会话变量（在当前会话中共享）
api().test("设置会话变量").set_var("session_var", "会话值").send()

# 3. 提取变量（从响应中提取）
api().test("提取变量").get("/data").send().extract("extracted_var", "data.value")

# 在后续测试中使用变量
api().test("使用变量").get("/endpoint").params({"param1": "{{global_var}}", "param2": "{{session_var}}"}).send()
```

### 1.2 变量表达式

支持在请求参数中使用复杂的变量表达式：

```python
# 使用变量表达式
api()\
    .test("变量表达式测试")\
    .post("/users")\
    .json({
        "username": "user_{{timestamp}}",  # 使用时间戳变量
        "email": "user_{{random_number}}@example.com",  # 使用随机数
        "profile": "{{uppercase('test profile')}}"  # 使用函数转换
    })\
    .send()
```

### 1.3 内置变量

框架提供了一些内置变量：

- `{{timestamp}}`: 当前时间戳
- `{{random_number}}`: 随机数字
- `{{random_string}}`: 随机字符串
- `{{uuid}}`: 唯一标识符
- `{{date}}`: 当前日期
- `{{datetime}}`: 当前日期时间

## 2. 高级断言功能

### 2.1 自定义断言函数

```python
from apitestkit import api
from apitestkit.assertion import ResponseAssertion

# 自定义断言函数
def custom_assertion(response, expected_value):
    data = response.json()
    assert "custom_field" in data, "响应中缺少custom_field字段"
    assert data["custom_field"] == expected_value, f"custom_field值不匹配: {data['custom_field']} != {expected_value}"
    return True

# 使用自定义断言
api()\
    .test("自定义断言测试")\
    .get("/custom-endpoint")\
    .send()\
    .assert_custom(custom_assertion, "expected_value")
```

### 2.2 断言组合

```python
# 组合多个断言条件
api()\
    .test("断言组合测试")\
    .get("/complex-data")\
    .send()\
    .assert_all([
        ("status_code", 200),
        ("json_path", "data.id", 123),
        ("response_time", 1000),
        ("contains", "success")
    ])
```

### 2.3 JSON Schema验证

```python
# JSON Schema验证
from apitestkit import api

# 定义Schema
schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["id", "name", "email"]
}

# 验证响应是否符合Schema
api()\
    .test("Schema验证测试")\
    .get("/user/1")\
    .send()\
    .assert_schema(schema)
```

## 3. 测试数据管理

### 3.1 数据驱动测试

```python
import pandas as pd
from apitestkit import TestSuite, TestCase

# 数据驱动测试用例
class DataDrivenTest(TestCase):
    def setup(self):
        # 读取测试数据
        self.test_data = pd.read_csv("test_data.csv").to_dict('records')
    
    def test_with_data(self):
        for data in self.test_data:
            self.api.test(f"测试 {data['test_id']}") \
                .post("/users") \
                .json({
                    "name": data["name"],
                    "email": data["email"]
                }) \
                .send() \
                .assert_status_code(data["expected_status"])

# 运行数据驱动测试
suite = TestSuite("数据驱动测试套件")
suite.add_test(DataDrivenTest())
suite.run()
```

### 3.2 测试数据生成器

```python
from apitestkit import api
from apitestkit.core.data_generator import DataGenerator

# 创建数据生成器
generator = DataGenerator()

# 生成测试数据
test_user = {
    "username": generator.username(),
    "email": generator.email(),
    "phone": generator.phone_number(),
    "address": generator.address(),
    "birth_date": generator.date_of_birth(min_age=18, max_age=65)
}

# 使用生成的数据\api()\
    .test("使用生成数据测试")\
    .post("/users")\
    .json(test_user)\
    .send()\
    .assert_status_code(201)
```

## 4. 测试场景管理

### 4.1 创建复杂测试场景

```python
from apitestkit import Scenario

# 创建测试场景
scenario = Scenario("用户管理场景")

# 添加测试步骤
scenario.add_step(
    name="用户注册",
    method="POST",
    url="/users/register",
    json={"username": "newuser", "email": "newuser@example.com", "password": "pass123"},
    assertions=[
        ("status_code", 201),
        ("extract", "user_id", "data.id")
    ]
)

scenario.add_step(
    name="用户登录",
    method="POST",
    url="/users/login",
    json={"email": "newuser@example.com", "password": "pass123"},
    assertions=[
        ("status_code", 200),
        ("extract", "token", "data.token")
    ]
)

scenario.add_step(
    name="获取用户信息",
    method="GET",
    url="/users/{{user_id}}",
    headers={"Authorization": "Bearer {{token}}"},
    assertions=[
        ("status_code", 200),
        ("json_path", "data.username", "newuser")
    ]
)

# 执行场景
results = scenario.run()
print(f"场景执行完成，成功步骤: {results['passed_steps']}, 失败步骤: {results['failed_steps']}")
```

### 4.2 场景前置和后置处理

```python
# 添加场景前置和后置处理
scenario = Scenario("带钩子的场景")

# 前置处理
def before_scenario():
    print("场景开始前的准备工作")
    # 创建测试环境、准备测试数据等
    return {"environment": "test"}

# 后置处理
def after_scenario(results):
    print(f"场景执行完成，总步骤: {results['total_steps']}")
    # 清理测试数据、恢复环境等

scenario.set_before(before_scenario)
scenario.set_after(after_scenario)

# 执行场景
scenario.run()
```

## 5. 大模型API测试增强

### 5.1 Agent接口测试

```python
from apitestkit import api, AgentAdapter

# 创建Agent适配器
agent = AgentAdapter(base_url="https://api.example.com/agent")

# 设置Agent参数模板
agent.set_template("default", {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
})

# 发送Agent请求
response = agent.chat(
    template="default",
    messages=[
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "解释什么是API测试"}
    ]
)

# 验证响应
assert response.status_code == 200
assert "content" in response.json()
```

### 5.2 流式响应处理高级特性

```python
from apitestkit import api

# 流式响应带回调处理
def stream_callback(chunk, context):
    """处理每个数据块的回调函数"""
    if chunk and "content" in chunk:
        # 累计内容
        if "full_content" not in context:
            context["full_content"] = ""
        context["full_content"] += chunk["content"]
        
        # 实时分析
        if "关键词" in chunk["content"]:
            print("检测到关键词!")
    return chunk

# 发送流式请求并处理
context = {}
response = api()\
    .test("高级流式处理测试")\
    .post("https://api.example.com/chat/completions")\
    .json({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "详细介绍API测试的最佳实践"}],
        "stream": True
    })\
    .stream()\
    .callback(stream_callback, context)\
    .send()

# 使用上下文数据
print(f"完整响应长度: {len(context['full_content'])} 字符")
```

## 6. 报告和监控

### 6.1 自定义报告模板

```python
from apitestkit.report import ReportGenerator

# 使用自定义模板生成报告
generator = ReportGenerator()

# 加载自定义Jinja2模板
generator.load_template("custom_report.html")

# 生成报告
generator.generate(
    test_results,
    output_path="./reports/custom_report.html",
    title="自定义测试报告",
    extra_data={"environment": "production", "release": "v1.0.0"}
)
```

### 6.2 实时监控和通知

```python
from apitestkit import TestSuite, TestCase
from apitestkit.core.notifier import EmailNotifier

# 创建通知器
email_notifier = EmailNotifier(
    smtp_server="smtp.example.com",
    smtp_port=587,
    username="test@example.com",
    password="password",
    recipients=["admin@example.com", "manager@example.com"]
)

# 创建测试套件并添加通知器
suite = TestSuite("带通知的测试套件")
suite.add_notifier(email_notifier)
suite.add_test(TestCase())

# 运行测试（失败时会发送邮件通知）
suite.run()
```

## 7. 性能测试集成

### 7.1 基本性能测试

```python
from apitestkit import api

# 运行性能测试
performance_results = api()\
    .test("性能测试")\
    .get("https://api.example.com/performance-test")\
    .performance(
        concurrency=50,  # 并发用户数
        requests=1000,   # 总请求数
        duration=30      # 持续时间（秒）
    )\
    .send()

# 分析性能结果
print(f"平均响应时间: {performance_results['avg_response_time']} ms")
print(f"95%响应时间: {performance_results['p95_response_time']} ms")
print(f"吞吐量: {performance_results['throughput']} 请求/秒")
print(f"错误率: {performance_results['error_rate']}%")
```

### 7.2 性能测试报告

```python
from apitestkit.report import ChartsGenerator

# 生成性能测试图表报告
charts = ChartsGenerator()
charts.generate_performance_chart(
    performance_results,
    output_path="./reports/performance_chart.png",
    title="API性能测试结果"
)

# 生成性能测试HTML报告
charts.generate_performance_report(
    performance_results,
    output_path="./reports/performance_report.html"
)
```

## 8. 安全性测试

### 8.1 基本安全检查

```python
from apitestkit import api
from apitestkit.security import SecurityChecker

# 创建安全检查器
security = SecurityChecker()

# 运行安全测试
response = api().get("https://api.example.com/endpoint").send()

# 执行安全检查
security_results = security.check(
    response,
    checks=[
        "check_headers",        # 检查安全响应头
        "check_cors",           # 检查CORS配置
        "check_content_type",   # 检查Content-Type
        "check_information_disclosure"  # 检查信息泄露
    ]
)

# 打印安全检查结果
for check_name, result in security_results.items():
    status = "通过" if result["passed"] else "失败"
    print(f"{check_name}: {status}")
    if not result["passed"]:
        print(f"  问题: {result['issues']}")
```

## 9. 最佳实践

### 9.1 测试分层

1. **单元测试**: 测试单个API端点
2. **集成测试**: 测试多个API端点的交互
3. **场景测试**: 测试完整的业务流程
4. **性能测试**: 测试API的性能特性
5. **安全测试**: 测试API的安全性

### 9.2 测试组织

```
project/
├── config/            # 配置文件
│   ├── dev.yaml
│   ├── test.yaml
│   └── prod.yaml
│
├── data/              # 测试数据
│   ├── test_data.csv
│   └── test_data.json
│
├── tests/             # 测试用例
│   ├── unit/          # 单元测试
│   ├── integration/   # 集成测试
│   ├── scenarios/     # 场景测试
│   └── performance/   # 性能测试
│
├── utils/             # 工具函数
│   ├── fixtures.py
│   └── helpers.py
│
└── conftest.py        # pytest配置
```

### 9.3 CI/CD集成

```yaml
# .github/workflows/api_tests.yml
name: API Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install apitestkit
    
    - name: Run API tests
      run: |
        pytest tests/ -v
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: reports/
      if: always()
```

## 10. 故障排除

### 10.1 常见错误及解决方案

#### 连接超时

```python
# 增加超时时间
api()\
    .test("超时测试")\
    .get("https://slow-api.example.com")\
    .timeout(60)  # 60秒超时
    .send()
```

#### SSL验证问题

```python
# 禁用SSL验证（仅开发环境）
api()\
    .test("SSL测试")\
    .get("https://self-signed-api.example.com")\
    .verify(False)  # 禁用SSL验证
    .send()
```

#### 请求重试

```python
# 配置重试策略
api()\
    .test("重试测试")\
    .get("https://unstable-api.example.com")\
    .retries(3)  # 最多重试3次
    .retry_interval(2)  # 每次重试间隔2秒
    .send()
```

## 下一步

- 查看[API参考文档](api_reference.md)了解详细的API文档
- 查看[示例目录](../examples)了解更多实际使用案例