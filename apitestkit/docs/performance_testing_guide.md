# 性能测试功能使用指南

## 概述

apitestkit 框架提供了强大的性能测试功能，支持 TPS（每秒事务数）测试、QPS（每秒查询数）测试、并发测试和爬坡测试等多种性能测试场景。通过简单易用的 API，您可以快速配置和执行各种性能测试，并获得详细的性能报告。

## 核心功能

- **TPS 测试**：测试系统在一定时间内能够处理的事务数量
- **QPS 测试**：测试系统在一定时间内能够处理的查询数量
- **并发测试**：测试系统在不同并发用户数下的性能表现
- **爬坡测试**：测试系统在逐渐增加负载情况下的性能变化趋势
- **详细报告**：生成包含响应时间、错误率、吞吐量等关键指标的测试报告

## 使用方法

### 1. 基本性能测试

```python
from apitestkit import api

# 创建一个基本的TPS测试
result = api().get("https://api.example.com/users")\
    .performance()\
    .tps(target_tps=50, duration=60)\
    .run()

# 生成报告
report = result.generate_report(format="json")
print(report)
```

### 2. QPS 测试示例

```python
from apitestkit import api

# 配置QPS测试，目标QPS为100，持续30秒
result = api().post("https://api.example.com/login")\
    .json({"username": "test", "password": "test123"})\
    .performance()\
    .qps(target_qps=100, duration=30)\
    .run()

# 生成HTML格式的报告
result.generate_report(format="html", output_path="./reports")
```

### 3. 并发测试示例

```python
from apitestkit import api

# 配置并发测试，100个并发用户，持续45秒
result = api().get("https://api.example.com/products")\
    .performance()\
    .concurrent(concurrent_users=100, duration=45)\
    .run()

# 查看测试结果摘要
print(f"平均响应时间: {result.metrics['avg_response_time']}ms")
print(f"95%响应时间: {result.metrics['p95_response_time']}ms")
print(f"错误率: {result.metrics['error_rate']}%")
```

### 4. 爬坡测试示例

```python
from apitestkit import api

# 配置爬坡测试，从10用户开始，逐步增加到100用户
result = api().delete("https://api.example.com/cache/clear")\
    .performance()\
    .ramp_up(start_users=10, target_users=100, ramp_up_time=60, hold_time=30)\
    .run()

# 生成文本格式报告
text_report = result.generate_report(format="text")
print(text_report)
```

### 5. 配置性能测试参数

```python
from apitestkit import api

# 高级配置示例
result = api().put("https://api.example.com/users/1")\
    .json({"name": "Updated User"})\
    .headers({"Authorization": "Bearer token123"})\
    .performance()\
    .tps(target_tps=50)\
    # 配置详细参数
    .with_timeout(30)  # 单个请求超时时间
    .with_ramp_up(10)  # 启动时间（秒）
    .with_error_threshold(5)  # 错误率阈值（%）
    .with_assertions(lambda resp: resp.status_code == 200)  # 自定义断言
    .run()
```

### 6. 使用盲顺序调用进行性能测试

```python
from apitestkit import api

# 使用盲顺序调用模式进行多步骤性能测试
test_api = api().enable_blind_order()

# 添加多个请求到队列
test_api.get("https://api.example.com/auth").queue_request()
test_api.post("https://api.example.com/users").json({"name": "test"}).queue_request()
test_api.get("https://api.example.com/users/1").queue_request()

# 执行队列中的所有请求
test_api.execute_queue()

# 对队列中的第一个请求进行性能测试（示例）
performance_api = api().get("https://api.example.com/auth")
perf_result = performance_api.performance().tps(target_tps=30, duration=30).run()
```

## 性能测试结果指标

性能测试运行后，您可以获取以下关键指标：

- `avg_response_time`: 平均响应时间（毫秒）
- `min_response_time`: 最小响应时间（毫秒）
- `max_response_time`: 最大响应时间（毫秒）
- `p50_response_time`: 50%响应时间（毫秒）
- `p90_response_time`: 90%响应时间（毫秒）
- `p95_response_time`: 95%响应时间（毫秒）
- `p99_response_time`: 99%响应时间（毫秒）
- `error_rate`: 错误率（百分比）
- `throughput`: 吞吐量（每秒请求数）
- `total_requests`: 总请求数
- `successful_requests`: 成功请求数
- `failed_requests`: 失败请求数

## 报告格式

框架支持生成以下格式的性能测试报告：

1. **JSON 格式**：便于程序处理和分析
2. **文本格式**：简洁易读的命令行输出
3. **HTML 格式**：包含图表和详细统计信息的可视化报告

## 最佳实践

1. **从小规模测试开始**：先使用低负载进行测试，确认系统稳定性
2. **逐步增加负载**：使用爬坡测试找出系统瓶颈
3. **设置合理的超时时间**：根据业务需求配置请求超时
4. **关注关键指标**：重点关注响应时间、错误率和吞吐量
5. **保存测试结果**：定期保存测试报告以便比较不同时期的性能变化

## 注意事项

1. 性能测试可能对被测系统造成压力，请在适当的环境中进行测试
2. 测试前确保系统已经过基本的功能测试
3. 对于长时间运行的测试，建议监控系统资源使用情况
4. 对于复杂的测试场景，可以结合盲顺序调用功能进行多步骤测试

## 示例：完整的性能测试脚本

```python
from apitestkit import api
import time

def run_performance_test():
    # 1. 预热测试
    print("执行预热测试...")
    warmup = api().get("https://api.example.com/health")\
        .performance()\
        .concurrent(concurrent_users=10, duration=30)\
        .run()
    print(f"预热完成，平均响应时间: {warmup.metrics['avg_response_time']}ms")
    
    # 2. 并发测试
    print("\n执行并发测试...")
    concurrent_test = api().get("https://api.example.com/products")\
        .performance()\
        .concurrent(concurrent_users=50, duration=60)\
        .run()
    
    # 3. 爬坡测试
    print("\n执行爬坡测试...")
    ramp_test = api().post("https://api.example.com/orders")\
        .json({"product_id": 1, "quantity": 1})\
        .performance()\
        .ramp_up(start_users=10, target_users=100, ramp_up_time=120, hold_time=60)\
        .run()
    
    # 4. 生成报告
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    concurrent_test.generate_report(format="html", output_path=f"./reports/concurrent_{timestamp}.html")
    ramp_test.generate_report(format="html", output_path=f"./reports/ramp_{timestamp}.html")
    
    # 5. 输出结果摘要
    print("\n=== 测试结果摘要 ===")
    print(f"并发测试 - 平均响应时间: {concurrent_test.metrics['avg_response_time']}ms, 错误率: {concurrent_test.metrics['error_rate']}%")
    print(f"爬坡测试 - 最大吞吐量: {ramp_test.metrics['throughput']} req/s, 95%响应时间: {ramp_test.metrics['p95_response_time']}ms")

if __name__ == "__main__":
    run_performance_test()
```

## 故障排除

1. **连接错误**：检查目标URL是否可访问，网络连接是否正常
2. **高错误率**：可能是系统负载过高或存在性能瓶颈，建议降低测试负载
3. **测试超时**：检查网络延迟或增加测试超时时间
4. **内存不足**：对于大规模测试，可能需要增加系统内存或减少并发用户数

如有其他问题，请参考框架的日志输出获取详细信息。