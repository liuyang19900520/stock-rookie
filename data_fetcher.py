import requests
import pandas as pd
import logging
import time
import random
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class FMPStockDataFetcher:
    """Financial Modeling Prep (FMP) 股票数据抓取器"""
    
    def __init__(self, cache_dir: str = "./cache"):
        # API配置
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable is required")
        
        self.base_url = "https://financialmodelingprep.com/api"
        self.session = requests.Session()
        self.last_request_time = 0
        
        # 速率限制配置
        self.min_request_interval = float(os.getenv('MIN_REQUEST_INTERVAL', 1.0))
        self.max_request_interval = float(os.getenv('MAX_REQUEST_INTERVAL', 3.0))
        
        # 缓存配置
        self.cache_dir = Path(os.getenv('CACHE_DIR', cache_dir))
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = int(os.getenv('CACHE_DURATION_HOURS', 24)) * 60 * 60
        
        # 请求限制配置
        self.request_count_file = self.cache_dir / "request_count.json"
        self.daily_request_limit = int(os.getenv('DAILY_REQUEST_LIMIT', 80))
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        logger.info("FMP Stock Data Fetcher initialized")
    
    def _rate_limit_delay(self):
        """实施1-3秒随机延迟"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        random_delay = random.uniform(self.min_request_interval, self.max_request_interval)
        
        if time_since_last < random_delay:
            delay = random_delay - time_since_last
            logger.info(f"Rate limiting: waiting {delay:.1f}s before next request")
            time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def _get_request_count(self) -> int:
        """获取今日请求次数"""
        try:
            if self.request_count_file.exists():
                with open(self.request_count_file, 'r') as f:
                    data = json.load(f)
                    if data.get('date') == self.today:
                        return data.get('count', 0)
            return 0
        except Exception as e:
            logger.warning(f"Failed to read request count: {e}")
            return 0
    
    def _increment_request_count(self):
        """增加请求计数"""
        try:
            count = self._get_request_count() + 1
            data = {
                'date': self.today,
                'count': count
            }
            with open(self.request_count_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Daily request count: {count}/{self.daily_request_limit}")
        except Exception as e:
            logger.error(f"Failed to increment request count: {e}")
    
    def _check_request_limit(self) -> bool:
        """检查是否超出请求限制"""
        current_count = self._get_request_count()
        if current_count >= self.daily_request_limit:
            logger.error(f"Daily request limit reached: {current_count}/{self.daily_request_limit}")
            return False
        return True
    
    def _get_cache_file(self, ticker: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{ticker.upper()}.json"
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_file.exists():
            return False
        
        try:
            modified_time = cache_file.stat().st_mtime
            current_time = time.time()
            return (current_time - modified_time) < self.cache_duration
        except Exception:
            return False
    
    def _load_from_cache(self, ticker: str) -> Optional[Dict[str, Any]]:
        """从缓存加载数据"""
        cache_file = self._get_cache_file(ticker)
        
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {ticker} data from cache")
                    return data
            except Exception as e:
                logger.warning(f"Failed to load cache for {ticker}: {e}")
        
        return None
    
    def _save_to_cache(self, ticker: str, data: Dict[str, Any]):
        """保存数据到缓存"""
        cache_file = self._get_cache_file(ticker)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"Saved {ticker} data to cache")
        except Exception as e:
            logger.error(f"Failed to save cache for {ticker}: {e}")
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """发起API请求"""
        self._rate_limit_delay()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def _get_historical_data(self, ticker: str) -> List[Dict]:
        """获取历史价格数据（5年）"""
        url = f"{self.base_url}/v3/historical-price-full/{ticker}?apikey={self.api_key}"
        
        data = self._make_request(url)
        if not data or 'historical' not in data:
            logger.warning(f"No historical data found for {ticker}")
            return []
        
        # 获取最近5年的数据
        historical = data['historical']
        five_years_ago = datetime.now() - timedelta(days=5*365)
        
        price_data = []
        for record in historical:
            try:
                record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                if record_date >= five_years_ago:
                    price_data.append({
                        "date": record['date'],
                        "open": float(record.get('open', 0)) if record.get('open') else None,
                        "high": float(record.get('high', 0)) if record.get('high') else None,
                        "low": float(record.get('low', 0)) if record.get('low') else None,
                        "close": float(record.get('close', 0)) if record.get('close') else None,
                        "volume": int(record.get('volume', 0)) if record.get('volume') else None
                    })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing price data for {ticker}: {e}")
                continue
        
        # 按日期排序（最新的在前）
        price_data.sort(key=lambda x: x['date'], reverse=True)
        logger.info(f"Retrieved {len(price_data)} days of historical data for {ticker}")
        
        return price_data
    
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
                "free_cash_flow_growth": growth.get('freeCashFlowGrowth')
            })
        
        # 获取实时报价数据
        quote_url = f"{self.base_url}/v3/quote/{ticker}?apikey={self.api_key}"
        quote_data = self._make_request(quote_url)
        
        if quote_data and len(quote_data) > 0:
            quote = quote_data[0]
            metrics.update({
                "current_price": quote.get('price'),
                "change": quote.get('change'),
                "change_percent": quote.get('changesPercentage'),
                "day_low": quote.get('dayLow'),
                "day_high": quote.get('dayHigh'),
                "year_low": quote.get('yearLow'),
                "year_high": quote.get('yearHigh'),
                "market_cap": quote.get('marketCap'),
                "volume": quote.get('volume'),
                "avg_volume": quote.get('avgVolume'),
                "open": quote.get('open'),
                "previous_close": quote.get('previousClose'),
                "eps": quote.get('eps'),
                "pe": quote.get('pe'),
                "shares_outstanding": quote.get('sharesOutstanding')
            })
        
        return metrics
    
    def get_stock_data(self, ticker: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取完整股票数据（FMP API版本）
        
        Args:
            ticker: 股票代码，如 'AAPL'
            use_cache: 是否使用缓存，默认True
            
        Returns:
            包含价格数据、公司信息和财务指标的完整字典
        """
        ticker = ticker.upper()
        
        # 根据参数决定是否检查缓存
        if use_cache:
            cached_data = self._load_from_cache(ticker)
            if cached_data:
                logger.info(f"从缓存加载 {ticker} 数据")
                return cached_data
        
        # 检查请求限制
        if not self._check_request_limit():
            logger.error(f"Daily request limit exceeded for {ticker}")
            return None
        
        try:
            logger.info(f"开始获取股票 {ticker} 的FMP数据")
            self._increment_request_count()
            
            result = {
                "ticker": ticker,
                "price_data": [],
                "company_info": {},
                "financial_metrics": {},
                "data_source": "financial_modeling_prep",
                "timestamp": datetime.now().isoformat(),
                "cache_expires": (datetime.now() + timedelta(seconds=self.cache_duration)).isoformat()
            }
            
            # 1. 获取历史价格数据
            logger.info(f"获取 {ticker} 历史价格数据")
            price_data = self._get_historical_data(ticker)
            result["price_data"] = price_data
            
            # 2. 获取公司基本信息
            logger.info(f"获取 {ticker} 公司基本信息")
            company_info = self._get_company_profile(ticker)
            result["company_info"] = company_info
            
            # 3. 获取财务指标
            logger.info(f"获取 {ticker} 财务指标")
            financial_metrics = self._get_financial_metrics(ticker)
            result["financial_metrics"] = financial_metrics
            
            # 根据参数决定是否保存到缓存
            if use_cache:
                self._save_to_cache(ticker, result)
                logger.info(f"成功完成 {ticker} 数据获取并缓存")
            else:
                result["cache_status"] = "bypassed"
                logger.info(f"成功完成 {ticker} 数据获取（跳过缓存）")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"获取股票 {ticker} 数据时发生错误: {error_msg}")
            return None

