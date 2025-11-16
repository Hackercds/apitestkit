# API参考文档

本文档提供了ApiTestKit框架的完整API参考，帮助开发者了解如何使用框架的各种功能和类。

## 1. 核心API

### 1.1 `api()` 函数

这是框架的主要入口点，用于创建API测试实例。

**签名：**
```python
def api():
    """创建并返回一个新的API测试实例"""
    return ApiAdapter()
```

**用法：**
```python
from apitestkit import api
response = api().get("https://api.example.com").send()
```

## 2. ApiAdapter 类

### 2.1 基本请求方法

#### 2.1.1 `test(name)`

设置测试名称。

**参数：**
- `name` (str): 测试的名称

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.2 `get(url)`

设置GET请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.3 `post(url)`

设置POST请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.4 `put(url)`

设置PUT请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.5 `delete(url)`

设置DELETE请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.6 `patch(url)`

设置PATCH请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.7 `head(url)`

设置HEAD请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.1.8 `options(url)`

设置OPTIONS请求。

**参数：**
- `url` (str): 请求的URL

**返回值：** ApiAdapter实例（用于链式调用）

### 2.2 请求配置方法

#### 2.2.1 `headers(headers_dict)`

设置请求头。

**参数：**
- `headers_dict` (dict): 请求头字典

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.2 `params(params_dict)`

设置URL查询参数。

**参数：**
- `params_dict` (dict): 查询参数字典

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.3 `json(json_data)`

设置JSON请求体。

**参数：**
- `json_data` (dict/list): JSON数据

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.4 `data(form_data)`

设置表单数据。

**参数：**
- `form_data` (dict): 表单数据

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.5 `files(files_dict)`

设置文件上传。

**参数：**
- `files_dict` (dict): 文件字典，格式为 `{'file': open('file.txt', 'rb')}`

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.6 `timeout(seconds)`

设置请求超时时间。

**参数：**
- `seconds` (int/float): 超时时间（秒）

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.7 `verify(verify_ssl)`

设置是否验证SSL证书。

**参数：**
- `verify_ssl` (bool): 是否验证SSL

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.2.8 `cookies(cookies_dict)`

设置请求Cookie。

**参数：**
- `cookies_dict` (dict): Cookie字典

**返回值：** ApiAdapter实例（用于链式调用）

### 2.3 执行和处理方法

#### 2.3.1 `send()`

发送请求并返回响应。

**返回值：** Response对象

#### 2.3.2 `stream()`

启用流式响应处理。

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.3.3 `callback(callback_func, context=None)`

设置流式响应的回调函数。

**参数：**
- `callback_func` (callable): 回调函数，接收chunk和context参数
- `context` (dict, 可选): 上下文对象，用于在回调之间共享数据

**返回值：** ApiAdapter实例（用于链式调用）

#### 2.3.4 `set_var(name, value)`

设置会话变量。

**参数：**
- `name` (str): 变量名称
- `value` (any): 变量值

**返回值：** ApiAdapter实例（用于链式调用）

### 2.4 断言方法

#### 2.4.1 `assert_status_code(status_code)`

断言响应状态码。

**参数：**
- `status_code` (int): 期望的状态码

**返回值：** Response对象（用于链式调用）

#### 2.4.2 `assert_json_path(path, expected_value=None)`

断言JSON路径的值。

**参数：**
- `path` (str): JSON路径，支持通配符
- `expected_value` (any, 可选): 期望的值

**返回值：** Response对象（用于链式调用）

#### 2.4.3 `assert_json_path_exists(path)`

断言JSON路径存在。

**参数：**
- `path` (str): JSON路径

**返回值：** Response对象（用于链式调用）

#### 2.4.4 `assert_json_path_not_exists(path)`

断言JSON路径不存在。

**参数：**
- `path` (str): JSON路径

**返回值：** Response对象（用于链式调用）

#### 2.4.5 `assert_response_time(max_time)`

断言响应时间。

**参数：**
- `max_time` (int): 最大响应时间（毫秒）

**返回值：** Response对象（用于链式调用）

#### 2.4.6 `assert_contains(text)`

断言响应包含指定文本。

**参数：**
- `text` (str): 要查找的文本

**返回值：** Response对象（用于链式调用）

#### 2.4.7 `assert_not_contains(text)`

断言响应不包含指定文本。

**参数：**
- `text` (str): 要查找的文本

**返回值：** Response对象（用于链式调用）

#### 2.4.8 `assert_regex(pattern)`

断言响应匹配正则表达式。

**参数：**
- `pattern` (str/re.Pattern): 正则表达式模式

**返回值：** Response对象（用于链式调用）

#### 2.4.9 `assert_header(header_name, expected_value=None)`

断言响应头。

**参数：**
- `header_name` (str): 头名称
- `expected_value` (str, 可选): 期望的值

**返回值：** Response对象（用于链式调用）

