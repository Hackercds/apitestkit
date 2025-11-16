# apitestkit - API自动化测试框架

一个功能强大、易于使用的API自动化测试框架，提供全面的API测试解决方案，支持复杂的测试场景和报告生成。

## 功能特性

- 简洁易用的API请求接口
- 强大的断言系统，支持多种断言方式
- 灵活的配置管理，支持JSON/YAML配置文件
- 完善的日志记录和敏感数据过滤
- 丰富的报告生成功能（HTML/PDF/JSON/CSV/Excel）
- 支持数据提取和变量替换
- 跨平台兼容性，支持Windows、Linux、macOS
- 支持并发测试和性能测试

## 安装

### 从PyPI安装（推荐）

```bash
pip install apitestkit
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/apitestkit.git
cd apitestkit

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .
```

## 快速开始

### 基本使用示例

```python
from apitestkit.request.http_client import http_client
from apitestkit.assertion.assertions import response_assertion

# 发送GET请求
response = http_client.get("https://api.example.com/users")

# 断言响应状态码
response_assertion.assert_status_code(response, 200)

# 断言JSON响应内容
response_assertion.assert_json_path(response, "$.data[0].name", "expected_name")
```

### 测试用例示例

```python
from apitestkit.test.test_case import TestCase
from apitestkit.test.test_runner import test_runner
from apitestkit.request.http_client import http_client
from apitestkit.assertion.assertions import response_assertion

class UserManagementTest(TestCase):
    def setUp(self):
        # 设置测试环境
        self.base_url = "https://api.example.com"
        http_client.base_url = self.base_url
    
    def test_get_user_list(self):
        """测试获取用户列表接口"""
        response = http_client.get("/users")
        response_assertion.assert_status_code(response, 200)
        response_assertion.assert_json_path_exists(response, "$.data")
    
    def tearDown(self):
        # 清理测试环境
        pass

# 运行测试
if __name__ == "__main__":
    result = test_runner.run_test(UserManagementTest)
    print(f"测试结果: {result.passed}")
```

## 框架结构

```
apitestkit/
├── __init__.py      # 包初始化文件
├── core/            # 核心功能模块
│   ├── __init__.py  # 核心模块初始化
│   ├── config.py    # 配置管理
│   └── logger.py    # 日志管理
├── request/         # 请求模块
│   ├── __init__.py  # 请求模块初始化
│   ├── http_client.py  # HTTP客户端
│   └── auth/        # 认证子模块
│       ├── __init__.py
│       └── auth_manager.py  # 认证管理器
├── assertion/       # 断言模块
│   ├── __init__.py  # 断言模块初始化
│   └── assertions.py  # 断言实现
├── response/        # 响应模块
│   ├── __init__.py  # 响应模块初始化
│   └── response.py  # 响应处理
├── extractor/       # 数据提取器模块
│   ├── __init__.py  # 提取器模块初始化
│   └── data_extractor.py  # 数据提取实现
├── report/          # 报告模块
│   ├── __init__.py  # 报告模块初始化
│   ├── report_generator.py  # 报告生成
│   └── charts_generator.py  # 图表生成
├── test/            # 测试框架模块
│   ├── __init__.py  # 测试框架初始化
│   ├── test_case.py  # 测试用例基类
│   ├── test_runner.py  # 测试运行器
│   ├── test_suite.py  # 测试套件
│   └── factory.py   # 测试工厂
└── exception/       # 异常模块
    ├── __init__.py  # 异常模块初始化
    └── exceptions.py  # 异常定义
```

## 核心模块

### 1. 配置管理 (ConfigManager)

管理框架的全局配置，包括日志级别、超时时间、基础URL等。

```python
from apitestkit.core.config import config_manager

# 设置配置
config_manager.set('base_url', 'https://api.example.com')
config_manager.set('log_level', 'DEBUG')
config_manager.set('default_timeout', 60)
```

### 3. 日志管理 (LoggerManager)

负责日志的记录和管理，支持不同级别的日志输出。

```python
from apitestkit.core.logger import logger_manager

# 记录日志
logger_manager.info("这是一条信息日志")
logger_manager.warning("这是一条警告日志")
logger_manager.error("这是一条错误日志")
logger_manager.debug("这是一条调试日志")
```

### 4. 断言功能 (ResponseAssertion)

提供丰富的响应断言方法，验证API响应是否符合预期。

