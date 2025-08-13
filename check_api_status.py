#!/usr/bin/env python3
"""
检查FMP API状态和限制
"""

import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_api_status():
    """检查FMP API状态"""
    api_key = os.getenv('FMP_API_KEY')
    
    if not api_key:
        print("❌ 未找到FMP_API_KEY环境变量")
        return
    
    print(f"🔑 API密钥: {api_key[:10]}...")
    
    # 测试基础端点
    test_urls = [
        f"https://financialmodelingprep.com/api/v3/profile/AAPL?apikey={api_key}",
        f"https://financialmodelingprep.com/api/v3/key-metrics/AAPL?apikey={api_key}&limit=1",
        f"https://financialmodelingprep.com/api/v3/ratios/AAPL?apikey={api_key}&limit=1"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📡 测试端点 {i}...")
        try:
            response = requests.get(url, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"   ✅ 成功获取数据，返回 {len(data)} 条记录")
                elif isinstance(data, dict):
                    print(f"   ✅ 成功获取数据")
                else:
                    print(f"   ⚠️  返回空数据")
            elif response.status_code == 429:
                print(f"   ❌ 请求限制 (429 Too Many Requests)")
                print(f"   💡 建议等待一段时间后再试")
            elif response.status_code == 401:
                print(f"   ❌ 认证失败 (401 Unauthorized)")
                print(f"   💡 请检查API密钥是否正确")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
    
    print(f"\n💡 建议:")
    print(f"   1. 如果是429错误，请等待几分钟后再试")
    print(f"   2. 如果是401错误，请检查API密钥")
    print(f"   3. 考虑升级FMP API计划以获得更高限制")

if __name__ == "__main__":
    check_api_status()