#### 2.4.10 `assert_custom(assertion_func, *args, **kwargs)`

使用自定义断言函数。

**参数：**
- `assertion_func` (callable): 自定义断言函数
- `*args`, `**kwargs`: 传递给断言函数的参数

**返回值：** Response对象（用于链式调用）

#### 2.4.11 `assert_all(assertions_list)`

一次执行多个断言。

**参数：**
- `assertions_list` (list): 断言列表，每个元素为元组 `(assertion_type, *args)`

**返回值：** Response对象（用于链式调用）

#### 2.4.12 `assert_schema(schema)`

使用JSON Schema验证响应。

**参数：**
- `schema` (dict): JSON Schema定义

**返回值：** Response对象（用于链式调用）

### 2.5 变量提取方法

#### 2.5.1 `extract(name, path)`

从响应中提取变量。

**参数：**
- `name` (str): 变量名称
- `path` (str): JSON路径

**返回值：** Response对象（用于链式调用）

## 3. Response 类

### 3.1 属性

#### 3.1.1 `status_code`

响应状态码。

#### 3.1.2 `headers`

响应头字典。

#### 3.1.3 `content`

原始响应内容（字节）。

#### 3.1.4 `text`

响应内容（字符串）。

#### 3.1.5 `json_data`

解析后的JSON数据。

#### 3.1.6 `elapsed`

请求耗时（timedelta对象）。

#### 3.1.7 `url`

请求的URL。

#### 3.1.8 `cookies`

响应Cookie。

### 3.2 方法

#### 3.2.1 `json()`

解析并返回JSON响应。

**返回值：** 解析后的JSON对象（dict/list）

#### 3.2.2 `time()`

返回请求耗时（毫秒）。

**返回值：** float

#### 3.2.3 `to_dict()`

将响应转换为字典。

**返回值：** dict

## 4. TestCase 类

### 4.1 基本方法

#### 4.1.1 `setup()`

测试设置方法，每个测试类执行前调用一次。

#### 4.1.2 `teardown()`

测试清理方法，每个测试类执行后调用一次。

#### 4.1.3 `set_up()`

测试方法设置，每个测试方法执行前调用。

#### 4.1.4 `tear_down()`

测试方法清理，每个测试方法执行后调用。

### 4.2 属性

#### 4.2.1 `api`

ApiAdapter实例，用于发送请求。

#### 4.2.2 `results`

测试结果集合。

## 5. TestSuite 类

### 5.1 方法

#### 5.1.1 `__init__(name)`

初始化测试套件。

**参数：**
- `name` (str): 测试套件名称

#### 5.1.2 `add_test(test_case)`

添加测试用例。

**参数：**
- `test_case` (TestCase): 测试用例实例

**返回值：** TestSuite实例（用于链式调用）

#### 5.1.3 `run()`

运行测试套件。

**返回值：** dict，包含测试结果

#### 5.1.4 `add_notifier(notifier)`

添加测试通知器。

**参数：**
- `notifier` (BaseNotifier): 通知器实例

**返回值：** TestSuite实例（用于链式调用）

## 6. Scenario 类

### 6.1 方法

#### 6.1.1 `__init__(name)`

初始化测试场景。

**参数：**
- `name` (str): 场景名称

#### 6.1.2 `add_step(name, method, url, **kwargs)`

添加测试步骤。

**参数：**
- `name` (str): 步骤名称
- `method` (str): HTTP方法
- `url` (str): 请求URL
- `**kwargs`: 其他请求参数（headers, json, data等）

**返回值：** Scenario实例（用于链式调用）

#### 6.1.3 `run()`

执行测试场景。

**返回值：** dict，包含场景执行结果

#### 6.1.4 `set_before(before_func)`

设置场景前置处理函数。

**参数：**
- `before_func` (callable): 前置处理函数

**返回值：** Scenario实例（用于链式调用）

#### 6.1.5 `set_after(after_func)`

设置场景后置处理函数。

**参数：**
- `after_func` (callable): 后置处理函数

**返回值：** Scenario实例（用于链式调用）

## 7. AgentAdapter 类

### 7.1 方法

#### 7.1.1 `__init__(base_url)`

初始化Agent适配器。

**参数：**
- `base_url` (str): Agent API基础URL

#### 7.1.2 `set_template(name, template)`

设置请求模板。

**参数：**
- `name` (str): 模板名称
- `template` (dict): 模板内容

**返回值：** AgentAdapter实例（用于链式调用）

#### 7.1.3 `chat(template, messages)`

发送聊天请求。

**参数：**
- `template` (str): 模板名称
- `messages` (list): 消息列表

**返回值：** Response对象

## 8. config_manager 模块

### 8.1 方法

#### 8.1.1 `set(key, value)`

设置配置值。

**参数：**
- `key` (str): 配置键
- `value` (any): 配置值

#### 8.1.2 `get(key, default=None)`

