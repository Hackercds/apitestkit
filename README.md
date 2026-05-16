# apitestkit - API自动化测试框架

一个功能强大、易于使用的API自动化测试框架，提供全面的API测试解决方案，支持复杂的测试场景和报告生成。**现已支持 Agent/MCP 集成调用**。

## 功能特性

- 简洁易用的API请求接口，支持链式调用
- 强大的断言系统，支持多种断言方式
- 灵活的配置管理，支持JSON/YAML配置文件
- 完善的日志记录和敏感数据过滤
- 丰富的报告生成功能（HTML/PDF/JSON/CSV/Excel）
- 支持数据提取和变量替换
- **支持 Agent/MCP 集成**，可通过标准化工具协议调用
- 跨平台兼容性，支持Windows、Linux、macOS

## 安装

### 从PyPI安装（推荐）

```bash
pip install apitestkit
```

### 从源码安装

```bash
git clone https://github.com/Hackercds/apitestkit.git
cd apitestkit
pip install -r requirements.txt
pip install -e .
```

## 快速开始

### 基本使用示例

```python
from apitestkit import api

# 发送GET请求并断言
result = (
    api()
    .test("获取用户信息")
    .get("https://jsonplaceholder.typicode.com/users/1")
    .send()
    .assert_status_code(200)
    .assert_json_path("name", "Leanne Graham")
    .extract("email", "email")  # 提取变量供后续使用
)
```

### 使用 ApiAdapter 直接请求

```python
from apitestkit import ApiAdapter

adapter = ApiAdapter()
response = adapter.request(
    method="GET",
    url="https://jsonplaceholder.typicode.com/posts/1"
)
print(response.status_code)
print(response.json())
```

### 变量提取与引用

```python
from apitestkit import api

# 创建资源并提取ID
api()\
    .test("CRUD操作测试")\
    .step("创建新帖子")\
    .post("https://jsonplaceholder.typicode.com/posts")\
    .json({"title": "测试标题", "body": "测试内容", "userId": 1})\
    .send()\
    .assert_status_code(201)\
    .extract("post_id", "id")

# 使用提取的变量
api()\
    .step("获取帖子详情")\
    .get("https://jsonplaceholder.typicode.com/posts/{{post_id}}")\
    .send()\
    .assert_status_code(200)
```

## Agent / MCP 集成

apitestkit 提供标准化的 MCP 工具协议，支持被 Agent 或 MCP 服务器调用。

### MCP 工具调用示例

```python
from apitestkit.mcp import get_mcp_protocol, list_mcp_tools, call_mcp_tool

# 列出所有可用工具
tools = list_mcp_tools()
print(tools)

# 调用 HTTP GET 工具
result = call_mcp_tool(
    "http_get",
    url="https://jsonplaceholder.typicode.com/users/1"
)
print(result.to_dict())

# 调用断言工具
result = call_mcp_tool(
    "assert",
    actual="hello",
    expected="hello",
    assertion_type="equals"
)
print(result.to_dict())
```

### MCP 工具列表

| 工具名 | 描述 | 分类 |
|--------|------|------|
| http_get | 发送HTTP GET请求 | http |
| http_post | 发送HTTP POST请求 | http |
| http_put | 发送HTTP PUT请求 | http |
| http_delete | 发送HTTP DELETE请求 | http |
| assert | 执行断言验证 | assertion |
| config_get | 获取配置值 | config |
| config_set | 设置配置值 | config |
| data_save | 保存数据到存储 | data |
| data_get | 从存储获取数据 | data |

### MCP 协议响应格式

所有工具返回统一的 `ToolResponse` 格式：

```python
{
    "success": true,                    # 是否完全成功
    "status": "success",               # SUCCESS/FAILURE/PARTIAL
    "tool_name": "http_get",            # 调用的工具名
    "message": "GET请求成功",           # 人类可读的消息
    "data": {...},                      # 工具返回的数据
    "error": null                       # 错误信息（如果失败）
}
```

### 导入方式

```python
# 方式1: 从包级别导入（MCP相关默认try-import，失败不报错）
import apitestkit
print(apitestkit._mcp_available)  # True/False

# 方式2: 直接从mcp模块导入
from apitestkit.mcp import MCPToolProtocol, get_mcp_protocol, call_mcp_tool
```

## 框架结构