```python
from apitestkit.core.assertions import assertions

# 使用断言器
response = api().get("/api/users").send().get_response()
assertions.assert_status_code(response, 200)
assertions.assert_json_path(response, "data.length", 10)
```

## 高级功能

### 变量提取与引用

```python
# 提取变量并在后续请求中使用
api()\
    .test("变量提取与引用测试")\
    .step("登录并获取token")\
    .post("/api/login")\
    .json({"username": "test", "password": "password"})\
    .send()\
    .assert_status_code(200)\
    .extract("token", "data.token")

api()\
    .step("使用token获取用户信息")\
    .get("/api/user/info")\
    .headers({"Authorization": "Bearer {{token}}"})\
    .send()\
    .assert_status_code(200)
```

### Agent接口测试

```python
# 基本的Agent API测试
ai_api()\
    .test("大模型API测试")\
    .step("测试文本生成")\
    .base_url("https://api.example-llm.com")\
    .ai_prompt("请简要介绍API测试")\
    .ai_options({\
        "model": "gpt-3.5-turbo",\
        "temperature": 0.7,\
        "max_tokens": 100\
    })\
    .post("/v1/chat/completions")\
    .send()\
    .assert_status_code(200)
```

### 流式响应处理

```python
# 流式响应测试
ai_api()\
    .test("流式响应测试")\
    .step("测试流式生成")\
    .base_url("https://api.example-llm.com")\
    .stream(enable=True, format="sse")\
    .ai_prompt("请列出5个API测试工具")\
    .ai_options({"model": "gpt-3.5-turbo", "stream": True})\
    .post("/v1/chat/completions")\
    .stream_extract("choices[0].delta.content", "stream_content")\
    .send()

# 获取完整流式内容
full_content = api_instance.get_full_stream_content()
```

### 请求参数构建

```python
api()\
    .test("参数构建测试")\
    .step("发送带参数的请求")\
    .get("/api/search")\
    .params({"keyword": "test", "page": 1, "limit": 10})\
    .headers({"Accept": "application/json"})\
    .send()\
    .assert_status_code(200)

# 表单数据
api()\
    .step("发送表单数据")\
    .post("/api/submit")\
    .body({"name": "Test", "email": "test@example.com"})\
    .send()\
    .assert_status_code(201)
```

### 完整断言示例

```python
api()\
    .test("完整断言示例")\
    .step("验证多种断言")\
    .get("/api/status")\
    .send()\
    .assert_status_code(200) \
    .assert_response_time(1000)  # 响应时间不超过1000ms\
    .assert_contains("success")  # 响应内容包含"success"\
    .assert_json_path("data.status", "online")  # JSON路径断言\
    .assert_header("Content-Type", "application/json")  # 响应头断言
```

## 高级配置系统

apitestkit 提供了强大的配置管理系统，支持多种配置方式和高级功能：

### 核心功能

- **多格式支持**：支持 JSON 和 YAML 格式配置文件
- **环境变量替换**：配置中可使用 `${ENV_VAR}` 语法引用环境变量
- **分层配置**：支持默认配置、环境特定配置和本地配置的自动加载
- **嵌套配置访问**：支持点号分隔的嵌套键访问（如 `ai.temperature`）
- **配置验证**：自动验证配置值的有效性
- **环境变量加载**：支持从环境变量加载配置
- **配置保存**：支持将当前配置保存为 JSON/YAML 文件

### 主要配置项

```yaml
# 基础配置
log_level: DEBUG
log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
default_timeout: 60
base_url: "https://api.example.com/v1"
verify_ssl: false

# HTTP 请求配置
headers:
  Content-Type: "application/json"
  Authorization: "Bearer ${API_TOKEN}"  # 支持环境变量替换

# AI/Agent 相关配置
ai:
  default_model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30

# 流式响应配置
streaming:
  chunk_size: 1024
  default_format: "json"
  max_buffer_size: 10485760  # 10MB

# 重试配置
retry:
  enabled: true
  max_retries: 3
  backoff_factor: 0.3
  status_codes: [500, 502, 503, 504]

# 并发配置
concurrency:
  max_workers: 10
  timeout: 300
```

### 配置使用示例

