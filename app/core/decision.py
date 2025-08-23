"""
决策模块 - 极简实现
提供基本的决策逻辑支持
"""

from typing import Dict, List, Any


def evaluate_rating_thresholds(total_score: float, thresholds: List[Dict]) -> Dict[str, str]:
    """
    根据总分和阈值评估评级
    
    Args:
        total_score: 总分
        thresholds: 评级阈值列表
        
    Returns:
        评级和规模建议
    """
    rating = "REDUCE/WAIT"
    sizing = "underweight"
    
    for threshold in thresholds:
        if total_score >= threshold.get('min_score', 0):
            rating = threshold.get('rating', 'REDUCE/WAIT')
            sizing = threshold.get('sizing', 'underweight')
    
    return {"rating": rating, "sizing": sizing}


def check_red_flags(indicators: List[Dict], inputs: Dict) -> List[str]:
    """
    检查红标条件
    
    Args:
        indicators: 指标列表
        inputs: 输入数据
        
    Returns:
        触发的红标列表
    """
    red_flags = []
    
    for indicator in indicators:
        indicator_id = indicator.get('id')
        raw_value = None
        
        # 获取原始值
        field_hint = indicator.get('fetch', {}).get('field_hint', [indicator_id])
        for field in field_hint:
            if field in inputs:
                raw_value = inputs[field]
                break
        
        # 检查红标条件
        if 'red_flag_if_below' in indicator:
            threshold = indicator['red_flag_if_below']
            if raw_value is not None and raw_value < threshold:
                red_flags.append(f"{indicator_id}: below {threshold}")
        
        if 'red_flag_if_below_any' in indicator:
            below_any = indicator['red_flag_if_below_any']
            for field, threshold in below_any.items():
                if field in inputs and inputs[field] < threshold:
                    red_flags.append(f"{indicator_id}.{field}: below {threshold}")
    
    return red_flags


def apply_rating_downgrade(current_rating: str, downgrade_levels: int = 1) -> str:
    """
    应用评级降级
    
    Args:
        current_rating: 当前评级
        downgrade_levels: 降级级别数
        
    Returns:
        降级后的评级
    """
    rating_hierarchy = ["BUY", "ACCUMULATE", "HOLD", "REDUCE/WAIT"]
    
    try:
        current_index = rating_hierarchy.index(current_rating)
        new_index = min(current_index + downgrade_levels, len(rating_hierarchy) - 1)
        return rating_hierarchy[new_index]
    except ValueError:
        return "REDUCE/WAIT"


def generate_sizing_advice(rating: str, category_scores: Dict[str, float]) -> str:
    """
    生成规模建议
    
    Args:
        rating: 评级
        category_scores: 类别分数
        
    Returns:
        规模建议
    """
    if rating == "BUY":
        return "建议加仓或超配"
    elif rating == "ACCUMULATE":
        return "建议分批建仓"
    elif rating == "HOLD":
        return "建议持有观望"
    elif rating == "REDUCE/WAIT":
        return "建议减持或等待"
    else:
        return "建议谨慎评估"
