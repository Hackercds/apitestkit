# 配置指南

本文档详细介绍ApiTestKit框架的配置选项和使用方法。

## 配置概述

ApiTestKit提供了灵活的配置管理系统，允许用户自定义框架的行为。配置可以通过多种方式设置：

1. 代码中直接设置
2. 配置文件
3. 环境变量

## 核心配置组件

框架使用`config_manager`进行配置管理，它是一个单例对象，可以在任何地方访问。

```python
from apitestkit import config_manager
```

## 配置选项

### 基本配置

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `base_url` | str | "" | API请求的基础URL |
| `timeout` | int | 30 | 请求超时时间（秒） |
| `max_retries` | int | 1 | 请求失败重试次数 |
| `retry_interval` | int | 1 | 重试间隔时间（秒） |
| `default_headers` | dict | {} | 默认请求头 |
| `ssl_verify` | bool | True | 是否验证SSL证书 |

### 日志配置

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `log_level` | str | "INFO" | 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL） |
| `log_format` | str | "%(asctime)s - %(name)s - %(levelname)s - %(message)s" | 日志格式 |
| `log_directory` | str | "./logs" | 日志文件保存目录 |
| `log_file` | str | None | 日志文件名，None表示使用默认名称 |
| `console_output` | bool | True | 是否输出到控制台 |
| `file_output` | bool | True | 是否输出到文件 |

### 报告配置

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `report_directory` | str | "./reports" | 报告保存目录 |
| `report_format` | str | "html" | 报告格式（html, json, csv, excel, pdf） |
| `report_title` | str | "API测试报告" | 报告标题 |
| `include_charts` | bool | True | 是否包含图表 |
| `auto_open_report` | bool | False | 是否自动打开报告 |

### 测试配置

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `test_parallel` | bool | False | 是否并行执行测试 |
| `test_workers` | int | 4 | 并行执行的工作线程数 |
| `test_timeout` | int | 300 | 单个测试用例超时时间（秒） |
| `stop_on_error` | bool | False | 遇到错误是否停止测试 |

## 代码中设置配置

### 设置单个配置项

```python
from apitestkit import config_manager

# 设置基础URL
config_manager.set("base_url", "https://api.example.com/v1")

# 设置超时时间
config_manager.set("timeout", 60)
```

### 获取配置项

```python
# 获取配置值
base_url = config_manager.get("base_url")
timeout = config_manager.get("timeout", 30)  # 带默认值
```

### 批量设置配置

```python
# 批量设置多个配置项
config_manager.update({
    "base_url": "https://api.example.com/v1",
    "timeout": 60,
    "max_retries": 3,
    "log_level": "DEBUG"
})
```

### 重置配置

```python
# 重置为默认配置
config_manager.reset()
```

## 使用配置文件

### 创建配置文件

可以创建一个YAML或JSON格式的配置文件。例如，创建`config.yaml`：

```yaml
# config.yaml
base_url: "https://api.example.com/v1"
timeout: 60
max_retries: 3
ssl_verify: false

log:
  level: "DEBUG"
  directory: "./test_logs"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

report:
  directory: "./test_reports"
  format: "html"
  title: "我的API测试报告"
```

### 加载配置文件

```python
import yaml
from apitestkit import config_manager

# 加载YAML配置文件
with open("config.yaml", "r", encoding="utf-8") as f:
    config_data = yaml.safe_load(f)
    
    # 扁平化配置数据并设置
    if "log" in config_data:
        for key, value in config_data["log"].items():
            config_manager.set(f"log_{key}", value)
    
    if "report" in config_data:
        for key, value in config_data["report"].items():
            config_manager.set(f"report_{key}", value)
    
    # 设置其他配置项
    for key, value in config_data.items():
        if key not in ["log", "report"]:
            config_manager.set(key, value)
```

## 使用环境变量

ApiTestKit支持通过环境变量设置配置。环境变量的命名规则为：`APITESTKIT_` + 大写配置项名。

例如：

```bash
# 设置环境变量
# Windows
export APITESTKIT_BASE_URL=https://api.example.com/v1
export APITESTKIT_TIMEOUT=60
export APITESTKIT_LOG_LEVEL=DEBUG

# Linux/MacOS
export APITESTKIT_BASE_URL=https://api.example.com/v1
export APITESTKIT_TIMEOUT=60
export APITESTKIT_LOG_LEVEL=DEBUG
```

然后在代码中：

```python
import os
from apitestkit import config_manager

# 从环境变量加载配置
config_manager.set("base_url", os.environ.get("APITESTKIT_BASE_URL", ""))
config_manager.set("timeout", int(os.environ.get("APITESTKIT_TIMEOUT", 30)))
config_manager.set("log_level", os.environ.get("APITESTKIT_LOG_LEVEL", "INFO"))
```

## 配置优先级

当通过多种方式设置同一配置项时，优先级从高到低为：

1. 代码中直接设置的值
2. 环境变量设置的值
3. 配置文件中的值
4. 默认值

## 示例：综合配置

以下是一个完整的配置示例：

```python
from apitestkit import config_manager
import yaml
import os

# 1. 加载配置文件
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
        for key, value in config_data.items():
            config_manager.set(key, value)
except FileNotFoundError:
    print("配置文件未找到，使用默认配置")

# 2. 从环境变量覆盖配置
for key in ["BASE_URL", "TIMEOUT", "LOG_LEVEL"]:
    env_key = f"APITESTKIT_{key}"
    if env_key in os.environ:
        config_manager.set(key.lower(), os.environ[env_key])

# 3. 代码中直接设置关键配置
config_manager.set("ssl_verify", False)  # 开发环境不验证SSL
config_manager.set("default_headers", {
    "Content-Type": "application/json",
    "User-Agent": "ApiTestKit/1.0.0"
})
```

## 最佳实践

1. **分离配置和代码**：将配置信息存储在单独的配置文件中
2. **使用环境变量**：敏感信息（如API密钥）应通过环境变量设置
3. **配置验证**：在使用前验证关键配置项是否正确设置
4. **不同环境配置**：为不同环境（开发、测试、生产）准备不同的配置文件

## 下一步

配置完成后，您可以参考[快速开始指南](quick_start.md)开始编写和运行测试用例。