```python
from apitestkit.core.config import global_config

# 基本配置操作
print(global_config.get('log_level'))  # 获取配置
global_config.set('base_url', 'https://api.example.com')  # 设置配置

# 嵌套配置访问
global_config.set('ai.temperature', 0.5)  # 设置嵌套配置
print(global_config.get('ai.default_model'))  # 获取嵌套配置

# 加载配置文件
global_config.load_config('config.yaml')  # 加载 YAML 文件
global_config.load_config('config.json')  # 加载 JSON 文件

# 加载默认配置链（default -> {env} -> local）
global_config.load_default_configs()

# 从环境变量加载配置
global_config.from_environment(prefix='API_TEST_')

# 获取 AI 特定配置
ai_config = global_config.get_ai_config('gpt-4')
streaming_config = global_config.get_streaming_config()

# 保存配置
global_config.save_config('saved_config.yaml')
```

### 分层配置系统

apitestkit 实现了智能的分层配置加载机制：

1. **默认配置**：从 `config/default.json` 或 `config/default.yaml` 加载
2. **环境配置**：从 `config/{环境名}.json` 或 `config/{环境名}.yaml` 加载
3. **本地配置**：从 `config/local.json` 或 `config/local.yaml` 加载

环境名可通过环境变量 `API_TEST_ENV` 设置，默认为 `development`。

### 环境变量支持

- 配置文件中可使用 `${ENV_VAR}` 语法引用环境变量
- 支持通过 `API_TEST_` 前缀的环境变量直接设置配置
  - 如 `API_TEST_BASE_URL` 对应 `base_url`
  - 下划线自动转换为点号，如 `API_TEST_AI_TEMPERATURE` 对应 `ai.temperature`

## 错误处理

apitestkit提供了错误处理机制，方便捕获和处理API测试过程中的异常：

```python
try:
    api()\
        .test("错误处理测试")\
        .step("测试异常处理")\
        .get("/api/non-existent-endpoint")\
        .send()\
        .assert_status_code(200)
except Exception as e:
    # 处理异常
    print(f"测试失败: {str(e)}")
```

## 测试用例示例

### 完整的CRUD操作测试

```python
from apitestkit import api
from apitestkit.core.config import config_manager

# 配置基础URL
config_manager.set('base_url', 'https://jsonplaceholder.typicode.com')

# 创建资源
api()\
    .test("CRUD操作测试")\
    .step("创建新帖子")\
    .post("/posts")\
    .json({"title": "测试标题", "body": "测试内容", "userId": 1})\
    .send()\
    .assert_status_code(201)\
    .extract("post_id", "id")

# 读取资源
api()\
    .step("获取创建的帖子")\
    .get("/posts/{{post_id}}")\
    .send()\
    .assert_status_code(200)\
    .assert_json_path("title", "测试标题")

# 更新资源
api()\
    .step("更新帖子")\
    .put("/posts/{{post_id}}")\
    .json({"title": "更新后的标题", "body": "更新后的内容", "userId": 1})\
    .send()\
    .assert_status_code(200)\
    .assert_json_path("title", "更新后的标题")

# 删除资源
api()\
    .step("删除帖子")\
    .delete("/posts/{{post_id}}")\
    .send()\
    .assert_status_code(200)
```

## 开发和扩展

### 自定义断言

可以扩展ResponseAssertion类来添加自定义断言方法：

```python
from apitestkit.core.assertions import ResponseAssertion

# 扩展断言器
class CustomAssertions(ResponseAssertion):
    def assert_response_schema(self, schema):
        # 自定义JSON Schema验证
        import jsonschema
        jsonschema.validate(self.response.json(), schema)
        return self
```

### 自定义中间件

可以通过装饰器添加自定义中间件处理请求和响应：

```python
from apitestkit.core.decorators import request_middleware

@request_middleware
def add_custom_header(request):
    # 在请求发送前添加自定义头部
    request.headers['X-Custom-Header'] = 'custom-value'
    return request
```

### Agent接口参数模板

可以创建和使用Agent接口参数模板，提高测试效率：

```python
# 创建参数模板
ai_api()\
    .agent_params_template("qa_model", {\
        "model": "gpt-3.5-turbo",\
        "temperature": 0.5,\
        "max_tokens": 200\
    })\
    .agent_params_template("creative_model", {\
        "model": "gpt-4",\
        "temperature": 0.9,\
        "max_tokens": 500\
    })

# 使用参数模板
ai_api()\
    .use_agent_template("qa_model")\
    .ai_prompt("什么是API测试？")
```

## 总结

apitestkit提供了一个简单易用但功能强大的API测试工具包，适用于各种规模的API测试项目。通过链式调用API设计，使测试代码更加简洁易读；丰富的断言功能和变量提取机制，满足各种测试场景的需求。

## 许可证

MIT License