获取配置值。

**参数：**
- `key` (str): 配置键
- `default` (any, 可选): 默认值

**返回值：** 配置值或默认值

#### 8.1.3 `load(file_path)`

从文件加载配置。

**参数：**
- `file_path` (str): 配置文件路径

#### 8.1.4 `save(file_path)`

保存配置到文件。

**参数：**
- `file_path` (str): 配置文件路径

#### 8.1.5 `clear()`

清空配置。

## 9. assertion 模块

### 9.1 ResponseAssertion 类

#### 9.1.1 `__init__(response)`

初始化断言对象。

**参数：**
- `response` (Response): 响应对象

#### 9.1.2 `status_code(status_code)`

断言状态码。

**参数：**
- `status_code` (int): 期望的状态码

**返回值：** ResponseAssertion实例（用于链式调用）

#### 9.1.3 `json_path(path, expected_value=None)`

断言JSON路径的值。

**参数：**
- `path` (str): JSON路径
- `expected_value` (any, 可选): 期望的值

**返回值：** ResponseAssertion实例（用于链式调用）

#### 9.1.4 `response_time(max_time)`

断言响应时间。

**参数：**
- `max_time` (int): 最大响应时间（毫秒）

**返回值：** ResponseAssertion实例（用于链式调用）

#### 9.1.5 `contains(text)`

断言响应包含文本。

**参数：**
- `text` (str): 要查找的文本

**返回值：** ResponseAssertion实例（用于链式调用）

#### 9.1.6 `not_contains(text)`

断言响应不包含文本。

**参数：**
- `text` (str): 要查找的文本

**返回值：** ResponseAssertion实例（用于链式调用）

#### 9.1.7 `regex(pattern)`

断言响应匹配正则表达式。

**参数：**
- `pattern` (str/re.Pattern): 正则表达式模式

**返回值：** ResponseAssertion实例（用于链式调用）

#### 9.1.8 `header(header_name, expected_value=None)`

断言响应头。

**参数：**
- `header_name` (str): 头名称
- `expected_value` (str, 可选): 期望的值

**返回值：** ResponseAssertion实例（用于链式调用）

## 10. report 模块

### 10.1 ReportGenerator 类

#### 10.1.1 `__init__()`

初始化报告生成器。

#### 10.1.2 `generate(results, output_path, title=None, extra_data=None)`

生成测试报告。

**参数：**
- `results` (dict): 测试结果
- `output_path` (str): 输出路径
- `title` (str, 可选): 报告标题
- `extra_data` (dict, 可选): 额外数据

#### 10.1.3 `load_template(template_path)`

加载自定义报告模板。

**参数：**
- `template_path` (str): 模板文件路径

### 10.2 ChartsGenerator 类

#### 10.2.1 `__init__()`

初始化图表生成器。

#### 10.2.2 `generate_performance_chart(results, output_path, title=None)`

生成性能测试图表。

**参数：**
- `results` (dict): 性能测试结果
- `output_path` (str): 输出路径
- `title` (str, 可选): 图表标题

#### 10.2.3 `generate_performance_report(results, output_path)`

生成性能测试HTML报告。

**参数：**
- `results` (dict): 性能测试结果
- `output_path` (str): 输出路径

## 11. core 模块

### 11.1 DataGenerator 类

#### 11.1.1 `__init__()`

初始化数据生成器。

#### 11.1.2 `username()`

生成用户名。

**返回值：** str

#### 11.1.3 `email()`

生成电子邮件地址。

**返回值：** str

#### 11.1.4 `phone_number()`

生成电话号码。

**返回值：** str

#### 11.1.5 `address()`

生成地址。

**返回值：** str

#### 11.1.6 `date_of_birth(min_age=18, max_age=65)`

生成出生日期。

**参数：**
- `min_age` (int): 最小年龄
- `max_age` (int): 最大年龄

**返回值：** str

### 11.2 BaseNotifier 类

#### 11.2.1 `notify(results)`

发送通知。

**参数：**
- `results` (dict): 测试结果

### 11.3 EmailNotifier 类

#### 11.3.1 `__init__(smtp_server, smtp_port, username, password, recipients)`

初始化邮件通知器。

**参数：**
- `smtp_server` (str): SMTP服务器
- `smtp_port` (int): SMTP端口
- `username` (str): SMTP用户名
- `password` (str): SMTP密码
- `recipients` (list): 收件人列表

#### 11.3.2 `notify(results)`

发送邮件通知。

**参数：**
- `results` (dict): 测试结果

## 12. security 模块

### 12.1 SecurityChecker 类

#### 12.1.1 `__init__()`

初始化安全检查器。

#### 12.1.2 `check(response, checks=None)`

执行安全检查。

**参数：**
- `response` (Response): 响应对象
- `checks` (list, 可选): 要执行的检查列表

**返回值：** dict，包含检查结果