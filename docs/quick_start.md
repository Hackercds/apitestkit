# 快速开始

本文档将帮助您快速了解和开始使用ApiTestKit框架进行API测试。

## 基础示例

### 1. 发送GET请求并验证响应

```python
from apitestkit import api

# 发送GET请求并验证响应
api()\
    .test("获取用户信息测试")\
    .step("获取用户ID为1的信息")\
    .get("/users/1")  # 相对路径，会与base_url拼接
    .base_url("https://api.example.com")  # 设置基础URL
    .headers({"Content-Type": "application/json"})  # 设置请求头
    .send()  # 发送请求
    .assert_status_code(200)  # 断言状态码为200
    .assert_json_path("data.username", "testuser")  # 断言JSON路径的值
    .assert_response_time(500)  # 断言响应时间小于500ms
```

### 2. 发送POST请求创建资源

```python
from apitestkit import api

# 发送POST请求创建用户
api()\
    .test("创建用户测试")\
    .step("创建新用户")\
    .post("https://api.example.com/users")  # 完整URL
    .json({
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123"
    })  # JSON请求体
    .send()\
    .assert_status_code(201)  # 断言创建成功状态码
    .extract("user_id", "data.id")  # 提取变量供后续使用
```

## 使用变量

### 提取和引用变量

```python
from apitestkit import api

# 第一步：登录并提取token
api()\
    .test("用户登录测试")\
    .step("用户登录")\
    .post("https://api.example.com/login")\
    .json({"username": "test", "password": "test123"})\
    .send()\
    .assert_status_code(200)\
    .extract("token", "data.token")  # 提取token变量

# 第二步：使用token进行认证请求
api()\
    .test("使用token访问测试")\
    .step("获取个人信息")\
    .get("https://api.example.com/profile")\
    .headers({"Authorization": "Bearer {{token}}"})  # 引用之前提取的token
    .send()\
    .assert_status_code(200)
```

## 使用装饰器定义测试

除了链式调用，还可以使用装饰器定义测试用例：

```python
from apitestkit import api_test, http_get, assert_response

@api_test("获取产品列表测试")
@http_get("https://api.example.com/products")
@assert_response(status_code=200)
def test_get_products(response):
    # 这里可以添加自定义断言逻辑
    data = response.json()
    assert len(data["products"]) > 0, "产品列表不应为空"
    return data

# 运行测试
test_get_products()
```

## 使用测试套件

对于更复杂的测试场景，可以使用测试套件：

```python
from apitestkit import TestSuite, TestCase

# 创建测试用例
class UserAPITest(TestCase):
    def setup(self):
        # 测试前准备工作
        self.base_url = "https://api.example.com"
    
    def test_login(self):
        # 登录测试
        response = self.api.post("/login") \
            .json({"username": "test", "password": "test123"}) \
            .send()
        
        self.assert_status_code(response, 200)
        self.extract("token", response, "data.token")
    
    def test_get_profile(self):
        # 获取个人信息测试
        response = self.api.get("/profile") \
            .headers({"Authorization": f"Bearer {{token}}"}) \
            .send()
        
        self.assert_status_code(response, 200)
    
    def teardown(self):
        # 测试后清理工作
        pass

# 创建并运行测试套件
suite = TestSuite("用户API测试套件")
suite.add_test(UserAPITest())
suite.run()

# 生成报告
report = suite.generate_report()
```

## 配置管理

在测试前配置框架：

```python
from apitestkit import config_manager

# 全局配置
config_manager.update({
    "base_url": "https://api.example.com",
    "timeout": 30,
    "log_level": "INFO",
    "report_directory": "./reports"
})

# 然后在测试中使用这些配置
from apitestkit import api

api()\
    .test("配置测试")\
    .get("/users")  # 会自动使用配置的base_url
    .send()
```

## 处理大模型流式API

ApiTestKit支持处理大模型的流式API响应：

```python
from apitestkit import api

# 发送流式请求
response_stream = api()\
    .test("大模型流式API测试")\
    .post("https://api.example.com/chat/completions")\
    .json({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": True
    })\
    .stream()  # 使用stream模式
    .send()

# 处理流式响应
full_response = ""
for chunk in response_stream:
    # 处理每个数据块
    if chunk and "content" in chunk:
        print(chunk["content"], end="", flush=True)
        full_response += chunk["content"]

print(f"\n完整响应: {full_response}")
```

## 生成测试报告

测试完成后生成报告：

```python
from apitestkit import api, generate_html_report

# 运行一系列测试
test_results = []

# 测试1
test1 = api()\
    .test("测试1")\
    .get("https://api.example.com/users")\
    .send()\
    .assert_status_code(200)

test_results.append(test1.results)

# 测试2
test2 = api()\
    .test("测试2")\
    .post("https://api.example.com/users")\
    .json({"name": "test"})\
    .send()\
    .assert_status_code(201)

test_results.append(test2.results)

# 生成HTML报告
generate_html_report(
    test_results,
    output_path="./reports/api_test_report.html",
    title="API测试报告"
)

print("报告已生成: ./reports/api_test_report.html")
```

## 异步测试

对于需要并行执行的测试，可以使用异步模式：

```python
import asyncio
from apitestkit import api

async def run_async_tests():
    # 创建多个异步测试任务
    tasks = [
        api().test("异步测试1").get("https://api.example.com/test1").send_async(),
        api().test("异步测试2").get("https://api.example.com/test2").send_async(),
        api().test("异步测试3").get("https://api.example.com/test3").send_async()
    ]
    
    # 并行执行所有测试
    results = await asyncio.gather(*tasks)
    
    # 处理结果
    for i, result in enumerate(results):
        print(f"测试 {i+1} 结果: {result['status_code']}")

# 运行异步测试
asyncio.run(run_async_tests())
```

## 常见问题解答

### 如何设置代理？

```python
# 设置HTTP代理
api()\
    .test("代理测试")\
    .get("https://api.example.com")\
    .proxies({"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"})\
    .send()
```

### 如何上传文件？

```python
# 上传文件
api()\
    .test("文件上传测试")\
    .post("https://api.example.com/upload")\
    .files({"file": open("test.txt", "rb")})\
    .send()
```

### 如何处理认证？

```python
# 基本认证
api()\
    .test("基本认证测试")\
    .get("https://api.example.com/protected")\
    .auth(("username", "password"))\
    .send()

# Bearer Token认证
api()\
    .test("Token认证测试")\
    .get("https://api.example.com/protected")\
    .headers({"Authorization": "Bearer your_token_here"})\
    .send()
```

## 下一步

- 查看[配置指南](configuration_guide.md)了解更多配置选项
- 查看[API参考文档](api_reference.md)了解所有可用的API
- 查看[高级功能指南](advanced_features.md)了解框架的高级特性