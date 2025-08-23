"""
股票评分系统核心模块
支持多种评分类型、权重归一化、决策规则等
"""

import json
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    """
    读取评分配置文件并校验权重
    
    Args:
        path: 配置文件路径
        
    Returns:
        配置字典，包含归一化标记
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 校验四大类权重之和
        weights = config.get('weights', {})
        total_weight = sum(weights.values())
        
        if abs(total_weight - 100) > 0.01:  # 允许0.01的浮点误差
            # 按比例归一化
            for category in weights:
                weights[category] = (weights[category] / total_weight) * 100
            config['_normalized'] = True
            logger.info(f"Weights normalized to sum to 100: {weights}")
        else:
            config['_normalized'] = False
        
        # 校验各类别内指标权重
        indicators = config.get('indicators', [])
        category_weights = {}
        
        for indicator in indicators:
            category = indicator.get('category')
            weight = indicator.get('weight', 0)
            if category not in category_weights:
                category_weights[category] = []
            category_weights[category].append((indicator['id'], weight))
        
        # 检查并归一化各类别权重
        for category, indicators_weights in category_weights.items():
            total_cat_weight = sum(weight for _, weight in indicators_weights)
            expected_weight = weights.get(category, 0)
            
            if abs(total_cat_weight - expected_weight) > 0.5:  # 允许±0.5浮动
                # 按比例归一化
                for indicator in indicators:
                    if indicator['category'] == category:
                        indicator['weight'] = (indicator['weight'] / total_cat_weight) * expected_weight
                logger.info(f"Category {category} weights normalized to sum to {expected_weight}")
        
        return config
        
    except Exception as e:
        logger.error(f"Error loading config from {path}: {e}")
        raise


def _linear_interpolate(value: float, breakpoints: List[List[float]]) -> float:
    """线性插值计算分数"""
    if not breakpoints:
        return 0
    
    # 排序断点
    sorted_points = sorted(breakpoints, key=lambda x: x[0])
    
    # 边界检查
    if value <= sorted_points[0][0]:
        return sorted_points[0][1]
    if value >= sorted_points[-1][0]:
        return sorted_points[-1][1]
    
    # 找到插值区间
    for i in range(len(sorted_points) - 1):
        if sorted_points[i][0] <= value <= sorted_points[i + 1][0]:
            x1, y1 = sorted_points[i]
            x2, y2 = sorted_points[i + 1]
            
            if x2 == x1:
                return y1
            
            # 线性插值
            ratio = (value - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)
    
    return 0


def _percentile_rank(value: float, sample_array: List[float]) -> float:
    """计算百分位排名"""
    if not sample_array:
        return 50  # 默认中位数
    
    # 过滤有效值
    valid_samples = [x for x in sample_array if x is not None and not math.isnan(x)]
    if not valid_samples:
        return 50
    
    # 计算百分位
    valid_samples.append(value)
    valid_samples.sort()
    
    rank = valid_samples.index(value)
    percentile = (rank / (len(valid_samples) - 1)) * 100
    
    return percentile


def _safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """安全除法"""
    if denominator == 0 or math.isnan(denominator):
        return default
    return numerator / denominator


def score_indicator(ind: dict, inputs: dict, peers: dict, context: dict) -> dict:
    """
    对单个指标进行评分
    
    Args:
        ind: 指标配置
        inputs: 输入数据
        peers: 同行数据
        context: 上下文信息
        
    Returns:
        评分结果字典
    """
    indicator_id = ind['id']
    scoring_config = ind.get('scoring', {})
    scoring_type = scoring_config.get('type')
    direction = ind.get('direction', 'higher_is_better')
    
    warnings = []
    peer_context = {}
    
    # 获取原始值
    raw_value = None
    field_hint = ind.get('fetch', {}).get('field_hint', [indicator_id])
    
    for field in field_hint:
        if field in inputs:
            raw_value = inputs[field]
            break
    
    if raw_value is None or (isinstance(raw_value, float) and math.isnan(raw_value)):
        warnings.append(f"Missing or invalid value for {indicator_id}")
        return {
            "id": indicator_id,
            "raw": None,
            "score": 0,
            "weight": ind.get('weight', 0),
            "category": ind.get('category'),
            "warnings": warnings,
            "peer_context": peer_context
        }
    
    # 根据评分类型计算分数
    score = 0
    
    if scoring_type == "linear_thresholds":
        breakpoints = scoring_config.get('breakpoints', [])
        score = _linear_interpolate(raw_value, breakpoints)
        
    elif scoring_type == "peer_percentile":
        peer_key = scoring_config.get('peer', indicator_id)
        if peer_key in peers:
            sample_array = peers[peer_key]
            score = _percentile_rank(raw_value, sample_array)
            peer_context['peer_median'] = sorted(sample_array)[len(sample_array)//2] if sample_array else None
        else:
            warnings.append(f"Peer data not available for {peer_key}")
            score = 60  # 默认分数
            
    elif scoring_type == "relative_to_peer":
        relation = scoring_config.get('relation', '')
        mapping = scoring_config.get('mapping', [])
        
        # 解析关系表达式
        if 'median_peer_' in relation:
            peer_key = relation.split('median_peer_')[-1]
            if peer_key in peers:
                peer_median = sorted(peers[peer_key])[len(peers[peer_key])//2]
                ratio = _safe_divide(raw_value, peer_median, 1.0)
                score = _linear_interpolate(ratio, mapping)
                peer_context['peer_median'] = peer_median
            else:
                warnings.append(f"Peer median not available for {peer_key}")
                score = 60
        else:
            warnings.append(f"Unsupported relation: {relation}")
            score = 60
            
    elif scoring_type == "two_dim":
        x_field = scoring_config.get('x')
        y_field = scoring_config.get('y')
        grid = scoring_config.get('grid', [])
        default = scoring_config.get('default', 60)
        
        x_value = inputs.get(x_field)
        y_value = inputs.get(y_field)
        
        if x_value is None or y_value is None:
            warnings.append(f"Missing x or y value for two_dim scoring")
            score = default
        else:
            # 检查是否命中网格
            max_score = default
            for grid_item in grid:
                x_range = grid_item.get('x', [])
                y_range = grid_item.get('y', [])
                grid_score = grid_item.get('score', 0)
                
                if (len(x_range) == 2 and x_range[0] <= x_value <= x_range[1] and
                    len(y_range) == 2 and y_range[0] <= y_value <= y_range[1]):
                    max_score = max(max_score, grid_score)
            
            score = max_score
            
    elif scoring_type == "count_thresholds":
        breakpoints = scoring_config.get('breakpoints', [])
        # 假设raw_value是计数
        score = _linear_interpolate(raw_value, breakpoints)
        
    elif scoring_type == "policy_phase":
        mapping = scoring_config.get('map', {})
        score = mapping.get(str(raw_value), 0)
        
    elif scoring_type == "composite_avg":
        sub_indicators = scoring_config.get('sub', [])
        sub_scores = []
        
        for sub_ind in sub_indicators:
            sub_key = sub_ind.get('k')
            sub_breakpoints = sub_ind.get('breakpoints', [])
            
            if sub_key in inputs:
                sub_value = inputs[sub_key]
                sub_score = _linear_interpolate(sub_value, sub_breakpoints)
                sub_scores.append(sub_score)
            else:
                warnings.append(f"Missing sub-indicator {sub_key}")
                sub_scores.append(0)
        
        score = sum(sub_scores) / len(sub_scores) if sub_scores else 0
        
    elif scoring_type == "stage":
        mapping = scoring_config.get('map', {})
        score = mapping.get(str(raw_value), 0)
        
    elif scoring_type == "categorical":
        mapping = scoring_config.get('map', {})
        score = mapping.get(str(raw_value), 0)
        
    elif scoring_type == "relative_index":
        # 如果inputs中已有相对收益百分比，直接使用
        if 'relative_return_pct' in inputs:
            score = _linear_interpolate(inputs['relative_return_pct'], 
                                      scoring_config.get('breakpoints', []))
        else:
            score = 60  # 默认分数
            
    elif scoring_type == "two_dim_invert":
        x_field = scoring_config.get('x')
        y_field = scoring_config.get('y')
        target = scoring_config.get('target', {})
        
        x_value = inputs.get(x_field)
        y_value = inputs.get(y_field)
        
        if x_value is None or y_value is None:
            warnings.append(f"Missing x or y value for two_dim_invert scoring")
            score = 60
        else:
            # 分别计算x和y的"越低越好"分数
            x_target = target.get('beta', [0.7, 1.1])
            y_target = target.get('vol', [0, 999])
            
            # x分数：越接近目标区间中心越好
            x_center = (x_target[0] + x_target[1]) / 2
            x_distance = abs(x_value - x_center)
            x_score = max(0, 100 - x_distance * 50)  # 距离越远分数越低
            
            # y分数：越低越好
            y_score = max(0, 100 - y_value * 0.1)  # 简单线性映射
            
            score = (x_score + y_score) / 2
            
    else:
        warnings.append(f"Unknown scoring type: {scoring_type}")
        score = 60
    
    # 处理方向
    if direction == "lower_is_better":
        score = 100 - score
    
    # 确保分数在0-100范围内
    score = max(0, min(100, score))
    
    return {
        "id": indicator_id,
        "raw": raw_value,
        "score": score,
        "weight": ind.get('weight', 0),
        "category": ind.get('category'),
        "warnings": warnings,
        "peer_context": peer_context
    }


def aggregate_scores(config: dict, breakdown: list) -> Tuple[Dict[str, float], float]:
    """
    聚合评分结果
    
    Args:
        config: 配置字典
        breakdown: 评分明细列表
        
    Returns:
        (类别分数字典, 总分)
    """
    weights = config.get('weights', {})
    category_scores = {}
    
    # 按类别分组
    category_indicators = {}
    for item in breakdown:
        category = item['category']
        if category not in category_indicators:
            category_indicators[category] = []
        category_indicators[category].append(item)
    
    # 计算各类别加权分数
    for category, indicators in category_indicators.items():
        if not indicators:
            category_scores[category] = 0
            continue
        
        # 计算类别内加权平均
        total_weight = sum(ind['weight'] for ind in indicators)
        if total_weight == 0:
            category_scores[category] = 0
            continue
        
        weighted_sum = sum(ind['score'] * ind['weight'] for ind in indicators)
        category_score = weighted_sum / total_weight
        category_scores[category] = category_score
    
    # 计算总分（与四大类权重相乘）
    total_score = 0
    for category, score in category_scores.items():
        category_weight = weights.get(category, 0)
        total_score += score * (category_weight / 100)
    
    return category_scores, total_score


def apply_decision_rules(config: dict, breakdown: list, category_scores: dict, 
                        total: float, inputs: dict) -> dict:
    """
    应用决策规则
    
    Args:
        config: 配置字典
        breakdown: 评分明细
        category_scores: 类别分数
        total: 总分
        inputs: 输入数据
        
    Returns:
        决策结果字典
    """
    decision_rules = config.get('decision_rules', {})
    triggered = []
    red_flags = []
    
    # 评分到评级映射
    score_to_rating = decision_rules.get('score_to_rating', [])
    rating = "REDUCE/WAIT"
    sizing = "underweight"
    
    for rule in score_to_rating:
        if total >= rule.get('min_score', 0):
            rating = rule.get('rating', 'REDUCE/WAIT')
            sizing = rule.get('sizing', 'underweight')
    
    # 检查红标
    red_flag_rules = decision_rules.get('red_flags', [])
    for rule in red_flag_rules:
        rule_id = rule.get('id')
        condition = rule.get('cond')
        action = rule.get('action')
        
        # 查找对应的指标
        indicator = None
        for item in breakdown:
            if item['id'] == rule_id:
                indicator = item
                break
        
        if indicator:
            raw_value = indicator['raw']
            
            # 解析条件
            if condition == "< 10.0" and raw_value is not None:
                if raw_value < 10.0:
                    red_flags.append(f"{rule_id}: {condition}")
                    if action == "DOWNGRADE_ONE_LEVEL":
                        # 降级逻辑
                        if rating == "BUY":
                            rating = "ACCUMULATE"
                        elif rating == "ACCUMULATE":
                            rating = "HOLD"
                        elif rating == "HOLD":
                            rating = "REDUCE/WAIT"
                    elif action == "IMMEDIATE_HOLD_REVIEW":
                        rating = "HOLD"
                        sizing = "review_required"
            
            elif condition == "LCR < 100 or NSFR < 100":
                lcr = inputs.get('lcr')
                nsfr = inputs.get('nsfr')
                if (lcr is not None and lcr < 100) or (nsfr is not None and nsfr < 100):
                    red_flags.append(f"{rule_id}: {condition}")
                    if action == "DOWNGRADE_ONE_LEVEL":
                        if rating == "BUY":
                            rating = "ACCUMULATE"
                        elif rating == "ACCUMULATE":
                            rating = "HOLD"
                        elif rating == "HOLD":
                            rating = "REDUCE/WAIT"
            
            elif condition == "drops_to_none":
                if raw_value == "none":
                    red_flags.append(f"{rule_id}: {condition}")
                    if action == "DOWNGRADE_ONE_LEVEL":
                        if rating == "BUY":
                            rating = "ACCUMULATE"
                        elif rating == "ACCUMULATE":
                            rating = "HOLD"
                        elif rating == "HOLD":
                            rating = "REDUCE/WAIT"
            
            elif condition == "true":
                # 手动触发的红标
                red_flags.append(f"{rule_id}: manual_trigger")
                if action == "IMMEDIATE_HOLD_REVIEW":
                    rating = "HOLD"
                    sizing = "review_required"
    
    # 检查买入触发条件
    buy_triggers = decision_rules.get('buy_triggers', [])
    for trigger in buy_triggers:
        if _evaluate_trigger(trigger, breakdown, category_scores, inputs, red_flags):
            triggered.append(f"BUY: {trigger}")
    
    # 检查减持触发条件
    trim_triggers = decision_rules.get('trim_triggers', [])
    for trigger in trim_triggers:
        if _evaluate_trigger(trigger, breakdown, category_scores, inputs, red_flags):
            triggered.append(f"TRIM: {trigger}")
    
    return {
        "rating": rating,
        "sizing": sizing,
        "triggered": triggered,
        "red_flags": red_flags
    }


def _evaluate_trigger(trigger: str, breakdown: list, category_scores: dict, 
                     inputs: dict, red_flags: list) -> bool:
    """评估触发条件"""
    try:
        # 创建评估环境
        env = {
            'breakdown': breakdown,
            'category_scores': category_scores,
            'inputs': inputs,
            'red_flags': red_flags
        }
        
        # 解析条件
        if "score >=" in trigger:
            parts = trigger.split(" score >=")
            indicator_id = parts[0].strip()
            threshold = float(parts[1].split()[0])
            
            for item in breakdown:
                if item['id'] == indicator_id:
                    return item['score'] >= threshold
                    
        elif ">=" in trigger and "score" not in trigger:
            parts = trigger.split(">=")
            indicator_id = parts[0].strip()
            threshold = float(parts[1].split()[0])
            
            return inputs.get(indicator_id, 0) >= threshold
            
        elif "no_red_flags" in trigger:
            return len(red_flags) == 0
            
        elif "core_fundamentals_weighted" in trigger:
            return category_scores.get('core_fundamentals', 0) >= 75
            
        elif "AND" in trigger:
            conditions = trigger.split(" AND ")
            return all(_evaluate_trigger(cond.strip(), breakdown, category_scores, inputs, red_flags) 
                      for cond in conditions)
            
        elif "OR" in trigger:
            conditions = trigger.split(" OR ")
            return any(_evaluate_trigger(cond.strip(), breakdown, category_scores, inputs, red_flags) 
                      for cond in conditions)
        
        return False
        
    except Exception as e:
        logger.warning(f"Error evaluating trigger '{trigger}': {e}")
        return False


def _generate_advice(rating: str, category_scores: dict, total: float) -> str:
    """生成投资建议"""
    if rating == "BUY":
        return "核心稳健+稳定币催化明确，建议加仓或超配"
    elif rating == "ACCUMULATE":
        return "基本面良好，回撤分批吸纳"
    elif rating == "HOLD":
        return "持有观望，等待估值或催化改善"
    elif rating == "REDUCE/WAIT":
        return "弱于预期，减持或等待更优价位"
    else:
        return "建议谨慎评估"


def score_stock(config: dict, inputs: dict, peers: dict = None, 
          overrides: dict = None, context: dict = None) -> dict:
    """
    主评分函数
    
    Args:
        config: 配置字典
        inputs: 输入数据
        peers: 同行数据
        overrides: 覆盖数据
        context: 上下文
        
    Returns:
        完整的评分结果
    """
    if peers is None:
        peers = {}
    if overrides is None:
        overrides = {}
    if context is None:
        context = {}
    
    # 合并overrides到inputs
    merged_inputs = inputs.copy()
    for key, value in overrides.items():
        merged_inputs[key] = value
    
    # 处理composite指标
    indicators = config.get('indicators', [])
    for indicator in indicators:
        if indicator.get('scoring', {}).get('type') == 'composite_avg':
            sub_indicators = indicator['scoring'].get('sub', [])
            for sub_ind in sub_indicators:
                sub_key = sub_ind.get('k')
                if sub_key not in merged_inputs:
                    # 检查是否有对应的field_hint
                    field_hints = indicator.get('fetch', {}).get('field_hint', [])
                    for hint in field_hints:
                        if hint.lower() == sub_key.lower():
                            if hint in merged_inputs:
                                merged_inputs[sub_key] = merged_inputs[hint]
                                break
    
    # 对每个指标进行评分
    breakdown = []
    all_warnings = []
    
    for indicator in indicators:
        result = score_indicator(indicator, merged_inputs, peers, context)
        breakdown.append(result)
        all_warnings.extend(result['warnings'])
    
    # 聚合分数
    category_scores, total_score = aggregate_scores(config, breakdown)
    
    # 应用决策规则
    decision_result = apply_decision_rules(config, breakdown, category_scores, total_score, merged_inputs)
    
    # 生成建议
    advice = _generate_advice(decision_result['rating'], category_scores, total_score)
    
    return {
        "meta": {
            "stock": config.get('meta', {}).get('stock', ''),
            "as_of": datetime.now().isoformat(),
            "scoring_version": config.get('meta', {}).get('scoring_version', ''),
            "warnings": all_warnings
        },
        "breakdown": breakdown,
        "category_scores": category_scores,
        "total_score": total_score,
        "rating": decision_result['rating'],
        "sizing": decision_result['sizing'],
        "triggered": decision_result['triggered'],
        "advice": advice
    }


# 内置测试样例
def run_sample_test():
    """运行内置样例测试"""
    # 加载配置
    config = load_config('app/config/bk.json')
    
    # 测试输入
    inputs = {
        "roe": 14.2, "cet1Ratio": 11.4, "lcr": 112, "nsfr": 121,
        "dividendYieldTTM": 3.2, "payoutRatio": 36,
        "priceToBookTTM": 1.07, "pb": 1.07,
        "netInterestIncomeYoY": 6.1, "feeRevenueYoY": 4.0,
        "assetsUnderCustodyAdminYoY": 3.5,
        "beta": 0.95, "realizedVol180d": 18.5,
        "epsNext12mRevisionPct": 2.1,
        "maxDrawdown180dPct": 14.0
    }
    
    peers = {
        "pb": [1.20, 1.10, 1.05],
        "auc_growth": [2.1, 3.8, 1.5],
        "pretax_margin": [0.29, 0.31, 0.27]
    }
    
    overrides = {
        "stablecoin_custody": ">=2_major",
        "tokenization_initiatives": 2,
        "digital_custody_maturity": "limited_clients",
        "regulatory_tailwind": "law_passed_rules_pending"
    }
    
    # 执行评分
    result = score_stock(config, inputs, peers, overrides)
    
    print("=== 评分结果 ===")
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


if __name__ == "__main__":
    run_sample_test()
