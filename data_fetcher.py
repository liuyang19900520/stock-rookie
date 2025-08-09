import yfinance as yf
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StockDataFetcher:
    """股票数据抓取器"""
    
    def __init__(self):
        self.session = None
    
    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        获取完整股票数据
        
        Args:
            ticker: 股票代码，如 'AAPL'
            
        Returns:
            包含价格数据、公司信息和财务指标的完整字典
        """
        try:
            logger.info(f"开始获取股票 {ticker} 的数据")
            stock = yf.Ticker(ticker)
            
            # 初始化返回数据结构
            result = {
                "price_data": [],
                "company_info": {},
                "financial_metrics": {}
            }
            
            # 1. 获取过去5年的价格数据
            try:
                hist_data = stock.history(period="5y")
                if not hist_data.empty:
                    price_data = []
                    for date, row in hist_data.iterrows():
                        price_data.append({
                            "date": date.strftime("%Y-%m-%d"),
                            "open": float(row['Open']) if pd.notna(row['Open']) else None,
                            "high": float(row['High']) if pd.notna(row['High']) else None,
                            "low": float(row['Low']) if pd.notna(row['Low']) else None,
                            "close": float(row['Close']) if pd.notna(row['Close']) else None,
                            "volume": int(row['Volume']) if pd.notna(row['Volume']) else None
                        })
                    result["price_data"] = price_data
                    logger.info(f"成功获取 {len(price_data)} 天的价格数据")
                else:
                    logger.warning(f"未找到 {ticker} 的历史价格数据")
            except Exception as e:
                logger.error(f"获取价格数据失败: {str(e)}")
            
            # 2. 获取公司基本信息
            try:
                info = stock.info
                fast_info = stock.fast_info if hasattr(stock, 'fast_info') else {}
                
                result["company_info"] = {
                    "symbol": ticker,
                    "name": info.get('longName'),
                    "sector": info.get('sector'),
                    "industry": info.get('industry'),
                    "country": info.get('country'),
                    "city": info.get('city'),
                    "website": info.get('website'),
                    "business_summary": info.get('longBusinessSummary'),
                    "market_cap": info.get('marketCap'),
                    "enterprise_value": info.get('enterpriseValue'),
                    "shares_outstanding": info.get('sharesOutstanding'),
                    "float_shares": info.get('floatShares'),
                    "full_time_employees": info.get('fullTimeEmployees'),
                    "first_trade_date": info.get('firstTradeDateEpochUtc'),
                    "currency": info.get('currency'),
                    "exchange": info.get('exchange'),
                    "quote_type": info.get('quoteType'),
                    "timezone": info.get('timeZoneFullName')
                }
                logger.info("成功获取公司基本信息")
            except Exception as e:
                logger.error(f"获取公司信息失败: {str(e)}")
            
            # 3. 获取财务指标
            try:
                info = stock.info
                financial_metrics = {}
                
                # 盈利能力指标
                financial_metrics.update({
                    "return_on_equity": info.get('returnOnEquity'),
                    "return_on_assets": info.get('returnOnAssets'),
                    "gross_margins": info.get('grossMargins'),
                    "profit_margins": info.get('profitMargins'),
                    "operating_margins": info.get('operatingMargins'),
                    "ebitda_margins": info.get('ebitdaMargins')
                })
                
                # 成长性指标
                financial_metrics.update({
                    "earnings_growth": info.get('earningsGrowth'),
                    "revenue_growth": info.get('revenueGrowth'),
                    "earnings_quarterly_growth": info.get('earningsQuarterlyGrowth'),
                    "revenue_quarterly_growth": info.get('revenueQuarterlyGrowth'),
                    "trailing_eps": info.get('trailingEps'),
                    "forward_eps": info.get('forwardEps')
                })
                
                # 偿债能力指标
                financial_metrics.update({
                    "debt_to_equity": info.get('debtToEquity'),
                    "current_ratio": info.get('currentRatio'),
                    "quick_ratio": info.get('quickRatio'),
                    "interest_coverage": info.get('interestCoverage'),
                    "total_debt": info.get('totalDebt'),
                    "total_cash": info.get('totalCash'),
                    "total_cash_per_share": info.get('totalCashPerShare')
                })
                
                # 估值指标
                financial_metrics.update({
                    "trailing_pe": info.get('trailingPE'),
                    "forward_pe": info.get('forwardPE'),
                    "price_to_book": info.get('priceToBook'),
                    "price_to_sales_trailing_12months": info.get('priceToSalesTrailing12Months'),
                    "enterprise_to_revenue": info.get('enterpriseToRevenue'),
                    "enterprise_to_ebitda": info.get('enterpriseToEbitda'),
                    "peg_ratio": info.get('pegRatio'),
                    "dividend_yield": info.get('dividendYield'),
                    "dividend_rate": info.get('dividendRate'),
                    "payout_ratio": info.get('payoutRatio')
                })
                
                # 现金流指标
                financial_metrics.update({
                    "operating_cashflow": info.get('operatingCashflow'),
                    "free_cashflow": info.get('freeCashflow'),
                    "levered_free_cashflow": info.get('leveredFreeCashflow'),
                    "total_revenue": info.get('totalRevenue'),
                    "ebitda": info.get('ebitda'),
                    "net_income_to_common": info.get('netIncomeToCommon')
                })
                
                # 其他重要指标
                financial_metrics.update({
                    "beta": info.get('beta'),
                    "52_week_high": info.get('fiftyTwoWeekHigh'),
                    "52_week_low": info.get('fiftyTwoWeekLow'),
                    "50_day_average": info.get('fiftyDayAverage'),
                    "200_day_average": info.get('twoHundredDayAverage'),
                    "average_volume": info.get('averageVolume'),
                    "average_volume_10days": info.get('averageVolume10days'),
                    "book_value": info.get('bookValue'),
                    "price_to_earnings_growth": info.get('priceEarningsToGrowthRatio'),
                    "held_percent_institutions": info.get('heldPercentInstitutions'),
                    "held_percent_insiders": info.get('heldPercentInsiders'),
                    "short_ratio": info.get('shortRatio'),
                    "short_percent_of_float": info.get('shortPercentOfFloat')
                })
                
                result["financial_metrics"] = financial_metrics
                logger.info("成功获取财务指标")
            except Exception as e:
                logger.error(f"获取财务指标失败: {str(e)}")
            
            # 4. 尝试获取更多详细财务数据
            try:
                # 财务报表数据
                financials = stock.financials
                if financials is not None and not financials.empty:
                    result["financials"] = financials.to_dict()
                    logger.info("成功获取财务报表数据")
                
                balance_sheet = stock.balance_sheet
                if balance_sheet is not None and not balance_sheet.empty:
                    result["balance_sheet"] = balance_sheet.to_dict()
                    logger.info("成功获取资产负债表数据")
                
                cashflow = stock.cashflow
                if cashflow is not None and not cashflow.empty:
                    result["cashflow"] = cashflow.to_dict()
                    logger.info("成功获取现金流量表数据")
                
                earnings = stock.earnings
                if earnings is not None and not earnings.empty:
                    result["earnings"] = earnings.to_dict()
                    logger.info("成功获取收益数据")
                
            except Exception as e:
                logger.error(f"获取详细财务数据失败: {str(e)}")
            
            logger.info(f"成功完成 {ticker} 数据获取")
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                logger.warning(f"获取股票 {ticker} 数据时遇到速率限制，请稍后重试")
            else:
                logger.error(f"获取股票 {ticker} 数据时发生错误: {error_msg}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息（保持向后兼容）
        
        Args:
            symbol: 股票代码，如 'AAPL'
            
        Returns:
            股票基本信息字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            stock_data = {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'profit_margins': info.get('profitMargins', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
            }
            
            logger.info(f"Successfully fetched data for {symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取历史价格数据
        
        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            历史价格数据 DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None
                
            logger.info(f"Successfully fetched {len(hist)} days of historical data for {symbol}")
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        批量获取多个股票的信息
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            股票信息字典，键为股票代码
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = self.get_stock_info(symbol)
            
        return results
    
    def calculate_price_change(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """
        计算价格变化
        
        Args:
            symbol: 股票代码
            days: 计算天数
            
        Returns:
            价格变化信息
        """
        try:
            hist = self.get_historical_data(symbol, period=f"{days}d")
            
            if hist is None or len(hist) < 2:
                return None
                
            current_price = hist['Close'].iloc[-1]
            past_price = hist['Close'].iloc[0]
            
            price_change = current_price - past_price
            price_change_pct = (price_change / past_price) * 100
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'past_price': past_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error calculating price change for {symbol}: {str(e)}")
            return None

# 创建全局实例
stock_fetcher = StockDataFetcher() 