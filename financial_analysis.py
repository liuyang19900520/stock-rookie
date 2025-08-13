"""
财务分析模块
提供详细的财务指标分析和SWOT分析功能
"""

import logging
import requests
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    """财务分析器 - 获取详细的财务指标和行业对比"""
    
    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable is required")
        
        self.base_url = "https://financialmodelingprep.com/api"
        self.session = requests.Session()
        self.last_request_time = 0
        
        # 速率限制
        self.min_request_interval = float(os.getenv('MIN_REQUEST_INTERVAL', 1.0))
        self.max_request_interval = float(os.getenv('MAX_REQUEST_INTERVAL', 3.0))
        
        # 行业平均数据（可以从FMP API获取，这里提供一些基准值）
        self.industry_averages = {
            "technology": {
                "pe_ratio": 25.0,
                "pb_ratio": 3.5,
                "dividend_yield": 1.2,
                "roe": 15.0,
                "debt_to_equity": 0.3,
                "current_ratio": 2.0,
                "gross_margin": 60.0,
                "net_margin": 12.0
            },
            "healthcare": {
                "pe_ratio": 20.0,
                "pb_ratio": 2.8,
                "dividend_yield": 1.8,
                "roe": 12.0,
                "debt_to_equity": 0.4,
                "current_ratio": 1.8,
                "gross_margin": 65.0,
                "net_margin": 10.0
            },
            "financial": {
                "pe_ratio": 12.0,
                "pb_ratio": 1.2,
                "dividend_yield": 3.5,
                "roe": 10.0,
                "debt_to_equity": 0.8,
                "current_ratio": 1.2,
                "gross_margin": 80.0,
                "net_margin": 15.0
            },
            "consumer_goods": {
                "pe_ratio": 18.0,
                "pb_ratio": 2.5,
                "dividend_yield": 2.5,
                "roe": 14.0,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "gross_margin": 45.0,
                "net_margin": 8.0
            },
            "energy": {
                "pe_ratio": 15.0,
                "pb_ratio": 1.8,
                "dividend_yield": 4.0,
                "roe": 8.0,
                "debt_to_equity": 0.6,
                "current_ratio": 1.3,
                "gross_margin": 35.0,
                "net_margin": 6.0
            },
            "telecommunications": {
                "pe_ratio": 16.0,
                "pb_ratio": 2.0,
                "dividend_yield": 4.5,
                "roe": 9.0,
                "debt_to_equity": 0.7,
                "current_ratio": 1.1,
                "gross_margin": 70.0,
                "net_margin": 8.0
            },
            "general": {
                "pe_ratio": 18.0,
                "pb_ratio": 2.2,
                "dividend_yield": 2.8,
                "roe": 12.0,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "gross_margin": 50.0,
                "net_margin": 10.0
            }
        }
    
    def _rate_limit_delay(self):
        """无延迟版本"""
        pass
    
    def _make_request(self, url: str) -> Optional[Any]:
        """发送API请求"""
        try:
            self._rate_limit_delay()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API请求失败: {url}, 错误: {e}")
            return None
    
    def get_dynamic_industry_averages(self, fmp_industry: str) -> Dict[str, Any]:
        """获取动态行业平均数据"""
        logger.info(f"获取 {fmp_industry} 行业动态平均数据")
        
        result = {
            "top_market_cap": {},      # 市值前10企业平均值
            "all_industry": {},        # 全行业平均值
            "top_volume": {}           # 成交量前10企业平均值
        }
        
        try:
            # 1. 获取同行业所有公司列表
            companies_url = f"{self.base_url}/v3/stock-screener?industry={fmp_industry}&apikey={self.api_key}"
            companies_data = self._make_request(companies_url)
            
            if not companies_data or len(companies_data) == 0:
                logger.warning(f"无法获取 {fmp_industry} 行业公司列表")
                return result
            
            # 提取公司信息
            companies = []
            for company in companies_data:
                if isinstance(company, dict):
                    companies.append({
                        'symbol': company.get('symbol'),
                        'market_cap': company.get('marketCap', 0),
                        'volume': company.get('volume', 0),
                        'price': company.get('price', 0)
                    })
            
            if len(companies) == 0:
                logger.warning(f"{fmp_industry} 行业没有有效的公司数据")
                return result
            
            # 2. 按市值排序，获取前10名
            companies_by_market_cap = sorted(companies, key=lambda x: x.get('market_cap', 0), reverse=True)[:10]
            top_market_cap_symbols = [c['symbol'] for c in companies_by_market_cap if c['symbol']]
            
            # 3. 按成交量排序，获取前10名
            companies_by_volume = sorted(companies, key=lambda x: x.get('volume', 0), reverse=True)[:10]
            top_volume_symbols = [c['symbol'] for c in companies_by_volume if c['symbol']]
            
            # 4. 获取所有公司的财务指标
            all_symbols = [c['symbol'] for c in companies if c['symbol']]
            
            # 5. 获取关键指标数据
            if top_market_cap_symbols:
                result["top_market_cap"] = self._get_average_metrics(top_market_cap_symbols, "市值前10")
            
            if all_symbols:
                result["all_industry"] = self._get_average_metrics(all_symbols, "全行业")
            
            if top_volume_symbols:
                result["top_volume"] = self._get_average_metrics(top_volume_symbols, "成交量前10")
            
            logger.info(f"成功获取 {fmp_industry} 行业动态数据")
            
        except Exception as e:
            logger.error(f"获取动态行业数据失败: {e}")
        
        return result
    
    def _get_average_metrics(self, symbols: List[str], group_name: str) -> Dict[str, Any]:
        """获取一组公司的平均财务指标"""
        logger.info(f"计算 {group_name} 平均指标，公司数量: {len(symbols)}")
        
        metrics_list = []
        valid_count = 0
        
        # 限制处理的股票数量以避免API限制
        max_symbols = min(len(symbols), 20)  # 最多处理20个股票
        
        for symbol in symbols[:max_symbols]:
            try:
                # 获取单个公司的关键指标
                key_metrics_url = f"{self.base_url}/v3/key-metrics/{symbol}?apikey={self.api_key}&limit=1"
                metrics_data = self._make_request(key_metrics_url)
                
                if metrics_data and len(metrics_data) > 0:
                    metrics = metrics_data[0]
                    
                    # 提取关键指标
                    company_metrics = {
                        'pe_ratio': metrics.get('peRatio'),
                        'pb_ratio': metrics.get('pbRatio'),
                        'ps_ratio': metrics.get('priceToSalesRatio'),
                        'dividend_yield': metrics.get('dividendYield'),
                        'roe': metrics.get('roe'),
                        'roa': metrics.get('roa'),
                        'debt_to_equity': metrics.get('debtToEquity'),
                        'current_ratio': metrics.get('currentRatio'),
                        'gross_profit_margin': metrics.get('grossProfitMargin'),
                        'net_profit_margin': metrics.get('netProfitMargin')
                    }
                    
                    # 过滤掉None值和异常值
                    valid_metrics = {}
                    for k, v in company_metrics.items():
                        if v is not None:
                            # 过滤异常值
                            if k in ['pe_ratio', 'pb_ratio', 'ps_ratio'] and (v <= 0 or v > 1000):
                                continue
                            if k in ['dividend_yield', 'roe', 'roa', 'gross_profit_margin', 'net_profit_margin'] and (v < -100 or v > 1000):
                                continue
                            if k in ['debt_to_equity', 'current_ratio'] and (v < -10 or v > 100):
                                continue
                            valid_metrics[k] = v
                    
                    if len(valid_metrics) >= 3:  # 至少要有3个有效指标
                        metrics_list.append(valid_metrics)
                        valid_count += 1
                
            except Exception as e:
                logger.warning(f"获取 {symbol} 指标失败: {e}")
                continue
        
        # 计算平均值
        if valid_count == 0:
            logger.warning(f"{group_name} 没有有效的财务数据")
            return {}
        
        # 计算每个指标的平均值
        averages = {}
        metric_keys = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'dividend_yield', 'roe', 'roa', 
                      'debt_to_equity', 'current_ratio', 'gross_profit_margin', 'net_profit_margin']
        
        for metric in metric_keys:
            values = [m.get(metric) for m in metrics_list if m.get(metric) is not None]
            if values:
                averages[metric] = sum(values) / len(values)
        
        logger.info(f"{group_name} 平均指标计算完成，有效公司数: {valid_count}")
        return averages
    
    def get_detailed_financial_metrics(self, ticker: str, industry: str = "general", fmp_industry: str = None) -> Dict[str, Any]:
        """获取详细的财务指标，包括动态行业对比"""
        logger.info(f"获取 {ticker} 详细财务指标")
        
        result = {
            "key_indicators": {},
            "industry_comparison": {},
            "dynamic_industry_averages": {},
            "growth_metrics": {},
            "efficiency_metrics": {},
            "liquidity_metrics": {},
            "profitability_metrics": {},
            "valuation_metrics": {}
        }
        
        # 获取关键指标
        key_metrics_url = f"{self.base_url}/v3/key-metrics/{ticker}?apikey={self.api_key}&limit=1"
        key_metrics_data = self._make_request(key_metrics_url)
        
        if key_metrics_data and len(key_metrics_data) > 0:
            km = key_metrics_data[0]
            
            # 关键指标
            result["key_indicators"] = {
                "pe_ratio": km.get('peRatio'),
                "pb_ratio": km.get('pbRatio'),
                "ps_ratio": km.get('priceToSalesRatio'),
                "dividend_yield": km.get('dividendYield'),
                "roe": km.get('roe'),
                "roa": km.get('roa'),
                "debt_to_equity": km.get('debtToEquity'),
                "current_ratio": km.get('currentRatio'),
                "gross_profit_margin": km.get('grossProfitMargin'),
                "net_profit_margin": km.get('netProfitMargin')
            }
            
            # 行业对比
            industry_avg = self.industry_averages.get(industry, self.industry_averages["general"])
            result["industry_comparison"] = {
                "pe_ratio": {
                    "company": km.get('peRatio'),
                    "industry_avg": industry_avg["pe_ratio"],
                    "status": self._compare_metric(km.get('peRatio'), industry_avg["pe_ratio"], "lower_better")
                },
                "pb_ratio": {
                    "company": km.get('pbRatio'),
                    "industry_avg": industry_avg["pb_ratio"],
                    "status": self._compare_metric(km.get('pbRatio'), industry_avg["pb_ratio"], "lower_better")
                },
                "dividend_yield": {
                    "company": km.get('dividendYield'),
                    "industry_avg": industry_avg["dividend_yield"],
                    "status": self._compare_metric(km.get('dividendYield'), industry_avg["dividend_yield"], "higher_better")
                },
                "roe": {
                    "company": km.get('roe'),
                    "industry_avg": industry_avg["roe"],
                    "status": self._compare_metric(km.get('roe'), industry_avg["roe"], "higher_better")
                },
                "debt_to_equity": {
                    "company": km.get('debtToEquity'),
                    "industry_avg": industry_avg["debt_to_equity"],
                    "status": self._compare_metric(km.get('debtToEquity'), industry_avg["debt_to_equity"], "lower_better")
                },
                "current_ratio": {
                    "company": km.get('currentRatio'),
                    "industry_avg": industry_avg["current_ratio"],
                    "status": self._compare_metric(km.get('currentRatio'), industry_avg["current_ratio"], "higher_better")
                },
                "gross_margin": {
                    "company": km.get('grossProfitMargin'),
                    "industry_avg": industry_avg["gross_margin"],
                    "status": self._compare_metric(km.get('grossProfitMargin'), industry_avg["gross_margin"], "higher_better")
                },
                "net_margin": {
                    "company": km.get('netProfitMargin'),
                    "industry_avg": industry_avg["net_margin"],
                    "status": self._compare_metric(km.get('netProfitMargin'), industry_avg["net_margin"], "higher_better")
                }
            }
            
            # 获取动态行业平均数据
            if fmp_industry:
                result["dynamic_industry_averages"] = self.get_dynamic_industry_averages(fmp_industry)
        
        # 获取增长率指标
        growth_url = f"{self.base_url}/v3/financial-growth/{ticker}?apikey={self.api_key}&limit=1"
        growth_data = self._make_request(growth_url)
        
        if growth_data and len(growth_data) > 0:
            growth = growth_data[0]
            result["growth_metrics"] = {
                "revenue_growth": growth.get('revenueGrowth'),
                "net_income_growth": growth.get('netIncomeGrowth'),
                "eps_growth": growth.get('epsgrowth'),
                "operating_cash_flow_growth": growth.get('operatingCashFlowGrowth'),
                "free_cash_flow_growth": growth.get('freeCashFlowGrowth'),
                "asset_growth": growth.get('assetGrowth'),
                "equity_growth": growth.get('equityGrowth')
            }
        
        # 获取效率指标
        ratios_url = f"{self.base_url}/v3/ratios/{ticker}?apikey={self.api_key}&limit=1"
        ratios_data = self._make_request(ratios_url)
        
        if ratios_data and len(ratios_data) > 0:
            ratios = ratios_data[0]
            result["efficiency_metrics"] = {
                "asset_turnover": ratios.get('assetTurnover'),
                "inventory_turnover": ratios.get('inventoryTurnover'),
                "receivables_turnover": ratios.get('receivablesTurnover'),
                "days_sales_outstanding": ratios.get('daysSalesOutstanding'),
                "days_inventory": ratios.get('daysInventory'),
                "days_payables": ratios.get('daysPayables')
            }
            
            result["liquidity_metrics"] = {
                "current_ratio": ratios.get('currentRatio'),
                "quick_ratio": ratios.get('quickRatio'),
                "cash_ratio": ratios.get('cashRatio'),
                "working_capital": ratios.get('workingCapital'),
                "operating_cash_flow_ratio": ratios.get('operatingCashFlowRatio')
            }
            
            result["profitability_metrics"] = {
                "gross_margin": ratios.get('grossProfitMargin'),
                "operating_margin": ratios.get('operatingProfitMargin'),
                "net_margin": ratios.get('netProfitMargin'),
                "ebitda_margin": ratios.get('ebitdaMargin'),
                "ebit_margin": ratios.get('ebitMargin'),
                "return_on_equity": ratios.get('returnOnEquity'),
                "return_on_assets": ratios.get('returnOnAssets'),
                "return_on_capital": ratios.get('returnOnCapitalEmployed')
            }
        
        # 获取估值指标
        valuation_url = f"{self.base_url}/v3/enterprise-values/{ticker}?apikey={self.api_key}&limit=1"
        valuation_data = self._make_request(valuation_url)
        
        if valuation_data and len(valuation_data) > 0:
            valuation = valuation_data[0]
            result["valuation_metrics"] = {
                "enterprise_value": valuation.get('enterpriseValue'),
                "ev_to_ebitda": valuation.get('enterpriseValueMultiple'),
                "ev_to_revenue": valuation.get('evToRevenue'),
                "ev_to_ebit": valuation.get('evToEbit'),
                "price_to_book": valuation.get('priceToBookRatio'),
                "price_to_sales": valuation.get('priceToSalesRatio'),
                "price_to_cash_flow": valuation.get('priceToCashFlowRatio')
            }
        
        return result
    
    def _compare_metric(self, company_value: float, industry_avg: float, comparison_type: str) -> str:
        """比较公司指标与行业平均值"""
        if company_value is None or industry_avg is None:
            return "no_data"
        
        if comparison_type == "lower_better":
            if company_value < industry_avg * 0.8:
                return "better"
            elif company_value > industry_avg * 1.2:
                return "worse"
            else:
                return "similar"
        elif comparison_type == "higher_better":
            if company_value > industry_avg * 1.2:
                return "better"
            elif company_value < industry_avg * 0.8:
                return "worse"
            else:
                return "similar"
        
        return "similar"
    
    def generate_swot_analysis(self, ticker: str, industry: str = "general") -> Dict[str, Any]:
        """生成SWOT分析"""
        logger.info(f"生成 {ticker} SWOT分析")
        
        # 获取财务指标
        financial_metrics = self.get_detailed_financial_metrics(ticker, industry)
        
        # 获取公司信息
        profile_url = f"{self.base_url}/v3/profile/{ticker}?apikey={self.api_key}"
        profile_data = self._make_request(profile_url)
        
        company_info = {}
        if profile_data and len(profile_data) > 0:
            company_info = profile_data[0]
        
        # 生成SWOT分析
        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        # 分析优势
        if financial_metrics.get("key_indicators"):
            ki = financial_metrics["key_indicators"]
            ic = financial_metrics.get("industry_comparison", {})
            
            # 财务优势
            if ki.get("roe") and ki["roe"] > 15:
                swot["strengths"].append("高ROE，资本回报能力强")
            
            if ki.get("gross_profit_margin") and ki["gross_profit_margin"] > 50:
                swot["strengths"].append("高毛利率，成本控制优秀")
            
            if ki.get("current_ratio") and ki["current_ratio"] > 1.5:
                swot["strengths"].append("良好的流动性，短期偿债能力强")
            
            if ki.get("debt_to_equity") and ki["debt_to_equity"] < 0.5:
                swot["strengths"].append("低负债率，财务结构稳健")
            
            # 行业对比优势
            for metric, comparison in ic.items():
                if comparison.get("status") == "better":
                    if metric == "pe_ratio":
                        swot["strengths"].append("估值相对行业较低")
                    elif metric == "roe":
                        swot["strengths"].append("ROE高于行业平均水平")
                    elif metric == "gross_margin":
                        swot["strengths"].append("毛利率高于行业平均水平")
        
        # 分析劣势
        if financial_metrics.get("key_indicators"):
            ki = financial_metrics["key_indicators"]
            ic = financial_metrics.get("industry_comparison", {})
            
            # 财务劣势
            if ki.get("roe") and ki["roe"] < 8:
                swot["weaknesses"].append("ROE较低，资本回报能力有限")
            
            if ki.get("gross_profit_margin") and ki["gross_profit_margin"] < 30:
                swot["weaknesses"].append("毛利率较低，成本控制需要改善")
            
            if ki.get("current_ratio") and ki["current_ratio"] < 1.0:
                swot["weaknesses"].append("流动性不足，短期偿债压力大")
            
            if ki.get("debt_to_equity") and ki["debt_to_equity"] > 1.0:
                swot["weaknesses"].append("高负债率，财务风险较高")
            
            # 行业对比劣势
            for metric, comparison in ic.items():
                if comparison.get("status") == "worse":
                    if metric == "pe_ratio":
                        swot["weaknesses"].append("估值相对行业较高")
                    elif metric == "roe":
                        swot["weaknesses"].append("ROE低于行业平均水平")
                    elif metric == "gross_margin":
                        swot["weaknesses"].append("毛利率低于行业平均水平")
        
        # 分析机会
        if financial_metrics.get("growth_metrics"):
            growth = financial_metrics["growth_metrics"]
            
            if growth.get("revenue_growth") and growth["revenue_growth"] > 0.1:
                swot["opportunities"].append("营收增长强劲，市场扩张机会")
            
            if growth.get("free_cash_flow_growth") and growth["free_cash_flow_growth"] > 0.1:
                swot["opportunities"].append("自由现金流增长，投资机会增加")
        
        # 分析威胁
        if financial_metrics.get("key_indicators"):
            ki = financial_metrics["key_indicators"]
            
            if ki.get("debt_to_equity") and ki["debt_to_equity"] > 0.8:
                swot["threats"].append("高负债率，利率上升风险")
            
            if ki.get("current_ratio") and ki["current_ratio"] < 1.2:
                swot["threats"].append("流动性紧张，经营风险增加")
        
        # 行业特定分析
        if industry == "technology":
            swot["strengths"].extend([
                "技术领先优势",
                "数字化转型机遇",
                "创新驱动增长"
            ])
            swot["threats"].extend([
                "技术更新迭代快",
                "竞争激烈",
                "监管变化风险"
            ])
        elif industry == "healthcare":
            swot["strengths"].extend([
                "人口老龄化趋势",
                "医疗需求增长",
                "政策支持"
            ])
            swot["threats"].extend([
                "监管严格",
                "研发成本高",
                "专利到期风险"
            ])
        elif industry == "telecommunications":
            swot["strengths"].extend([
                "基础设施投资大",
                "监管环境复杂",
                "数字化转型"
            ])
            swot["threats"].extend([
                "资本支出大",
                "竞争激烈",
                "技术变革风险"
            ])
        
        # 如果没有数据，添加默认信息
        if not swot["strengths"]:
            swot["strengths"].append("暂无数据")
        if not swot["weaknesses"]:
            swot["weaknesses"].append("暂无数据")
        if not swot["opportunities"]:
            swot["opportunities"].append("暂无数据")
        if not swot["threats"]:
            swot["threats"].append("暂无数据")
        
        return swot
