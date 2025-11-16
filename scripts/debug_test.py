#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试测试脚本 - 用于详细排查HTTP客户端和响应断言功能的问题
"""
import sys
sys.path.append('.')

from apitestkit.request.http_client import HttpClient
from apitestkit.assertion.assertions import ResponseAssertion
import traceback
import json

def test_http_client_debug():
    """详细调试HTTP客户端功能"""
    print("\n===== 详细调试HTTP客户端 =====")
    try:
        # 创建HTTP客户端实例
        client = HttpClient()
        print("✅ HTTP客户端实例创建成功")
        
        # 测试GET请求
        print("\n正在执行GET请求...")
        response = client.get("https://httpbin.org/get")
        print(f"✅ GET请求响应状态码: {response.status_code}")
        print(f"✅ GET请求响应时间(elapsed_ms): {response.elapsed_ms}")
        print(f"✅ GET请求响应时间(response_time): {response.response_time}")
        
        # 尝试访问响应内容
        try:
            content = response.text
            print(f"✅ GET请求响应内容长度: {len(content)} 字符")
            # 尝试解析JSON
            json_data = response.json()
            print(f"✅ GET请求响应JSON解析成功，包含键: {', '.join(json_data.keys())}")
        except Exception as e:
            print(f"❌ 无法处理GET响应内容: {str(e)}")
            print(traceback.format_exc())
        
        # 测试POST请求
        print("\n正在执行POST请求...")
        data = {"test": "data"}
        response = client.post("https://httpbin.org/post", data=data)
        print(f"✅ POST请求响应状态码: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ HTTP客户端测试失败: {str(e)}")
        print("\n详细错误堆栈:")
        print(traceback.format_exc())
        return False

def test_assertion_debug():
    """详细调试响应断言功能"""
    print("\n===== 详细调试响应断言 =====")
    try:
        # 创建HTTP客户端实例并获取响应
        client = HttpClient()
        print("✅ 创建HTTP客户端实例成功")
        
        response = client.get("https://httpbin.org/get")
        print(f"✅ 获取测试响应成功，状态码: {response.status_code}")
        
        # 创建断言实例
        assertion = ResponseAssertion(response)
        print("✅ 创建响应断言实例成功")
        
        # 测试状态码断言
        print("\n测试状态码断言...")
        status_result = assertion.assert_status_code(response, 200, "eq")
        print(f"状态码断言结果: {'通过' if status_result else '失败'}")
        
        # 测试响应时间断言
        print("\n测试响应时间断言...")
        try:
            time_result = assertion.assert_response_time(response, 5.0, "lt")  # 5秒内
            print(f"响应时间断言结果: {'通过' if time_result else '失败'}")
        except Exception as e:
            print(f"❌ 响应时间断言异常: {str(e)}")
            print(traceback.format_exc())
        
        # 测试响应内容包含断言
        print("\n测试响应内容包含断言...")
        try:
            contains_result = assertion.assert_response_contains(response, "url")
            print(f"响应内容包含断言结果: {'通过' if contains_result else '失败'}")
        except Exception as e:
            print(f"❌ 响应内容包含断言异常: {str(e)}")
            print(traceback.format_exc())
        
        # 测试JSON路径断言
        print("\n测试JSON路径断言...")
        try:
            json_result = assertion.assert_json_path(response, "$.url", "httpbin.org", "contains")
            print(f"JSON路径断言结果: {'通过' if json_result else '失败'}")
        except Exception as e:
            print(f"❌ JSON路径断言异常: {str(e)}")
            print(traceback.format_exc())
        
        return True
    except Exception as e:
        print(f"❌ 断言测试失败: {str(e)}")
        print("\n详细错误堆栈:")
        print(traceback.format_exc())
        return False

def main():
    """主函数"""
    print("开始调试测试...")
    
    http_result = test_http_client_debug()
    assertion_result = test_assertion_debug()
    
    print("\n===== 调试测试结果 =====")
    print(f"HTTP客户端调试: {'通过' if http_result else '失败'}")
    print(f"响应断言调试: {'通过' if assertion_result else '失败'}")
    
    if http_result and assertion_result:
        print("\n✅ 所有调试测试通过！")
    else:
        print("\n❌ 部分调试测试失败，请查看详细错误信息。")

if __name__ == "__main__":
    main()