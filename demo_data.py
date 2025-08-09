#!/usr/bin/env python3
"""
演示数据模块 - 提供模拟股票数据用于测试和演示
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import random

def get_demo_stock_data(ticker: str) -> Dict[str, Any]:
    """
    生成演示用的股票数据
    
    Args:
        ticker: 股票代码
        
    Returns:
        模拟的完整股票数据
    """
    
    # 生成模拟价格数据（过去30天）
    price_data = []
    base_price = 150.0  # 基础价格
    current_date = datetime.now()
    
    for i in range(30):
        date = current_date - timedelta(days=i)
        # 模拟价格波动
        price_change = random.uniform(-0.05, 0.05)  # ±5% 波动
        open_price = base_price * (1 + price_change)
        high_price = open_price * (1 + random.uniform(0, 0.03))
        low_price = open_price * (1 - random.uniform(0, 0.03))
        close_price = open_price * (1 + random.uniform(-0.02, 0.02))
        volume = random.randint(1000000, 10000000)
        
        price_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
    
    # 按日期排序（最早的在前）
    price_data.reverse()
    
    # 模拟公司信息
    company_info = {
        "symbol": ticker,
        "name": f"{ticker} Corporation",
        "sector": "Technology",
        "industry": "Software",
        "country": "United States",
        "city": "Cupertino",
        "website": f"https://www.{ticker.lower()}.com",
        "business_summary": f"{ticker} is a leading technology company that designs and manufactures consumer electronics, software, and online services.",
        "market_cap": 2800000000000,  # 2.8T
        "enterprise_value": 2750000000000,
        "shares_outstanding": 15000000000,
        "float_shares": 14500000000,
        "full_time_employees": 150000,
        "first_trade_date": 345600000,
        "currency": "USD",
        "exchange": "NASDAQ",
        "quote_type": "EQUITY",
        "timezone": "America/New_York"
    }
    
    # 模拟财务指标
    financial_metrics = {
        # 盈利能力指标
        "return_on_equity": 0.25,
        "return_on_assets": 0.15,
        "gross_margins": 0.42,
        "profit_margins": 0.21,
        "operating_margins": 0.28,
        "ebitda_margins": 0.32,
        
        # 成长性指标
        "earnings_growth": 0.08,
        "revenue_growth": 0.12,
        "earnings_quarterly_growth": 0.06,
        "revenue_quarterly_growth": 0.09,
        "trailing_eps": 6.15,
        "forward_eps": 6.75,
        
        # 偿债能力指标
        "debt_to_equity": 0.35,
        "current_ratio": 1.8,
        "quick_ratio": 1.5,
        "interest_coverage": 12.5,
        "total_debt": 120000000000,
        "total_cash": 180000000000,
        "total_cash_per_share": 12.0,
        
        # 估值指标
        "trailing_pe": 24.5,
        "forward_pe": 22.3,
        "price_to_book": 6.2,
        "price_to_sales_trailing_12months": 5.8,
        "enterprise_to_revenue": 5.5,
        "enterprise_to_ebitda": 17.2,
        "peg_ratio": 2.1,
        "dividend_yield": 0.015,
        "dividend_rate": 0.92,
        "payout_ratio": 0.15,
        
        # 现金流指标
        "operating_cashflow": 95000000000,
        "free_cashflow": 85000000000,
        "levered_free_cashflow": 80000000000,
        "total_revenue": 480000000000,
        "ebitda": 125000000000,
        "net_income_to_common": 98000000000,
        
        # 其他重要指标
        "beta": 1.15,
        "52_week_high": 180.50,
        "52_week_low": 135.20,
        "50_day_average": 165.30,
        "200_day_average": 158.75,
        "average_volume": 45000000,
        "average_volume_10days": 52000000,
        "book_value": 24.50,
        "price_to_earnings_growth": 2.1,
        "held_percent_institutions": 0.62,
        "held_percent_insiders": 0.08,
        "short_ratio": 1.2,
        "short_percent_of_float": 0.03
    }
    
    return {
        "price_data": price_data,
        "company_info": company_info,
        "financial_metrics": financial_metrics,
        "data_source": "demo",
        "note": "这是演示数据，非真实股票数据"
    }

if __name__ == "__main__":
    # 测试演示数据生成
    demo_data = get_demo_stock_data("DEMO")
    print(f"生成了 {len(demo_data['price_data'])} 天的价格数据")
    print(f"公司名称: {demo_data['company_info']['name']}")
    print(f"市值: ${demo_data['company_info']['market_cap']:,}")
