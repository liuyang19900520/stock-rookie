"""
股票评分系统
支持不同行业的个性化评分权重和阈值配置
基于外部配置文件，实现评分系统与行业模板的解耦
"""

import logging
import numpy as np
import yaml
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ================================
# 行业模板配置管理器
# ================================

class IndustryTemplateManager:
    """行业模板配置管理器"""
    
    def __init__(self, config_file: str = "industry_templates.yaml"):
        self.config_file = Path(config_file)
        self.config = None
        self.industry_mapping = {}
        self.templates = {}
        self.metadata = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not self.config_file.exists():
                logger.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
                self._create_default_config()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 提取配置
            self.industry_mapping = self.config.get('industry_mapping', {})
            self.templates = self.config.get('templates', {})
            self.metadata = self.config.get('metadata', {})
            
            logger.info(f"成功加载行业模板配置，包含 {len(self.templates)} 个行业模板")
            logger.info(f"配置版本: {self.metadata.get('version', 'unknown')}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self.industry_mapping = {
            "Banks - Diversified": "banking",
            "Consumer Electronics": "technology",
            "default": "general"
        }
        
        self.templates = {
            "banking": {
                "name": "银行业",
                "thresholds": {
                    "roe_min": 8,
                    "pe_max": 12,
                    "pe_zero": 20,
                    "pb_bonus": 1.2,
                    "yield_min": 3,
                    "ma_days": 200,
                    "trend_min_pct": -5,
                    "trend_max_pct": 15,
                    "atr_pct_max": 15,
                    "atr_pct_zero": 30
                },
                "weights": {
                    "quality": 0.25,
                    "value": 0.30,
                    "dividend": 0.20,
                    "trend": 0.15,
                    "risk": -0.10
                },
                "decision_thresholds": {
                    "buy": 70,
                    "watch": 55
                }
            },
            "technology": {
                "name": "科技行业",
                "thresholds": {
                    "roe_min": 15,
                    "pe_max": 25,
                    "pe_zero": 50,
                    "pb_bonus": 2.0,
                    "yield_min": 1,
                    "ma_days": 50,
                    "trend_min_pct": -10,
                    "trend_max_pct": 30,
                    "atr_pct_max": 25,
                    "atr_pct_zero": 50
                },
                "weights": {
                    "quality": 0.20,
                    "value": 0.25,
                    "dividend": 0.10,
                    "trend": 0.25,
                    "risk": -0.20
                },
                "decision_thresholds": {
                    "buy": 70,
                    "watch": 55
                }
            },
            "general": {
                "name": "通用",
                "thresholds": {
                    "roe_min": 10,
                    "pe_max": 18,
                    "pe_zero": 35,
                    "pb_bonus": 1.5,
                    "yield_min": 2.5,
                    "ma_days": 100,
                    "trend_min_pct": -10,
                    "trend_max_pct": 20,
                    "atr_pct_max": 20,
                    "atr_pct_zero": 40
                },
                "weights": {
                    "quality": 0.25,
                    "value": 0.25,
                    "dividend": 0.20,
                    "trend": 0.20,
                    "risk": -0.10
                },
                "decision_thresholds": {
                    "buy": 70,
                    "watch": 55
                }
            }
        }
        
        self.metadata = {
            "version": "1.0.0",
            "description": "默认配置"
        }
    
    def reload_config(self):
        """重新加载配置文件"""
        logger.info("重新加载行业模板配置...")
        self._load_config()
    
    def get_industry_template(self, industry: str) -> Optional[Dict]:
        """获取行业模板配置"""
        return self.templates.get(industry)
    
    def map_fmp_industry(self, fmp_industry: str) -> str:
        """将FMP API行业映射到模板行业"""
        if not fmp_industry:
            return self.industry_mapping.get("default", "general")
        
        # 精确匹配
        if fmp_industry in self.industry_mapping:
            return self.industry_mapping[fmp_industry]
        
        # 模糊匹配
        fmp_lower = fmp_industry.lower()
        for fmp_key, template_industry in self.industry_mapping.items():
            if fmp_key.lower() in fmp_lower or fmp_lower in fmp_key.lower():
                return template_industry
        
        # 关键词匹配
        if any(keyword in fmp_lower for keyword in ['bank', 'financial', 'credit']):
            return "banking"
        elif any(keyword in fmp_lower for keyword in ['consumer electronics', 'software', 'tech', 'electronic', 'semiconductor']):
            return "technology"
        elif any(keyword in fmp_lower for keyword in ['drug', 'medical', 'biotech', 'healthcare']):
            return "healthcare"
        elif any(keyword in fmp_lower for keyword in ['oil', 'gas', 'energy', 'coal']):
            return "energy"
        elif any(keyword in fmp_lower for keyword in ['beverage', 'food', 'consumer']):
            return "consumer_goods"
        elif any(keyword in fmp_lower for keyword in ['retail', 'store', 'shop']):
            return "retail"
        elif any(keyword in fmp_lower for keyword in ['industrial', 'machinery', 'aerospace']):
            return "industrial"
        elif any(keyword in fmp_lower for keyword in ['reit', 'real estate', 'property']):
            return "real_estate"
        elif any(keyword in fmp_lower for keyword in ['telecom', 'communication', 'entertainment']):
            return "telecommunications"
        elif any(keyword in fmp_lower for keyword in ['chemical', 'steel', 'aluminum', 'material']):
            return "materials"
        elif any(keyword in fmp_lower for keyword in ['utility', 'electric', 'gas', 'water']):
            return "utilities"
        elif any(keyword in fmp_lower for keyword in ['airline', 'railroad', 'transportation']):
            return "transportation"
        
        # 默认返回通用模板
        return self.industry_mapping.get("default", "general")
    
    def list_available_templates(self) -> List[str]:
        """列出所有可用的行业模板"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict]:
        """获取模板详细信息"""
        template = self.templates.get(template_name)
        if template:
            return {
                "name": template.get("name", template_name),
                "description": template.get("description", ""),
                "characteristics": template.get("characteristics", []),
                "thresholds": template.get("thresholds", {}),
                "weights": template.get("weights", {}),
                "decision_thresholds": template.get("decision_thresholds", {})
            }
        return None

# 创建全局模板管理器实例
template_manager = IndustryTemplateManager()

# ================================
# 数据类定义
# ================================

@dataclass
class StockScores:
    """股票各维度得分"""
    quality: int
    value: int
    dividend: int
    trend: int
    risk: int

@dataclass
class StockRating:
    """股票评级结果"""
    scores: StockScores
    total_score: float
    decision: str
    industry: str
    details: Dict[str, Any]

# ================================
# 核心评分类
# ================================

class StockScorer:
    """股票评分器"""
    
    def __init__(self, template_manager: Optional[IndustryTemplateManager] = None):
        self.template_manager = template_manager or IndustryTemplateManager()
    
    def map_fmp_industry(self, fmp_industry: str) -> str:
        """
        将FMP API的行业字段映射到模板中的行业类型
        
        Args:
            fmp_industry: FMP API返回的行业字段
            
        Returns:
            模板中的行业类型
        """
        return self.template_manager.map_fmp_industry(fmp_industry)
    
    def calculate_moving_average(self, price_data: List[Dict], days: int) -> Optional[float]:
        """
        计算移动平均线
        
        Args:
            price_data: 价格数据列表（按日期倒序）
            days: 均线天数
            
        Returns:
            移动平均价格
        """
        if not price_data or len(price_data) < days:
            return None
        
        try:
            # 获取最近days天的收盘价
            recent_prices = []
            for i in range(min(days, len(price_data))):
                close_price = price_data[i].get('close')
                if close_price is not None:
                    recent_prices.append(float(close_price))
            
            if len(recent_prices) < days * 0.8:  # 至少需要80%的数据
                return None
                
            return sum(recent_prices) / len(recent_prices)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error calculating moving average: {e}")
            return None
    
    def calculate_atr_percentage(self, price_data: List[Dict], days: int = 14) -> Optional[float]:
        """
        计算ATR百分比（Average True Range Percentage）
        
        Args:
            price_data: 价格数据列表（按日期倒序）
            days: ATR计算天数
            
        Returns:
            ATR百分比
        """
        if not price_data or len(price_data) < days + 1:
            return None
        
        try:
            true_ranges = []
            
            for i in range(days):
                if i + 1 >= len(price_data):
                    break
                    
                current = price_data[i]
                previous = price_data[i + 1]
                
                high = float(current.get('high', 0))
                low = float(current.get('low', 0))
                prev_close = float(previous.get('close', 0))
                
                if high == 0 or low == 0 or prev_close == 0:
                    continue
                
                # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)
            
            if len(true_ranges) < days * 0.8:
                return None
            
            atr = sum(true_ranges) / len(true_ranges)
            current_price = float(price_data[0].get('close', 1))
            
            if current_price == 0:
                return None
                
            return (atr / current_price) * 100
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error calculating ATR: {e}")
            return None

# 简化的评分函数用于测试
def score_stock(data: Dict, industry: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    简化的股票评分函数
    
    Args:
        data: 股票数据（来自FMP API）
        industry: 可选的行业覆盖
        
    Returns:
        评分结果字典
    """
    try:
        # 提取基础数据
        company_info = data.get('company_info', {})
        financial_metrics = data.get('financial_metrics', {})
        price_data = data.get('price_data', [])
        
        # 确定行业
        if industry is None:
            fmp_industry = company_info.get('industry', '')
            industry = template_manager.map_fmp_industry(fmp_industry)
            logger.info(f"Mapped FMP industry '{fmp_industry}' to template '{industry}'")
        
        # 获取行业模板配置
        template = template_manager.get_industry_template(industry)
        if template is None:
            logger.warning(f"Template '{industry}' not found, using 'general' template")
            industry = 'general'
            template = template_manager.get_industry_template(industry)
        
        thresholds = template['thresholds']
        weights = template['weights']
        decision_thresholds = template['decision_thresholds']
        
        # 简化的评分计算
        scores = {}
        
        # Quality Score (ROE)
        roe = financial_metrics.get('roe', 0)
        if roe:
            roe_pct = float(roe) * 100 if roe < 1 else float(roe)
            roe_min = thresholds['roe_min']
            quality_score = min(100, max(0, int((roe_pct / roe_min) * 100))) if roe_pct >= roe_min else int((roe_pct / roe_min) * 100)
        else:
            quality_score = 0
        scores['quality'] = quality_score
        
        # Value Score (PE)
        pe_ratio = financial_metrics.get('pe_ratio', 0)
        if pe_ratio:
            pe = float(pe_ratio)
            pe_max = thresholds['pe_max']
            pe_zero = thresholds['pe_zero']
            if pe <= pe_max:
                value_score = 100
            elif pe >= pe_zero:
                value_score = 0
            else:
                value_score = int(100 * (pe_zero - pe) / (pe_zero - pe_max))
        else:
            value_score = 0
        scores['value'] = value_score
        
        # Dividend Score
        dividend_yield = financial_metrics.get('dividend_yield', 0)
        if dividend_yield:
            yield_pct = float(dividend_yield) * 100 if dividend_yield < 1 else float(dividend_yield)
            yield_min = thresholds['yield_min']
            dividend_score = min(100, max(0, int((yield_pct / yield_min) * 100))) if yield_pct >= yield_min else int((yield_pct / yield_min) * 100)
        else:
            dividend_score = 0
        scores['dividend'] = dividend_score
        
        # Trend Score (简化版)
        trend_score = 50  # 默认中性
        scores['trend'] = trend_score
        
        # Risk Score (简化版)
        risk_score = 50  # 默认中性
        scores['risk'] = risk_score
        
        # 计算总分
        total_score = (
            quality_score * weights['quality'] +
            value_score * weights['value'] +
            dividend_score * weights['dividend'] +
            trend_score * weights['trend'] +
            risk_score * weights['risk']
        )
        
        # 决策
        buy_threshold = decision_thresholds.get('buy', 70)
        watch_threshold = decision_thresholds.get('watch', 55)
        
        if total_score >= buy_threshold:
            decision = "Buy"
        elif total_score >= watch_threshold:
            decision = "Watch"
        else:
            decision = "Avoid"
        
        return {
            "scores": scores,
            "total_score": round(total_score, 2),
            "decision": decision,
            "industry": industry,
            "template_name": template.get('name', industry),
            "details": {
                "industry_used": industry,
                "fmp_industry": company_info.get('industry', 'N/A'),
                "template_info": {
                    "name": template.get('name', industry),
                    "description": template.get('description', ''),
                    "characteristics": template.get('characteristics', [])
                },
                "weights": weights,
                "thresholds": thresholds,
                "decision_thresholds": decision_thresholds,
                "raw_data": {
                    "roe": roe,
                    "pe_ratio": pe_ratio,
                    "dividend_yield": dividend_yield
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error scoring stock: {e}")
        return None

# 创建全局评分器实例
stock_scorer = StockScorer(template_manager)
