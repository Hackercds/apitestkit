# ApiTestKit 发布说明

## 版本 1.0.0

### 发布日期
2025-11-17

### 项目介绍
ApiTestKit 是一个功能强大的 API 测试框架，旨在简化 API 自动化测试流程，提供灵活的请求发送、响应断言和测试报告生成能力。

### 核心功能

#### 1. 灵活的 API 请求接口
- 支持所有常见 HTTP 方法（GET, POST, PUT, DELETE 等）
- 链式调用风格，简化代码编写
- 支持请求头、URL 参数、表单数据、JSON 数据等
- 内置请求重试机制和超时控制

#### 2. 强大的断言系统
- 状态码断言
- JSON 路径断言
- 正则表达式匹配断言
- 响应时间断言
- 自定义断言支持

#### 3. 完善的配置管理
- 支持配置文件（YAML, JSON）
- 环境变量覆盖配置
- 不同环境（开发、测试、生产）的配置管理
- 配置验证和默认值支持

#### 4. 测试用例和套件管理
- 基于类的测试用例定义
- 测试套件组织和运行
- 参数化测试支持
- 测试前置和后置操作

#### 5. 性能测试功能
- TPS/QPS 测试
- 并发用户测试
- 爬坡测试
- 详细的性能指标收集和报告

#### 6. 日志和报告
- 多级日志记录
- 敏感信息过滤
- 测试报告生成
- 详细的请求/响应日志

### 安装方法

#### 通过 PyPI 安装
```bash
pip install apitestkit
```

#### 从源码安装
```bash
git clone https://github.com/example/apitestkit.git
cd apitestkit
pip install -e .
```

### 快速开始

```python
from apitestkit.adapter.api_adapter import api

# 发送 GET 请求并断言
api()\
    .test("示例测试")\
    .get("https://httpbin.org/get")\
    .params({"test": "value"})\
    .send()\
    .assert_status_code(200)

# 发送 POST 请求
api()\
    .test("POST 请求测试")\
    .post("https://httpbin.org/post")\
    .json({"name": "test", "value": 123})\
    .send()\
    .assert_status_code(200)
```

### 文档

- [完整用户指南](USER_GUIDE.md)
- [架构设计文档](ARCHITECTURE_DESIGN.md)
- [配置指南](docs/configuration_guide.md)
- [性能测试指南](apitestkit/docs/performance_testing_guide.md)
- [快速开始](docs/quick_start.md)

### 依赖

- requests>=2.25.0
- pytest>=6.2.0
- jsonschema>=4.0.0
- colorama>=0.4.4
- python-dateutil>=2.8.1
- PyYAML>=6.0

### 已知问题

1. 部分测试用例可能需要针对特定环境进行调整
2. 性能测试在高并发场景下可能需要额外的系统资源
3. 某些高级断言功能可能需要更详细的文档说明

### 贡献指南

欢迎提交 Issue 和 Pull Request！请参考项目仓库中的贡献指南。

### 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。