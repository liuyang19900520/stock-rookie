#!/usr/bin/env python3
"""
评分系统演示脚本
展示完整的评分功能
"""

import requests
import json
from typing import Dict, Any


def demo_scoring_api():
    """演示评分API功能"""
    base_url = "http://localhost:8000"
    
    print("=== 股票评分系统演示 ===\n")
    
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
    
    # 3. 对BK进行评分
    print("3. BK股票评分:")
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
        print(f"   触发规则: {result['triggered']}")
        print(f"   警告: {len(result['meta']['warnings'])} 个")
    else:
        print(f"   错误: {response.status_code} - {response.text}")
    print()
    
    # 4. 批量评分
    print("4. 批量评分 (BK, AAPL, MSFT):")
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
    
    # 5. 展示评分明细
    print("5. BK评分明细 (前10个指标):")
    response = requests.post(
        f"{base_url}/v1/scoring/score",
        json={"symbol": "BK"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        breakdown = result['breakdown']
        
        # 按分数排序
        sorted_breakdown = sorted(breakdown, key=lambda x: x['score'], reverse=True)
        
        print("   高分指标:")
        for i, item in enumerate(sorted_breakdown[:5]):
            print(f"     - {item['id']}: {item['score']:.1f} (raw: {item['raw']})")
        
        print("   低分指标:")
        for i, item in enumerate(sorted_breakdown[-5:]):
            print(f"     - {item['id']}: {item['score']:.1f} (raw: {item['raw']})")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    print("=== 演示完成 ===")


def demo_scoring_logic():
    """演示评分逻辑"""
    print("=== 评分逻辑演示 ===\n")
    
    # 直接使用评分模块
    from app.core.scoring import load_config, score_stock
    
    # 加载配置
    config = load_config('app/config/bk.json')
    
    # 测试不同场景
    test_cases = [
        {
            "name": "优秀银行",
            "inputs": {
                "roe": 16.0, "cet1Ratio": 12.0, "lcr": 120, "nsfr": 125,
                "dividendYieldTTM": 4.0, "payoutRatio": 40,
                "priceToBookTTM": 1.0, "pb": 1.0,
                "netInterestIncomeYoY": 8.0, "feeRevenueYoY": 6.0,
                "assetsUnderCustodyAdminYoY": 5.0,
                "beta": 0.8, "realizedVol180d": 15.0,
                "epsNext12mRevisionPct": 3.0,
                "maxDrawdown180dPct": 10.0
            }
        },
        {
            "name": "一般银行",
            "inputs": {
                "roe": 12.0, "cet1Ratio": 10.5, "lcr": 105, "nsfr": 110,
                "dividendYieldTTM": 2.5, "payoutRatio": 50,
                "priceToBookTTM": 1.2, "pb": 1.2,
                "netInterestIncomeYoY": 2.0, "feeRevenueYoY": 1.0,
                "assetsUnderCustodyAdminYoY": 1.0,
                "beta": 1.1, "realizedVol180d": 25.0,
                "epsNext12mRevisionPct": -1.0,
                "maxDrawdown180dPct": 20.0
            }
        }
    ]
    
    peers = {
        "pb": [1.20, 1.10, 1.05],
        "auc_growth": [2.1, 3.8, 1.5],
        "pretax_margin": [0.29, 0.31, 0.27]
    }
    
    overrides = {
        "stablecoin_custody": ">=2_major",
        "tokenization_initiatives": 2,
        "digital_custody_maturity": "limited_clients",
        "regulatory_tailwind": "law_passed_rules_pending"
    }
    
    for case in test_cases:
        print(f"{case['name']}:")
        result = score_stock(config, case['inputs'], peers, overrides)
        print(f"  总分: {result['total_score']:.1f}")
        print(f"  评级: {result['rating']}")
        print(f"  建议: {result['advice']}")
        print(f"  类别分数:")
        for category, score in result['category_scores'].items():
            print(f"    - {category}: {score:.1f}")
        print()


if __name__ == "__main__":
    try:
        demo_scoring_api()
        print("\n" + "="*50 + "\n")
        demo_scoring_logic()
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
