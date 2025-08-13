import requests
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class FMPStockDataFetcher:
    """Financial Modeling Prep (FMP) 股票数据抓取器 - 简化版本"""
    
    def __init__(self):
        # API配置
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable is required")
        
        self.base_url = "https://financialmodelingprep.com/api"
        self.session = requests.Session()
        
        logger.info("FMP Stock Data Fetcher (简化版本) initialized")
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """发送API请求"""
        import time
        import random
        
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                # 增加延迟避免API限制
                delay = base_delay + random.uniform(0, 1)  # 2-3秒随机延迟
                time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 429:
                    # 遇到限制，等待更长时间
                    wait_time = (attempt + 1) * 5  # 5秒, 10秒, 15秒
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    return None
                time.sleep(base_delay * (attempt + 1))  # 递增延迟
        
        return None
    
    def _get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """获取公司基本信息"""
        url = f"{self.base_url}/v3/profile/{ticker}?apikey={self.api_key}"
        
        data = self._make_request(url)
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No company profile found for {ticker}")
            return {}
        
        profile = data[0]
        company_info = {
            "symbol": profile.get('symbol'),
            "company_name": profile.get('companyName'),
            "industry": profile.get('industry'),
            "sector": profile.get('sector'),
            "country": profile.get('country'),
            "exchange": profile.get('exchangeShortName'),
            "ipo_date": profile.get('ipoDate'),
            "market_cap": profile.get('mktCap'),
            "employees": profile.get('fullTimeEmployees'),
            "website": profile.get('website'),
            "description": profile.get('description'),
            "ceo": profile.get('ceo'),
            "currency": profile.get('currency'),
            "is_etf": profile.get('isEtf', False),
            "is_actively_trading": profile.get('isActivelyTrading', True)
        }
        
        return company_info
    
    def _get_financial_metrics(self, ticker: str) -> Dict[str, Any]:
        """获取财务指标"""
        metrics = {}
        
        # 获取关键指标
        key_metrics_url = f"{self.base_url}/v3/key-metrics/{ticker}?apikey={self.api_key}&limit=1"
        key_metrics_data = self._make_request(key_metrics_url)
        
        if key_metrics_data and len(key_metrics_data) > 0:
            km = key_metrics_data[0]
            metrics.update({
                "pe_ratio": km.get('peRatio'),
                "pb_ratio": km.get('pbRatio'),
                "ps_ratio": km.get('priceToSalesRatio'),
                "ev_to_ebitda": km.get('enterpriseValueMultiple'),
                "ev_to_sales": km.get('evToSales'),
                "dividend_yield": km.get('dividendYield'),
                "roe": km.get('roe'),
                "roa": km.get('roa'),
                "debt_to_equity": km.get('debtToEquity'),
                "current_ratio": km.get('currentRatio'),
                "quick_ratio": km.get('quickRatio'),
                "gross_profit_margin": km.get('grossProfitMargin'),
                "operating_profit_margin": km.get('operatingProfitMargin'),
                "net_profit_margin": km.get('netProfitMargin'),
                "free_cash_flow_per_share": km.get('freeCashFlowPerShare'),
                "book_value_per_share": km.get('bookValuePerShare'),
                "operating_cash_flow_per_share": km.get('operatingCashFlowPerShare'),
                "revenue_per_share": km.get('revenuePerShare')
            })
        
        # 获取比率数据
        ratios_url = f"{self.base_url}/v3/ratios/{ticker}?apikey={self.api_key}&limit=1"
        ratios_data = self._make_request(ratios_url)
        
        if ratios_data and len(ratios_data) > 0:
            ratios = ratios_data[0]
            metrics.update({
                "interest_coverage": ratios.get('interestCoverage'),
                "debt_ratio": ratios.get('debtRatio'),
                "asset_turnover": ratios.get('assetTurnover'),
                "inventory_turnover": ratios.get('inventoryTurnover'),
                "receivables_turnover": ratios.get('receivablesTurnover'),
                "return_on_capital_employed": ratios.get('returnOnCapitalEmployed'),
                "return_on_tangible_assets": ratios.get('returnOnTangibleAssets')
            })
        
        # 获取增长率数据
        growth_url = f"{self.base_url}/v3/financial-growth/{ticker}?apikey={self.api_key}&limit=1"
        growth_data = self._make_request(growth_url)
        
        if growth_data and len(growth_data) > 0:
            growth = growth_data[0]
            metrics.update({
                "revenue_growth": growth.get('revenueGrowth'),
                "net_income_growth": growth.get('netIncomeGrowth'),
                "eps_growth": growth.get('epsgrowth'),
                "operating_cash_flow_growth": growth.get('operatingCashFlowGrowth'),
                "free_cash_flow_growth": growth.get('freeCashFlowGrowth'),
                "asset_growth": growth.get('assetGrowth'),
                "equity_growth": growth.get('equityGrowth')
            })
        
        return metrics
    
    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        获取股票数据（简化版本 - 无缓存，无价格数据）
        
        Args:
            ticker: 股票代码，如 'AAPL'
            
        Returns:
            包含公司信息和财务指标的字典
        """
        ticker = ticker.upper()
        
        try:
            logger.info(f"开始获取股票 {ticker} 的FMP数据")
            
            result = {
                "ticker": ticker,
                "company_info": {},
                "financial_metrics": {},
                "data_source": "financial_modeling_prep",
                "timestamp": datetime.now().isoformat()
            }
            
            # 1. 获取公司基本信息
            logger.info(f"获取 {ticker} 公司基本信息")
            company_info = self._get_company_profile(ticker)
            result["company_info"] = company_info
            
            # 2. 获取财务指标
            logger.info(f"获取 {ticker} 财务指标")
            financial_metrics = self._get_financial_metrics(ticker)
            result["financial_metrics"] = financial_metrics
            
            logger.info(f"成功完成 {ticker} 数据获取")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"获取股票 {ticker} 数据时发生错误: {error_msg}")
            return None

# 为了保持向后兼容性，创建一个别名
StockDataFetcher = FMPStockDataFetcher
