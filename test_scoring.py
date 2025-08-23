#!/usr/bin/env python3
"""
评分系统测试文件
测试各种评分类型和决策规则
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.scoring import load_config, score_stock, score_indicator, aggregate_scores, apply_decision_rules


def test_complete_scoring():
    """完整评分测试"""
    print("=== 完整评分测试 ===")
    
    # 加载配置
    config = load_config('app/config/bk.json')
    
    # 完整的测试输入
    inputs = {
        # 核心基本面指标
        "roe": 14.2,
        "cet1Ratio": 11.4,
        "lcr": 112,
        "nsfr": 121,
        "netInterestIncomeYoY": 6.1,
        "feeRevenueYoY": 4.0,
        "assetsUnderCustodyAdminYoY": 3.5,
        
        # 估值和回报指标
        "dividendYieldTTM": 3.2,
        "payoutRatio": 36,
        "priceToBookTTM": 1.07,
        "pb": 1.07,
        "trailing12mBuybackYield": 3.5,
        
        # 市场技术指标
        "beta": 0.95,
        "realizedVol180d": 18.5,
        "epsNext12mRevisionPct": 2.1,
        "maxDrawdown180dPct": 14.0,
        
        # 计算指标
        "pretax_income": 5000,
        "total_revenue": 15000,
    }
    
    # 同行数据
    peers = {
        "pb": [1.20, 1.10, 1.05],
        "auc_growth": [2.1, 3.8, 1.5],
        "pretax_margin": [0.29, 0.31, 0.27]
    }
    
    # 覆盖数据
    overrides = {
        "stablecoin_custody": ">=2_major",
        "tokenization_initiatives": 2,
        "digital_custody_maturity": "limited_clients",
        "regulatory_tailwind": "law_passed_rules_pending"
    }
    
    # 执行评分
    result = score_stock(config, inputs, peers, overrides)
    
    print(f"总分: {result['total_score']:.1f}")
    print(f"评级: {result['rating']}")
    print(f"建议: {result['advice']}")
    print(f"触发规则: {result['triggered']}")
    print(f"红标: {result['meta']['warnings']}")
    
    print("\n=== 类别分数 ===")
    for category, score in result['category_scores'].items():
        print(f"{category}: {score:.1f}")
    
    print("\n=== 核心指标分数 ===")
    for item in result['breakdown']:
        if item['category'] == 'core_fundamentals':
            print(f"{item['id']}: {item['score']:.1f} (raw: {item['raw']})")
    
    return result


def test_individual_scoring_types():
    """测试各种评分类型"""
    print("\n=== 评分类型测试 ===")
    
    config = load_config('app/config/bk.json')
    
    # 测试线性阈值评分
    roe_indicator = next(ind for ind in config['indicators'] if ind['id'] == 'roe')
    result = score_indicator(roe_indicator, {"roe": 15.0}, {}, {})
    print(f"ROE 15.0% -> 分数: {result['score']:.1f}")
    
    # 测试同行百分位评分
    auc_indicator = next(ind for ind in config['indicators'] if ind['id'] == 'auc_growth')
    result = score_indicator(auc_indicator, {"assetsUnderCustodyAdminYoY": 3.5}, 
                           {"auc_growth": [2.1, 3.8, 1.5]}, {})
    print(f"AUC Growth 3.5% -> 分数: {result['score']:.1f}")
    
    # 测试相对同行评分
    pb_indicator = next(ind for ind in config['indicators'] if ind['id'] == 'pb_vs_peers')
    result = score_indicator(pb_indicator, {"pb": 1.07}, {"pb": [1.20, 1.10, 1.05]}, {})
    print(f"P/B 1.07 vs peers -> 分数: {result['score']:.1f}")
    
    # 测试二维评分
    div_indicator = next(ind for ind in config['indicators'] if ind['id'] == 'dividend_yield_growth')
    result = score_indicator(div_indicator, {"dividendYieldTTM": 3.2, "payoutRatio": 36}, {}, {})
    print(f"Dividend Yield 3.2% + Payout 36% -> 分数: {result['score']:.1f}")
    
    # 测试分类评分
    stablecoin_indicator = next(ind for ind in config['indicators'] if ind['id'] == 'stablecoin_custody')
    result = score_indicator(stablecoin_indicator, {"stablecoin_custody": ">=2_major"}, {}, {})
    print(f"Stablecoin Custody >=2_major -> 分数: {result['score']:.1f}")


def test_decision_rules():
    """测试决策规则"""
    print("\n=== 决策规则测试 ===")
    
    config = load_config('app/config/bk.json')
    
    # 模拟评分明细
    breakdown = [
        {"id": "roe", "score": 90, "raw": 15.0, "category": "core_fundamentals"},
        {"id": "pb_vs_peers", "score": 85, "raw": 1.05, "category": "valuation_and_returns"},
        {"id": "tokenization_initiatives", "score": 90, "raw": 2, "category": "digital_asset_optionality"},
        {"id": "regulatory_tailwind", "score": 85, "raw": "law_passed_rules_pending", "category": "digital_asset_optionality"},
    ]
    
    category_scores = {
        "core_fundamentals": 75,
        "valuation_and_returns": 80,
        "digital_asset_optionality": 85,
        "market_technicals": 70
    }
    
    total_score = 78.5
    
    inputs = {
        "roe": 15.0,
        "pb": 1.05,
        "tokenization_initiatives": 2,
        "regulatory_tailwind": "law_passed_rules_pending"
    }
    
    decision = apply_decision_rules(config, breakdown, category_scores, total_score, inputs)
    
    print(f"评级: {decision['rating']}")
    print(f"规模: {decision['sizing']}")
    print(f"触发规则: {decision['triggered']}")
    print(f"红标: {decision['red_flags']}")


def test_edge_cases():
    """测试边界情况"""
    print("\n=== 边界情况测试 ===")
    
    config = load_config('app/config/bk.json')
    
    # 测试缺失数据
    inputs = {"roe": None}
    roe_indicator = next(ind for ind in config['indicators'] if ind['id'] == 'roe')
    result = score_indicator(roe_indicator, inputs, {}, {})
    print(f"缺失ROE数据 -> 分数: {result['score']}, 警告: {result['warnings']}")
    
    # 测试极端值
    inputs = {"roe": 25.0}  # 超出范围
    result = score_indicator(roe_indicator, inputs, {}, {})
    print(f"ROE 25% (超出范围) -> 分数: {result['score']:.1f}")
    
    # 测试零值
    inputs = {"roe": 0}
    result = score_indicator(roe_indicator, inputs, {}, {})
    print(f"ROE 0% -> 分数: {result['score']:.1f}")


if __name__ == "__main__":
    # 运行所有测试
    test_complete_scoring()
    test_individual_scoring_types()
    test_decision_rules()
    test_edge_cases()
    
    print("\n=== 测试完成 ===")