# 为了保持向后兼容性，创建一个别名
StockDataFetcher = FMPStockDataFetcher

class FMPStockDataFetcherUnlimited:
    """Financial Modeling Prep (FMP) 股票数据抓取器 - 无请求限制版本"""
    
    def __init__(self, cache_dir: str = "./cache"):
        # API配置
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable is required")
        
        self.base_url = "https://financialmodelingprep.com/api"
        self.session = requests.Session()
        self.last_request_time = 0
        
        # 速率限制配置（保留以避免API限制）
        self.min_request_interval = float(os.getenv('MIN_REQUEST_INTERVAL', 1.0))
        self.max_request_interval = float(os.getenv('MAX_REQUEST_INTERVAL', 3.0))
        
        # 缓存配置
        self.cache_dir = Path(os.getenv('CACHE_DIR', cache_dir))
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = int(os.getenv('CACHE_DURATION_HOURS', 24)) * 60 * 60
        
        logger.info("FMP Stock Data Fetcher (Unlimited) initialized")
    
    def _rate_limit_delay(self):
        """实施1-3秒随机延迟（避免API限制）"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        random_delay = random.uniform(self.min_request_interval, self.max_request_interval)
        
        if time_since_last < random_delay:
            delay = random_delay - time_since_last
            logger.info(f"Rate limiting: waiting {delay:.1f}s before next request")
            time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def _get_cache_file(self, ticker: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{ticker.upper()}.json"
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_file.exists():
            return False
        
        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < self.cache_duration
    
    def _load_from_cache(self, ticker: str) -> Optional[Dict[str, Any]]:
        """从缓存加载数据"""
        cache_file = self._get_cache_file(ticker)
        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded {ticker} data from cache")
                return data
            except Exception as e:
                logger.warning(f"Failed to load cache for {ticker}: {e}")
        return None
    
    def _save_to_cache(self, ticker: str, data: Dict[str, Any]):
        """保存数据到缓存"""
        cache_file = self._get_cache_file(ticker)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {ticker} data to cache")
        except Exception as e:
            logger.error(f"Failed to save cache for {ticker}: {e}")
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """发送HTTP请求"""
        self._rate_limit_delay()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _get_historical_data(self, ticker: str) -> List[Dict]:
        """获取历史价格数据"""
        url = f"{self.base_url}/v3/historical-price-full/{ticker}?apikey={self.api_key}"
        data = self._make_request(url)
        
        if data and 'historical' in data:
            historical_data = data['historical']
            logger.info(f"Retrieved {len(historical_data)} days of historical data for {ticker}")
            return historical_data
        return []
    
    def _get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """获取公司基本信息"""
        url = f"{self.base_url}/v3/profile/{ticker}?apikey={self.api_key}"
        data = self._make_request(url)
        
        if data and len(data) > 0:
            profile = data[0]
            return {
                "company_name": profile.get('companyName'),
                "symbol": profile.get('symbol'),
                "price": profile.get('price'),
                "changes": profile.get('changes'),
                "currency": profile.get('currency'),
                "exchange": profile.get('exchange'),
                "industry": profile.get('industry'),
                "website": profile.get('website'),
                "description": profile.get('description'),
                "ceo": profile.get('ceo'),
                "sector": profile.get('sector'),
                "country": profile.get('country'),
                "full_time_employees": profile.get('fullTimeEmployees'),
                "phone": profile.get('phone'),
                "address": profile.get('address'),
                "city": profile.get('city'),
                "state": profile.get('state'),
                "zip": profile.get('zip'),
                "dcf_diff": profile.get('dcfDiff'),
                "dcf": profile.get('dcf'),
                "beta": profile.get('beta'),
                "vol_avg": profile.get('volAvg'),
                "mkt_cap": profile.get('mktCap'),
                "last_div": profile.get('lastDiv'),
                "range": profile.get('range'),
                "changes_percentage": profile.get('changesPercentage'),
                "avg_volume": profile.get('avgVolume'),
                "pe": profile.get('pe'),
                "eps": profile.get('eps'),
                "earnings_announcement": profile.get('earningsAnnouncement'),
                "shares_outstanding": profile.get('sharesOutstanding'),
                "timestamp": profile.get('timestamp')
            }
        return {}
    
    def _get_financial_metrics(self, ticker: str) -> Dict[str, Any]:
        """获取财务指标"""
        metrics = {}
        
        # 获取关键财务比率
        ratios_url = f"{self.base_url}/v3/ratios/{ticker}?apikey={self.api_key}"
        ratios_data = self._make_request(ratios_url)
        
        if ratios_data and len(ratios_data) > 0:
            ratios = ratios_data[0]
            metrics.update({
                "current_ratio": ratios.get('currentRatio'),
                "quick_ratio": ratios.get('quickRatio'),
                "cash_ratio": ratios.get('cashRatio'),
                "debt_to_equity": ratios.get('debtToEquity'),
                "debt_to_assets": ratios.get('debtToAssets'),
                "interest_coverage": ratios.get('interestCoverage'),
                "gross_profit_margin": ratios.get('grossProfitMargin'),
                "operating_profit_margin": ratios.get('operatingProfitMargin'),
                "net_profit_margin": ratios.get('netProfitMargin'),
                "roe": ratios.get('returnOnEquity'),
                "roa": ratios.get('returnOnAssets'),
                "roic": ratios.get('returnOnCapitalEmployed'),
                "asset_turnover": ratios.get('assetTurnover'),
                "inventory_turnover": ratios.get('inventoryTurnover'),
                "receivables_turnover": ratios.get('receivablesTurnover'),
                "payables_turnover": ratios.get('payablesTurnover'),
                "days_sales_outstanding": ratios.get('daysOfSalesOutstanding'),
                "days_payables_outstanding": ratios.get('daysOfPayablesOutstanding'),
                "days_inventory_outstanding": ratios.get('daysOfInventoryOutstanding'),
                "operating_cycle": ratios.get('operatingCycle'),
                "cash_conversion_cycle": ratios.get('cashConversionCycle'),
                "pe_ratio": ratios.get('priceEarningsRatio'),
                "pb_ratio": ratios.get('priceToBookRatio'),
                "ps_ratio": ratios.get('priceToSalesRatio'),
                "pcf_ratio": ratios.get('priceCashFlowRatio'),
                "ev_to_ebitda": ratios.get('enterpriseValueMultiple'),
                "dividend_yield": ratios.get('dividendYield'),
                "dividend_payout_ratio": ratios.get('dividendPayoutRatio'),
                "free_cash_flow_yield": ratios.get('freeCashFlowYield')
            })
        
        # 获取现金流增长率
        growth_url = f"{self.base_url}/v3/cash-flow-statement-growth/{ticker}?apikey={self.api_key}"
        growth_data = self._make_request(growth_url)
        
        if growth_data and len(growth_data) > 0:
            growth = growth_data[0]
            metrics.update({
                "operating_cash_flow_growth": growth.get('operatingCashFlowGrowth'),
                "net_income_growth": growth.get('netIncomeGrowth'),
                "free_cash_flow_growth": growth.get('freeCashFlowGrowth')
            })
        
        # 获取实时报价数据
        quote_url = f"{self.base_url}/v3/quote/{ticker}?apikey={self.api_key}"
        quote_data = self._make_request(quote_url)
        
        if quote_data and len(quote_data) > 0:
            quote = quote_data[0]
            metrics.update({
                "current_price": quote.get('price'),
                "change": quote.get('change'),
                "change_percent": quote.get('changesPercentage'),
                "day_low": quote.get('dayLow'),
                "day_high": quote.get('dayHigh'),
                "year_low": quote.get('yearLow'),
                "year_high": quote.get('yearHigh'),
                "market_cap": quote.get('marketCap'),
                "volume": quote.get('volume'),
                "avg_volume": quote.get('avgVolume'),
                "open": quote.get('open'),
                "previous_close": quote.get('previousClose'),
                "eps": quote.get('eps'),
                "pe": quote.get('pe'),
                "shares_outstanding": quote.get('sharesOutstanding')
            })
        
        return metrics
    
    def get_stock_data(self, ticker: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取完整股票数据（FMP API版本 - 无请求限制）
        
        Args:
            ticker: 股票代码，如 'AAPL'
            use_cache: 是否使用缓存，默认True
            
        Returns:
            包含价格数据、公司信息和财务指标的完整字典
        """
        ticker = ticker.upper()
        
        # 根据参数决定是否检查缓存
        if use_cache:
            cached_data = self._load_from_cache(ticker)
            if cached_data:
                logger.info(f"从缓存加载 {ticker} 数据")
                return cached_data
        
        try:
            logger.info(f"开始获取股票 {ticker} 的FMP数据（无限制版本）")
            
            result = {
                "ticker": ticker,
                "price_data": [],
                "company_info": {},
                "financial_metrics": {},
                "data_source": "financial_modeling_prep_unlimited",
                "timestamp": datetime.now().isoformat(),
                "cache_expires": (datetime.now() + timedelta(seconds=self.cache_duration)).isoformat()
            }
            
            # 1. 获取历史价格数据
            logger.info(f"获取 {ticker} 历史价格数据")
            price_data = self._get_historical_data(ticker)
            result["price_data"] = price_data
            
            # 2. 获取公司基本信息
            logger.info(f"获取 {ticker} 公司基本信息")
            company_info = self._get_company_profile(ticker)
            result["company_info"] = company_info
            
            # 3. 获取财务指标
            logger.info(f"获取 {ticker} 财务指标")
            financial_metrics = self._get_financial_metrics(ticker)
            result["financial_metrics"] = financial_metrics
            
            # 根据参数决定是否保存到缓存
            if use_cache:
                self._save_to_cache(ticker, result)
                logger.info(f"成功完成 {ticker} 数据获取并缓存")
            else:
                result["cache_status"] = "bypassed"
                logger.info(f"成功完成 {ticker} 数据获取（跳过缓存）")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"获取股票 {ticker} 数据时发生错误: {error_msg}")
            return None