```
apitestkit/
├── __init__.py          # 包初始化，导出核心组件
├── adapter/             # 适配器层
│   ├── __init__.py
│   ├── api_adapter.py   # API适配器（链式调用核心）
│   └── api_decorators.py # 装饰器（api_test, http_get等）
├── assertion/           # 断言模块
│   ├── __init__.py
│   └── assertions.py    # 断言实现（Assertions类）
├── core/                 # 核心功能模块
│   ├── __init__.py
│   ├── config.py        # 配置管理（config_manager）
│   ├── data_storage.py  # 数据存储（DataStorageManager）
│   ├── exceptions.py    # 异常定义
│   └── logger.py        # 日志管理
├── mcp/                  # MCP/Agent集成协议层
│   ├── __init__.py
│   └── tool_protocol.py # MCP工具协议实现
├── report/               # 报告模块
│   ├── __init__.py
│   ├── report_generator.py  # 报告生成器
│   └── charts_generator.py  # 图表生成器
└── test/                 # 测试框架模块
    ├── __init__.py
    └── test_runner.py    # 测试运行器（TestRunner）
```

## 核心模块

### 1. 配置管理 (ConfigManager)

```python
from apitestkit import config_manager

# 设置配置
config_manager.set('base_url', 'https://api.example.com')
config_manager.set('log_level', 'DEBUG')

# 获取配置
print(config_manager.get('base_url'))

# 从文件加载配置
config_manager.load_config('config.yaml')

# 嵌套配置
config_manager.set('ai.temperature', 0.7)
print(config_manager.get('ai.temperature'))
```

### 2. 断言功能 (Assertions)

```python
from apitestkit.assertion.assertions import Assertions

asserter = Assertions()

# 基础断言
asserter.assert_equal(1, 1, "值相等")
asserter.assert_contains("hello world", "world")
asserter.assert_is_not_none("some value")

# 响应断言
response = adapter.request("GET", "https://api.example.com/data")
asserter.assert_status_code(response, 200)
asserter.assert_json_path(response, "data.name", "expected")
```

### 3. 日志管理 (LoggerManager)

```python
from apitestkit import logger_manager

logger_manager.info("信息日志")
logger_manager.warning("警告日志")
logger_manager.error("错误日志")
logger_manager.debug("调试日志")
```

### 4. 数据存储 (DataStorageManager)

```python
from apitestkit.core.data_storage import get_data_storage

storage = get_data_storage()

# 保存数据
storage.save_data("token", "abc123", scope="session")

# 获取数据
token = storage.get_data("token", scope="session", default="")

# 清除数据
storage.clear_memory_data()
```

### 5. 测试运行器 (TestRunner)

```python
from apitestkit import TestRunner

# 创建测试套件
runner = TestRunner()

# 添加测试用例
runner.add_test_case(test_case_func)

# 运行测试
result = runner.run()

# 生成报告
report = result.generate_report()
```

### 6. 报告生成

```python
from apitestkit import ReportGenerator, generate_html_report

# 生成HTML报告
report_path = generate_html_report(results, output_dir="reports/")

# 使用报告生成器
generator = ReportGenerator(output_format="html")
report = generator.generate(results)
```

## 装饰器

### @api_test

```python
from apitestkit import api_test

@api_test(name="我的测试")
def test_example():
    api().get("https://api.example.com/data").send()
```

### @http_get / @http_post 等

```python
from apitestkit import http_get, http_post

@http_get("/users/{user_id}")
def get_user(user_id):
    pass

@http_post("/users")
def create_user(data):
    pass
```

## 配置系统

apitestkit 支持多格式配置和环境变量替换：

```yaml
# config.yaml
log_level: DEBUG
default_timeout: 60
base_url: "https://api.example.com/v1"
verify_ssl: false

# 环境变量替换
headers:
  Authorization: "Bearer ${API_TOKEN}"

# AI配置
ai:
  default_model: "gpt-4"
  temperature: 0.7
```

```python
# 加载配置
config_manager.load_config('config.yaml')

# 从环境变量加载
config_manager.from_environment(prefix='API_')

# 保存配置
config_manager.save_config('saved_config.yaml')
```

## 常见问题

### Q: 导入时提示 `ImportError`？

确保使用正确的导入路径：
```python
# 正确
from apitestkit import api, ApiAdapter
from apitestkit import config_manager
from apitestkit.assertion.assertions import Assertions

# 错误（文档与代码不一致，已修正）
# from apitestkit.request.http_client import http_client  # 不存在
# from apitestkit.core.assertions import assertions        # 路径错误
```

### Q: MCP工具不可用？

MCP模块默认懒加载，如果失败不会影响主框架：
```python
import apitestkit
print(apitestkit._mcp_available)  # 检查MCP是否可用
```

### Q: 如何自定义断言？

```python
from apitestkit.assertion.assertions import Assertions

class CustomAssertions(Assertions):
    def assert_custom(self, actual, expected):
        if actual != expected:
            raise AssertionException(
                f"自定义断言失败: {actual} != {expected}",
                assertion_type="custom",
                expected=expected,
                actual=actual
            )
```

## 许可证

MIT License