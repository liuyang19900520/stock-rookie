#!/usr/bin/env python3
"""
API演示脚本
展示评分系统的完整功能
"""

import requests
import json


def demo_scoring_api():
    """演示评分API功能"""
    base_url = "http://localhost:8000"
    
    print("=== 股票评分系统API演示 ===\n")
    
    # 1. 检查配置
    print("1. 检查可用配置:")
    response = requests.get(f"{base_url}/v1/scoring/configs")
    if response.status_code == 200:
        configs = response.json()
        for config in configs['configs']:
            print(f"   - {config['name']}: {config['stock']} ({config['version']})")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 2. 获取BK配置详情
    print("2. BK配置详情:")
    response = requests.get(f"{base_url}/v1/scoring/config/bk.json")
    if response.status_code == 200:
        config = response.json()
        print(f"   股票: {config['meta']['stock']}")
        print(f"   版本: {config['meta']['scoring_version']}")
        print(f"   指标数量: {config['indicators_count']}")
        print(f"   权重分配:")
        for category, weight in config['weights'].items():
            print(f"     - {category}: {weight}%")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 3. 对BK进行基础评分
    print("3. BK基础评分:")
    response = requests.post(
        f"{base_url}/v1/scoring/score",
        json={"symbol": "BK"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   总分: {result['total_score']:.1f}")
        print(f"   评级: {result['rating']}")
        print(f"   建议: {result['advice']}")
        print(f"   类别分数:")
        for category, score in result['category_scores'].items():
            print(f"     - {category}: {score:.1f}")
        print(f"   警告数量: {len(result['meta']['warnings'])}")
    else:
        print(f"   错误: {response.status_code} - {response.text}")
    print()
    
    # 4. 对BK进行带overrides的评分
    print("4. BK评分（带数字资产overrides）:")
    scoring_request = {
        "symbol": "BK",
        "overrides": {
            "stablecoin_custody": ">=2_major",
            "tokenization_initiatives": 2,
            "digital_custody_maturity": "limited_clients",
            "regulatory_tailwind": "law_passed_rules_pending"
        }
    }
    
    response = requests.post(
        f"{base_url}/v1/scoring/score",
        json=scoring_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   总分: {result['total_score']:.1f}")
        print(f"   评级: {result['rating']}")
        print(f"   建议: {result['advice']}")
        print(f"   类别分数:")
        for category, score in result['category_scores'].items():
            print(f"     - {category}: {score:.1f}")
        print(f"   警告数量: {len(result['meta']['warnings'])}")
        
        # 显示成功评分的指标
        print("   成功评分的指标:")
        breakdown = result['breakdown']
        for item in breakdown:
            if item['raw'] is not None:
                print(f"     - {item['id']}: {item['score']:.1f} (raw: {item['raw']})")
    else:
        print(f"   错误: {response.status_code} - {response.text}")
    print()
    
    # 5. 批量评分
    print("5. 批量评分 (BK, AAPL, MSFT):")
    batch_request = {
        "symbols": ["BK", "AAPL", "MSFT"],
        "overrides": {
            "stablecoin_custody": ">=2_major",
            "tokenization_initiatives": 2,
            "digital_custody_maturity": "limited_clients",
            "regulatory_tailwind": "law_passed_rules_pending"
        }
    }
    
    response = requests.post(
        f"{base_url}/v1/scoring/batch-score",
        json=batch_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   总股票数: {result['total_symbols']}")
        print(f"   成功: {result['successful_symbols']}")
        print(f"   失败: {result['failed_symbols']}")
        print("   详细结果:")
        for item in result['results']:
            if item['success']:
                print(f"     - {item['symbol']}: {item['total_score']:.1f} ({item['rating']})")
            else:
                print(f"     - {item['symbol']}: 失败 - {item['error']}")
    else:
        print(f"   错误: {response.status_code} - {response.text}")
    print()
    
    print("=== 演示完成 ===")
    print("\n您可以在浏览器中访问以下地址:")
    print(f"  - API文档: {base_url}/docs")
    print(f"  - ReDoc文档: {base_url}/redoc")
    print(f"  - 健康检查: {base_url}/health")


if __name__ == "__main__":
    try:
        demo_scoring_api()
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
