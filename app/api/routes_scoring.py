"""
评分API路由
提供股票评分功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.scoring import load_config, score_stock
from app.db.base import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/scoring", tags=["scoring"])


class ScoringRequest(BaseModel):
    """评分请求模型"""
    symbol: str
    config_path: Optional[str] = "app/config/bk.json"
    overrides: Optional[Dict[str, Any]] = {}
    context: Optional[Dict[str, Any]] = {}


class ScoringResponse(BaseModel):
    """评分响应模型"""
    meta: Dict[str, Any]
    breakdown: List[Dict[str, Any]]
    category_scores: Dict[str, float]
    total_score: float
    rating: str
    sizing: str
    triggered: List[str]
    advice: str


@router.post("/score", response_model=ScoringResponse)
async def score_stock_endpoint(
    request: ScoringRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    对股票进行评分
    
    Args:
        request: 评分请求
        db: 数据库会话
        
    Returns:
        评分结果
    """
    try:
        # 加载配置
        config = load_config(request.config_path)
        
        # 从数据库获取股票数据
        from app.data.repositories import CoreIndicatorsRepository
        
        # 获取最新指标数据
        repo = CoreIndicatorsRepository(db)
        indicators_data = await repo.get_latest_indicators(request.symbol)
        
        if not indicators_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for symbol {request.symbol}"
            )
        
        # 转换为输入格式
        inputs = {}
        for indicator_id, indicator in indicators_data.items():
            if indicator.value is not None:
                inputs[indicator_id] = float(indicator.value)
        
        # 构建同行数据（这里简化处理，实际可以从数据库获取）
        peers = {
            "pb": [1.20, 1.10, 1.05],
            "auc_growth": [2.1, 3.8, 1.5],
            "pretax_margin": [0.29, 0.31, 0.27]
        }
        
        # 执行评分
        result = score_stock(
            config=config,
            inputs=inputs,
            peers=peers,
            overrides=request.overrides,
            context=request.context
        )
        
        logger.info(f"Scoring completed for {request.symbol}: {result['total_score']:.1f}")
        
        return ScoringResponse(**result)
        
    except Exception as e:
        logger.error(f"Error scoring {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs")
async def list_configs():
    """列出可用的评分配置"""
    import os
    import glob
    
    config_dir = "app/config"
    config_files = glob.glob(os.path.join(config_dir, "*.json"))
    
    configs = []
    for config_file in config_files:
        try:
            config = load_config(config_file)
            configs.append({
                "name": os.path.basename(config_file),
                "path": config_file,
                "stock": config.get('meta', {}).get('stock', ''),
                "version": config.get('meta', {}).get('scoring_version', ''),
                "description": config.get('meta', {}).get('description', '')
            })
        except Exception as e:
            logger.warning(f"Failed to load config {config_file}: {e}")
    
    return {"configs": configs}


@router.get("/config/{config_name}")
async def get_config(config_name: str):
    """获取特定配置的详情"""
    config_path = f"app/config/{config_name}"
    
    try:
        config = load_config(config_path)
        return {
            "name": config_name,
            "path": config_path,
            "meta": config.get('meta', {}),
            "weights": config.get('weights', {}),
            "indicators_count": len(config.get('indicators', [])),
            "decision_rules": config.get('decision_rules', {})
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Config not found: {e}")


@router.post("/batch-score")
async def batch_score_stocks(
    symbols: List[str],
    config_path: str = "app/config/bk.json",
    overrides: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    批量评分多个股票
    
    Args:
        symbols: 股票代码列表
        config_path: 配置文件路径
        overrides: 覆盖数据
        db: 数据库会话
        
    Returns:
        批量评分结果
    """
    if overrides is None:
        overrides = {}
    
    try:
        # 加载配置
        config = load_config(config_path)
        
        results = []
        from app.data.repositories import CoreIndicatorsRepository
        
        for symbol in symbols:
            try:
                # 获取股票数据
                repo = CoreIndicatorsRepository(db)
                indicators_data = await repo.get_latest_indicators(symbol)
                
                if not indicators_data:
                    results.append({
                        "symbol": symbol,
                        "error": "No data found",
                        "success": False
                    })
                    continue
                
                # 转换为输入格式
                inputs = {}
                for indicator_id, indicator in indicators_data.items():
                    if indicator.value is not None:
                        inputs[indicator_id] = float(indicator.value)
                
                # 构建同行数据
                peers = {
                    "pb": [1.20, 1.10, 1.05],
                    "auc_growth": [2.1, 3.8, 1.5],
                    "pretax_margin": [0.29, 0.31, 0.27]
                }
                
                # 执行评分
                result = score_stock(
                    config=config,
                    inputs=inputs,
                    peers=peers,
                    overrides=overrides,
                    context={}
                )
                
                results.append({
                    "symbol": symbol,
                    "success": True,
                    "total_score": result['total_score'],
                    "rating": result['rating'],
                    "category_scores": result['category_scores'],
                    "advice": result['advice']
                })
                
            except Exception as e:
                logger.error(f"Error scoring {symbol}: {e}")
                results.append({
                    "symbol": symbol,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "results": results,
            "total_symbols": len(symbols),
            "successful_symbols": len([r for r in results if r['success']]),
            "failed_symbols": len([r for r in results if not r['success']])
        }
        
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))
