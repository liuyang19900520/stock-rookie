#!/usr/bin/env python3
"""
测试优化后的API调用
"""

import logging
from data_fetcher import FMPStockDataFetcher

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_optimized_fetcher():
    """测试优化后的数据获取器"""
    try:
        print("🚀 测试优化后的数据获取器...")
        fetcher = FMPStockDataFetcher()
        
        print("📊 获取AAPL数据...")
        data = fetcher.get_stock_data("AAPL")
        
        if data:
            print("✅ 数据获取成功")
            print(f"   Ticker: {data.get('ticker')}")
            print(f"   公司信息: {len(data.get('company_info', {}))} 个字段")
            print(f"   财务指标: {len(data.get('financial_metrics', {}))} 个字段")
            
            # 显示一些关键信息
            company_info = data.get('company_info', {})
            if company_info:
                print(f"   公司名称: {company_info.get('company_name')}")
                print(f"   行业: {company_info.get('industry')}")
            
            financial_metrics = data.get('financial_metrics', {})
            if financial_metrics:
                print(f"   PE比率: {financial_metrics.get('pe_ratio')}")
                print(f"   ROE: {financial_metrics.get('roe')}")
        else:
            print("❌ 数据获取失败")
            print("💡 可能是API限制，请等待几分钟后再试")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_fetcher()
