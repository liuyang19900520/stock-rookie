import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScoreWeights:
    """评分权重配置"""
    valuation: float = 0.25      # 估值指标权重
    profitability: float = 0.25  # 盈利能力权重
    growth: float = 0.20         # 成长性权重
    financial_health: float = 0.15  # 财务健康权重
    momentum: float = 0.15       # 动量指标权重

@dataclass
class StockScore:
    """股票评分结果"""
    symbol: str
    total_score: float
    valuation_score: float
    profitability_score: float
    growth_score: float
    financial_health_score: float
    momentum_score: float
    grade: str
    recommendation: str

class StockScorer:
    """股票评分器"""
    
    def __init__(self, weights: Optional[ScoreWeights] = None):
        self.weights = weights or ScoreWeights()
    
    def normalize_score(self, value: float, optimal_range: Tuple[float, float], 
                       reverse: bool = False) -> float:
        """
        将指标值标准化为0-100分
        
        Args:
            value: 原始值
            optimal_range: 最优范围 (min, max)
            reverse: 是否反向评分（值越小越好）
            
        Returns:
            标准化后的分数 (0-100)
        """
        if pd.isna(value) or value == 0:
            return 50  # 缺失值给中性分
        
        min_val, max_val = optimal_range
        
        if reverse:
            # 值越小越好（如P/E比率）
            if value <= min_val:
                return 100
            elif value >= max_val:
                return 0
            else:
                return 100 - ((value - min_val) / (max_val - min_val)) * 100
        else:
            # 值越大越好（如ROE）
            if value >= max_val:
                return 100
            elif value <= min_val:
                return 0
            else:
                return ((value - min_val) / (max_val - min_val)) * 100
    
    def calculate_valuation_score(self, stock_data: Dict) -> float:
        """计算估值评分"""
        try:
            pe_ratio = stock_data.get('pe_ratio', 0)
            pb_ratio = stock_data.get('pb_ratio', 0)
            
            # P/E 比率评分 (5-25为优秀范围)
            pe_score = self.normalize_score(pe_ratio, (5, 25), reverse=True)
            
            # P/B 比率评分 (0.5-3为合理范围)
            pb_score = self.normalize_score(pb_ratio, (0.5, 3), reverse=True)
            
            valuation_score = (pe_score + pb_score) / 2
            
            logger.debug(f"Valuation score: PE={pe_score:.1f}, PB={pb_score:.1f}, Total={valuation_score:.1f}")
            return valuation_score
            
        except Exception as e:
            logger.error(f"Error calculating valuation score: {str(e)}")
            return 50
    
    def calculate_profitability_score(self, stock_data: Dict) -> float:
        """计算盈利能力评分"""
        try:
            profit_margins = stock_data.get('profit_margins', 0)
            roe = stock_data.get('return_on_equity', 0)
            
            # 净利润率评分 (0-0.3为优秀范围)
            margin_score = self.normalize_score(profit_margins, (0, 0.3))
            
            # ROE评分 (0-0.4为优秀范围)
            roe_score = self.normalize_score(roe, (0, 0.4))
            
            profitability_score = (margin_score + roe_score) / 2
            
            logger.debug(f"Profitability score: Margin={margin_score:.1f}, ROE={roe_score:.1f}, Total={profitability_score:.1f}")
            return profitability_score
            
        except Exception as e:
            logger.error(f"Error calculating profitability score: {str(e)}")
            return 50
    
    def calculate_growth_score(self, stock_data: Dict) -> float:
        """计算成长性评分"""
        try:
            revenue_growth = stock_data.get('revenue_growth', 0)
            
            # 营收增长率评分 (-0.1 to 0.5为合理范围)
            growth_score = self.normalize_score(revenue_growth, (-0.1, 0.5))
            
            logger.debug(f"Growth score: Revenue growth={growth_score:.1f}")
            return growth_score
            
        except Exception as e:
            logger.error(f"Error calculating growth score: {str(e)}")
            return 50
    
    def calculate_financial_health_score(self, stock_data: Dict) -> float:
        """计算财务健康评分"""
        try:
            debt_to_equity = stock_data.get('debt_to_equity', 0)
            
            # 债务股权比评分 (0-1为健康范围)
            health_score = self.normalize_score(debt_to_equity, (0, 1), reverse=True)
            
            logger.debug(f"Financial health score: D/E={health_score:.1f}")
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating financial health score: {str(e)}")
            return 50
    
    def calculate_momentum_score(self, price_change_data: Optional[Dict]) -> float:
        """计算动量评分"""
        try:
            if not price_change_data:
                return 50
            
            price_change_pct = price_change_data.get('price_change_pct', 0)
            
            # 价格变化评分 (-20% to 20%为合理范围)
            momentum_score = self.normalize_score(price_change_pct, (-20, 20))
            
            logger.debug(f"Momentum score: Price change={momentum_score:.1f}")
            return momentum_score
            
        except Exception as e:
            logger.error(f"Error calculating momentum score: {str(e)}")
            return 50
    
    def get_grade_and_recommendation(self, total_score: float) -> Tuple[str, str]:
        """根据总分获取等级和建议"""
        if total_score >= 80:
            return "A", "强烈推荐"
        elif total_score >= 70:
            return "B", "推荐"
        elif total_score >= 60:
            return "C", "中性"
        elif total_score >= 50:
            return "D", "谨慎"
        else:
            return "F", "不推荐"
    
    def score_stock(self, stock_data: Dict, price_change_data: Optional[Dict] = None) -> StockScore:
        """
        对股票进行综合评分
        
        Args:
            stock_data: 股票基本信息
            price_change_data: 价格变化数据
            
        Returns:
            股票评分结果
        """
        try:
            # 计算各项分数
            valuation_score = self.calculate_valuation_score(stock_data)
            profitability_score = self.calculate_profitability_score(stock_data)
            growth_score = self.calculate_growth_score(stock_data)
            financial_health_score = self.calculate_financial_health_score(stock_data)
            momentum_score = self.calculate_momentum_score(price_change_data)
            
            # 计算加权总分
            total_score = (
                valuation_score * self.weights.valuation +
                profitability_score * self.weights.profitability +
                growth_score * self.weights.growth +
                financial_health_score * self.weights.financial_health +
                momentum_score * self.weights.momentum
            )
            
            grade, recommendation = self.get_grade_and_recommendation(total_score)
            
            result = StockScore(
                symbol=stock_data.get('symbol', 'N/A'),
                total_score=round(total_score, 1),
                valuation_score=round(valuation_score, 1),
                profitability_score=round(profitability_score, 1),
                growth_score=round(growth_score, 1),
                financial_health_score=round(financial_health_score, 1),
                momentum_score=round(momentum_score, 1),
                grade=grade,
                recommendation=recommendation
            )
            
            logger.info(f"Stock {result.symbol} scored {result.total_score} (Grade: {result.grade})")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring stock: {str(e)}")
            # 返回默认评分
            return StockScore(
                symbol=stock_data.get('symbol', 'N/A'),
                total_score=50.0,
                valuation_score=50.0,
                profitability_score=50.0,
                growth_score=50.0,
                financial_health_score=50.0,
                momentum_score=50.0,
                grade="C",
                recommendation="数据不足"
            )
    
    def score_multiple_stocks(self, stocks_data: Dict[str, Dict], 
                            price_changes: Optional[Dict[str, Dict]] = None) -> List[StockScore]:
        """
        批量评分多个股票
        
        Args:
            stocks_data: 多个股票的基本信息
            price_changes: 多个股票的价格变化数据
            
        Returns:
            股票评分结果列表
        """
        results = []
        
        for symbol, stock_data in stocks_data.items():
            if stock_data is None:
                continue
                
            price_change = price_changes.get(symbol) if price_changes else None
            score = self.score_stock(stock_data, price_change)
            results.append(score)
        
        # 按总分降序排列
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        return results

# 创建全局实例
stock_scorer = StockScorer() 