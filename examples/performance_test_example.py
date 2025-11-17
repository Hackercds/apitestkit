#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试功能使用示例

本示例展示了如何使用 apitestkit 框架的性能测试功能，包括：
1. TPS 测试
2. QPS 测试  
3. 并发测试
4. 爬坡测试
5. 盲顺序调用与性能测试结合
"""

import time
import json
from apitestkit import api


def print_separator(title):
    """打印分隔线，用于分隔不同的测试场景"""
    print("\n" + "=" * 80)
    print(f"{title:^80}")
    print("=" * 80)


def print_test_summary(metrics):
    """打印测试结果摘要"""
    print("\n测试结果摘要:")
    print(f"  平均响应时间: {metrics['avg_response_time']:.2f}ms")
    print(f"  最小响应时间: {metrics['min_response_time']:.2f}ms")
    print(f"  最大响应时间: {metrics['max_response_time']:.2f}ms")
    print(f"  50%响应时间: {metrics['p50_response_time']:.2f}ms")
    print(f"  90%响应时间: {metrics['p90_response_time']:.2f}ms")
    print(f"  95%响应时间: {metrics['p95_response_time']:.2f}ms")
    print(f"  99%响应时间: {metrics['p99_response_time']:.2f}ms")
    print(f"  错误率: {metrics['error_rate']:.2f}%")
    print(f"  吞吐量: {metrics['throughput']:.2f} req/s")
    print(f"  总请求数: {metrics['total_requests']}")
    print(f"  成功请求: {metrics['successful_requests']}")
    print(f"  失败请求: {metrics['failed_requests']}")


def test_tps():
    """示例1: TPS (每秒事务数) 测试"""
    print_separator("示例1: TPS 测试")
    
    print("配置TPS测试，目标每秒50个事务，持续30秒...")
    
    # 创建TPS测试
    result = api().get("https://httpbin.org/get")\
        .headers({"X-Test": "TPS-Test"})\
        .performance()\
        .tps(target_tps=50, duration=30)\
        .with_timeout(10)\
        .run()
    
    # 打印结果摘要
    print_test_summary(result.metrics)
    
    # 生成JSON格式的报告
    json_report = result.generate_report(format="json")
    print("\n生成JSON报告示例:")
    # 只打印部分报告内容
    report_data = json.loads(json_report)
    print(json.dumps({"test_name": report_data.get("test_name"), "metrics": report_data.get("metrics")}, indent=2))


def test_qps():
    """示例2: QPS (每秒查询数) 测试"""
    print_separator("示例2: QPS 测试")
    
    print("配置QPS测试，目标每秒100个查询，持续20秒...")
    
    # 创建QPS测试
    result = api().post("https://httpbin.org/post")\
        .json({"query": "test_data", "page": 1, "limit": 10})\
        .performance()\
        .qps(target_qps=100, duration=20)\
        .with_ramp_up(5)\
        .run()
    
    # 打印结果摘要
    print_test_summary(result.metrics)


def test_concurrent():
    """示例3: 并发用户测试"""
    print_separator("示例3: 并发用户测试")
    
    print("配置并发测试，模拟30个并发用户，持续45秒...")
    
    # 创建并发测试
    result = api().get("https://httpbin.org/delay/1")\
        .performance()\
        .concurrent(concurrent_users=30, duration=45)\
        .with_error_threshold(1)\
        .run()
    
    # 打印结果摘要
    print_test_summary(result.metrics)
    
    # 生成文本格式报告
    text_report = result.generate_report(format="text")
    print("\n文本格式报告:")
    print(text_report)


def test_ramp_up():
    """示例4: 爬坡测试"""
    print_separator("示例4: 爬坡测试")
    
    print("配置爬坡测试，从5个用户开始，逐步增加到50个用户...")
    
    # 创建爬坡测试
    result = api().put("https://httpbin.org/put")\
        .data({"update_field": "test_value"})\
        .performance()\
        .ramp_up(
            start_users=5,      # 起始用户数
            target_users=50,    # 目标用户数
            ramp_up_time=60,    # 爬坡时间（秒）
            hold_time=30        # 达到目标后保持时间（秒）
        )\
        .run()
    
    # 打印结果摘要
    print_test_summary(result.metrics)
    
    # 生成HTML报告（如果需要）
    # result.generate_report(format="html", output_path="./reports")


def test_advanced_features():
    """示例5: 高级功能 - 自定义断言和详细配置"""
    print_separator("示例5: 高级功能")
    
    print("配置高级性能测试，包含自定义断言...")
    
    # 自定义断言函数
    def custom_assertion(response):
        """检查响应状态码和响应体"""
        return response.status_code == 200 and "url" in response.text
    
    # 创建高级配置的性能测试
    result = api().delete("https://httpbin.org/delete")\
        .headers({"Authorization": "Bearer test_token"})\
        .performance()\
        .tps(target_tps=20, duration=15)\
        .with_timeout(15)\
        .with_ramp_up(3)\
        .with_error_threshold(0.5)\
        .with_assertions(custom_assertion)\
        .run()
    
    # 打印结果摘要
    print_test_summary(result.metrics)


def test_blind_order_with_performance():
    """示例6: 盲顺序调用与性能测试结合"""
    print_separator("示例6: 盲顺序调用与性能测试结合")
    
    print("使用盲顺序调用模式创建请求链...")
    
    # 创建API实例并启用盲顺序调用
    test_api = api().enable_blind_order()
    
    # 创建请求链（登录 -> 获取用户信息 -> 获取订单列表）
    print("创建请求链: 登录 -> 获取用户信息 -> 获取订单列表")
    
    # 登录请求
    test_api.post("https://httpbin.org/post")\
        .json({"username": "test_user", "password": "test_pass"})\
        .step_name("登录")\
        .queue_request()
    
    # 获取用户信息请求
    test_api.get("https://httpbin.org/get?user=123")\
        .step_name("获取用户信息")\
        .queue_request()
    
    # 获取订单列表请求
    test_api.get("https://httpbin.org/get?orders=true")\
        .step_name("获取订单列表")\
        .queue_request()
    
    # 执行请求链
    print("\n执行请求链...")
    test_api.execute_queue()
    
    # 对关键步骤进行性能测试
    print("\n对'获取订单列表'步骤进行性能测试...")
    performance_result = api().get("https://httpbin.org/get?orders=true")\
        .performance()\
        .tps(target_tps=15, duration=10)\
        .run()
    
    # 打印性能测试结果
    print_test_summary(performance_result.metrics)


def test_scenario_performance():
    """示例7: 完整场景性能测试"""
    print_separator("示例7: 完整场景性能测试")
    
    # 记录开始时间
    start_time = time.time()
    
    print("执行完整的场景性能测试流程...")
    print("步骤1: 执行预热测试")
    
    # 1. 预热测试
    warmup = api().get("https://httpbin.org/get?warmup=true")\
        .performance()\
        .concurrent(concurrent_users=10, duration=10)\
        .run()
    
    print(f"预热完成，平均响应时间: {warmup.metrics['avg_response_time']:.2f}ms")
    
    print("\n步骤2: 执行基准测试")
    # 2. 基准测试（正常负载）
    baseline = api().get("https://httpbin.org/get?baseline=true")\
        .performance()\
        .concurrent(concurrent_users=20, duration=30)\
        .run()
    
    print(f"基准测试完成，平均响应时间: {baseline.metrics['avg_response_time']:.2f}ms")
    
    print("\n步骤3: 执行压力测试")
    # 3. 压力测试（高负载）
    stress = api().get("https://httpbin.org/get?stress=true")\
        .performance()\
        .tps(target_tps=100, duration=20)\
        .run()
    
    print(f"压力测试完成，错误率: {stress.metrics['error_rate']:.2f}%")
    
    # 记录结束时间
    end_time = time.time()
    
    print("\n=== 场景测试总结 ===")
    print(f"总测试时间: {end_time - start_time:.2f}秒")
    print(f"基准性能 - 平均响应时间: {baseline.metrics['avg_response_time']:.2f}ms")
    print(f"压力测试 - 最大吞吐量: {stress.metrics['throughput']:.2f} req/s")
    print(f"压力测试 - 95%响应时间: {stress.metrics['p95_response_time']:.2f}ms")


if __name__ == "__main__":
    print("apitestkit 性能测试功能示例\n")
    
    try:
        # 运行各个测试示例
        test_tps()
        test_qps()
        test_concurrent()
        test_ramp_up()
        test_advanced_features()
        test_blind_order_with_performance()
        test_scenario_performance()
        
        print_separator("所有测试完成")
        print("\n请参考 'apitestkit/docs/performance_testing_guide.md' 获取详细使用说明。")
        
    except Exception as e:
        print(f"\n测试执行过程中发生错误: {str(e)}")
        print("请检查网络连接或目标服务器是否可用。")