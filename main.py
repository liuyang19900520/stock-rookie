from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from data_fetcher import FMPStockDataFetcher, FMPStockDataFetcherUnlimited
from scoring import score_stock, template_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Stock Rookie API",
    description="股票投资分析 API",
    version="1.0.0"
)

# 创建数据获取器实例
stock_fetcher = FMPStockDataFetcher()
stock_fetcher_unlimited = FMPStockDataFetcherUnlimited()

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Welcome to Stock Rookie API"}

@app.get("/ping")
async def ping():
    """健康检查接口"""
    logger.info("Ping endpoint called")
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    """详细健康检查"""
    return {
        "status": "healthy",
        "service": "stock-rookie-api",
        "version": "1.0.0"
    }

@app.get("/data")
async def get_stock_data_cached(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取股票完整数据（使用缓存）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含价格数据、公司信息和财务指标的完整真实数据（优先从缓存获取）
    """
    # 参数校验
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=400,
            detail="ticker参数必须是非空字符串"
        )
    
    if len(ticker) > 10:
        raise HTTPException(
            status_code=400,
            detail="ticker长度不能超过10个字符"
        )
    
    # 转换为大写
    ticker = ticker.upper().strip()
    
    try:
        logger.info(f"开始处理股票数据请求（缓存模式）: {ticker}")
        
        # 使用缓存获取数据
        stock_data = stock_fetcher.get_stock_data(ticker, use_cache=True)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁或已达到每日限制，请稍后重试"
            )
        
        # 添加请求统计信息
        request_count = stock_fetcher._get_request_count()
        stock_data["request_info"] = {
            "daily_requests_used": request_count,
            "daily_limit": stock_fetcher.daily_request_limit,
            "remaining_requests": stock_fetcher.daily_request_limit - request_count,
            "cache_mode": "enabled"
        }
        
        logger.info(f"成功返回股票 {ticker} 的数据（缓存模式）")
        return stock_data
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 数据时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/data/fresh")
async def get_stock_data_fresh(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取股票最新数据（不使用缓存）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含价格数据、公司信息和财务指标的最新真实数据（强制从Yahoo Finance获取）
    """
    # 参数校验
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=400,
            detail="ticker参数必须是非空字符串"
        )
    
    if len(ticker) > 10:
        raise HTTPException(
            status_code=400,
            detail="ticker长度不能超过10个字符"
        )
    
    # 转换为大写
    ticker = ticker.upper().strip()
    
    try:
        logger.info(f"开始处理股票数据请求（最新数据模式）: {ticker}")
        
        # 强制获取最新数据，不使用缓存
        stock_data = stock_fetcher.get_stock_data(ticker, use_cache=False)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的最新数据")
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁或已达到每日限制，请稍后重试"
            )
        
        # 添加请求统计信息
        request_count = stock_fetcher._get_request_count()
        stock_data["request_info"] = {
            "daily_requests_used": request_count,
            "daily_limit": stock_fetcher.daily_request_limit,
            "remaining_requests": stock_fetcher.daily_request_limit - request_count,
            "cache_mode": "bypassed"
        }
        
        logger.info(f"成功返回股票 {ticker} 的最新数据")
        return stock_data
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 最新数据时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/data/unlimited")
async def get_stock_data_unlimited(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取股票完整数据（无请求限制版本）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含价格数据、公司信息和财务指标的完整真实数据（无请求限制）
    """
    # 参数校验
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=400,
            detail="ticker参数必须是非空字符串"
        )
    
    if len(ticker) > 10:
        raise HTTPException(
            status_code=400,
            detail="ticker长度不能超过10个字符"
        )
    
    # 转换为大写
    ticker = ticker.upper().strip()
    
    try:
        logger.info(f"开始处理股票数据请求（无限制版本）: {ticker}")
        
        # 使用无限制版本获取数据
        stock_data = stock_fetcher_unlimited.get_stock_data(ticker, use_cache=True)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=500,
                detail="无法获取股票数据，请稍后重试"
            )
        
        # 添加请求信息（无限制版本）
        stock_data["request_info"] = {
            "version": "unlimited",
            "data_source": "financial_modeling_prep_unlimited",
            "cache_mode": "enabled",
            "rate_limiting": "enabled_only_for_api_protection"
        }
        
        logger.info(f"成功返回股票 {ticker} 的数据（无限制版本）")
        return stock_data
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 数据时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/data/unlimited/fresh")
async def get_stock_data_unlimited_fresh(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取股票完整数据（无请求限制版本，强制刷新）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含价格数据、公司信息和财务指标的完整真实数据（无请求限制，强制刷新）
    """
    # 参数校验
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=400,
            detail="ticker参数必须是非空字符串"
        )
    
    if len(ticker) > 10:
        raise HTTPException(
            status_code=400,
            detail="ticker长度不能超过10个字符"
        )
    
    # 转换为大写
    ticker = ticker.upper().strip()
    
    try:
        logger.info(f"开始处理股票数据请求（无限制版本，强制刷新）: {ticker}")
        
        # 使用无限制版本强制获取数据
        stock_data = stock_fetcher_unlimited.get_stock_data(ticker, use_cache=False)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=500,
                detail="无法获取股票数据，请稍后重试"
            )
        
        # 添加请求信息（无限制版本）
        stock_data["request_info"] = {
            "version": "unlimited",
            "data_source": "financial_modeling_prep_unlimited",
            "cache_mode": "disabled",
            "rate_limiting": "enabled_only_for_api_protection"
        }
        
        logger.info(f"成功返回股票 {ticker} 的数据（无限制版本，强制刷新）")
        return stock_data
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 数据时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/status")
async def api_status():
    """
    API状态检查
    
    Returns:
        系统状态和数据源可用性信息
    """
    import time
    from datetime import datetime
    
    # 获取请求统计
    request_count = stock_fetcher._get_request_count()
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "api_version": "2.0.0",
        "status": "operational",
        "request_stats": {
            "daily_requests_used": request_count,
            "daily_limit": stock_fetcher.daily_request_limit,
            "remaining_requests": stock_fetcher.daily_request_limit - request_count,
            "usage_percentage": f"{(request_count / stock_fetcher.daily_request_limit * 100):.1f}%"
        },
        "services": {
            "fmp_api": {"status": "unknown", "description": "Financial Modeling Prep API数据源"},
            "cache_system": {"status": "active", "description": "本地缓存系统"},
            "rate_limiting": {"status": "active", "description": "1-3秒随机延迟保护"}
        }
    }
    
    # 检查缓存系统
    try:
        cache_dir = stock_fetcher.cache_dir
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.json"))
            status["services"]["cache_system"]["cached_stocks"] = len(cache_files) - 1  # 减去request_count.json
            status["services"]["cache_system"]["status"] = "healthy"
        else:
            status["services"]["cache_system"]["status"] = "degraded"
    except Exception as e:
        status["services"]["cache_system"]["status"] = "unavailable"
        status["services"]["cache_system"]["error"] = str(e)
    
    # FMP API测试
    try:
        if hasattr(stock_fetcher, 'api_key') and stock_fetcher.api_key:
            status["services"]["fmp_api"]["status"] = "healthy"
            status["services"]["fmp_api"]["api_key_configured"] = True
        else:
            status["services"]["fmp_api"]["status"] = "unavailable"
            status["services"]["fmp_api"]["api_key_configured"] = False
            status["services"]["fmp_api"]["error"] = "API key not configured"
    except Exception as e:
        status["services"]["fmp_api"]["status"] = "unavailable"
        status["services"]["fmp_api"]["error"] = str(e)
    
    # 检查请求限制状态
    if request_count >= stock_fetcher.daily_request_limit:
        status["services"]["rate_limiting"]["status"] = "limit_reached"
        status["services"]["rate_limiting"]["note"] = "已达到每日请求限制"
        status["status"] = "degraded"
    elif request_count >= stock_fetcher.daily_request_limit * 0.8:
        status["services"]["rate_limiting"]["note"] = "接近每日请求限制"
    
    return status

@app.get("/score")
async def score_stock_endpoint(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    股票评分接口
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含各维度得分和综合评级的结果
    """
    # 参数校验
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=400,
            detail="ticker参数必须是非空字符串"
        )
    
    if len(ticker) > 10:
        raise HTTPException(
            status_code=400,
            detail="ticker长度不能超过10个字符"
        )
    
    # 转换为大写
    ticker = ticker.upper().strip()
    
    try:
        logger.info(f"开始处理股票评分请求: {ticker}")
        
        # 先获取股票数据
        stock_data = stock_fetcher.get_stock_data(ticker, use_cache=True)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁或已达到每日限制，请稍后重试"
            )
        
        # 进行评分
        rating_result = score_stock(stock_data)
        
        if rating_result is None:
            logger.warning(f"无法为股票 {ticker} 计算评分")
            raise HTTPException(
                status_code=400,
                detail="数据不足，无法计算评分"
            )
        
        # 添加基础信息
        rating_result["ticker"] = ticker
        rating_result["timestamp"] = stock_data.get("timestamp")
        
        # 添加请求统计信息
        request_count = stock_fetcher._get_request_count()
        rating_result["request_info"] = {
            "daily_requests_used": request_count,
            "daily_limit": stock_fetcher.daily_request_limit,
            "remaining_requests": stock_fetcher.daily_request_limit - request_count
        }
        
        logger.info(f"成功返回股票 {ticker} 的评分: {rating_result['total_score']:.1f} ({rating_result['decision']})")
        return rating_result
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"评分股票 {ticker} 时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/templates")
async def list_templates():
    """
    列出所有可用的行业模板
    
    Returns:
        所有行业模板的列表和详细信息
    """
    try:
        templates = template_manager.list_available_templates()
        template_details = {}
        
        for template_name in templates:
            info = template_manager.get_template_info(template_name)
            if info:
                template_details[template_name] = info
        
        return {
            "available_templates": templates,
            "template_details": template_details,
            "metadata": template_manager.metadata,
            "total_templates": len(templates)
        }
        
    except Exception as e:
        logger.error(f"获取模板列表时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/templates/{template_name}")
async def get_template_info(template_name: str):
    """
    获取特定行业模板的详细信息
    
    Args:
        template_name: 模板名称
        
    Returns:
        模板的详细信息
    """
    try:
        template_info = template_manager.get_template_info(template_name)
        
        if template_info is None:
            raise HTTPException(
                status_code=404,
                detail=f"模板 '{template_name}' 不存在"
            )
        
        return {
            "template_name": template_name,
            "info": template_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板信息时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.post("/templates/reload")
async def reload_templates():
    """
    重新加载行业模板配置文件
    
    Returns:
        重新加载结果
    """
    try:
        template_manager.reload_config()
        
        return {
            "message": "行业模板配置重新加载成功",
            "templates_count": len(template_manager.list_available_templates()),
            "config_file": str(template_manager.config_file),
            "metadata": template_manager.metadata
        }
        
    except Exception as e:
        logger.error(f"重新加载模板配置时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="重新加载配置失败，请检查配置文件"
        )

@app.get("/industries")
async def get_all_industries():
    """
    获取 FMP API 的所有可用行业分类
    
    Returns:
        包含所有行业分类的列表，以及行业映射建议
    """
    try:
        logger.info("开始获取 FMP 所有行业分类")
        
        # 调用 FMP API 获取行业列表
        url = f"https://financialmodelingprep.com/api/v3/industries-list?apikey={stock_fetcher.api_key}"
        
        # 使用现有的请求方法
        response = stock_fetcher._make_request(url)
        
        if response is None:
            raise HTTPException(
                status_code=500,
                detail="无法从 FMP API 获取行业列表"
            )
        
        # 提取行业名称
        industries = []
        if isinstance(response, list):
            for industry in response:
                if isinstance(industry, str):
                    # 直接是字符串数组
                    industries.append(industry)
                elif isinstance(industry, dict) and 'industry' in industry:
                    # 对象数组格式
                    industries.append(industry['industry'])
        elif isinstance(response, dict):
            # 如果响应是字典格式
            if 'industries' in response:
                industries = response['industries']
            elif 'data' in response:
                industries = response['data']
        
        # 分析现有映射
        current_mapping = template_manager.industry_mapping
        existing_industries = set(current_mapping.keys())
        
        # 分析新行业
        new_industries = []
        mapped_industries = []
        
        for industry in industries:
            if industry in existing_industries:
                mapped_industries.append({
                    "industry": industry,
                    "template": current_mapping[industry],
                    "status": "已映射"
                })
            else:
                # 为新行业提供建议
                suggested_template = _suggest_template_for_industry(industry)
                new_industries.append({
                    "industry": industry,
                    "suggested_template": suggested_template,
                    "reasoning": _get_template_reasoning(industry, suggested_template),
                    "status": "需要映射"
                })
        
        # 生成 YAML 格式的映射建议
        yaml_mapping = _generate_yaml_mapping(new_industries)
        
        result = {
            "total_industries": len(industries),
            "existing_mappings": len(mapped_industries),
            "new_industries": len(new_industries),
            "industries": {
                "mapped": mapped_industries,
                "new": new_industries
            },
            "yaml_mapping_suggestion": yaml_mapping,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"成功获取 {len(industries)} 个行业分类，其中 {len(new_industries)} 个新行业需要映射")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行业分类时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取行业分类失败: {str(e)}"
        )

def _suggest_template_for_industry(industry: str) -> str:
    """为新行业建议合适的模板"""
    industry_lower = industry.lower()
    
    # 金融相关
    if any(keyword in industry_lower for keyword in ['bank', 'financial', 'credit', 'insurance', 'asset', 'investment', 'capital', 'mortgage']):
        if 'insurance' in industry_lower:
            return 'insurance'
        return 'banking'
    
    # 科技相关
    if any(keyword in industry_lower for keyword in ['software', 'technology', 'semiconductor', 'internet', 'electronic', 'gaming', 'communication']):
        return 'technology'
    
    # 医疗相关
    if any(keyword in industry_lower for keyword in ['drug', 'medical', 'biotechnology', 'healthcare', 'pharmaceutical']):
        return 'healthcare'
    
    # 能源相关
    if any(keyword in industry_lower for keyword in ['oil', 'gas', 'energy', 'coal', 'renewable', 'petroleum']):
        return 'energy'
    
    # 消费品相关
    if any(keyword in industry_lower for keyword in ['beverage', 'food', 'packaged', 'household', 'personal', 'textile', 'apparel', 'footwear']):
        return 'consumer_goods'
    
    # 零售相关
    if any(keyword in industry_lower for keyword in ['retail', 'store', 'dealership', 'grocery', 'discount', 'department']):
        return 'retail'
    
    # 工业相关
    if any(keyword in industry_lower for keyword in ['aerospace', 'defense', 'industrial', 'machinery', 'metal', 'electrical', 'building']):
        return 'industrial'
    
    # 房地产相关
    if any(keyword in industry_lower for keyword in ['reit', 'real estate', 'property', 'development']):
        return 'real_estate'
    
    # 通信相关
    if any(keyword in industry_lower for keyword in ['telecom', 'entertainment', 'broadcasting', 'publishing', 'media']):
        return 'telecommunications'
    
    # 材料相关
    if any(keyword in industry_lower for keyword in ['chemical', 'steel', 'aluminum', 'copper', 'gold', 'silver', 'agricultural']):
        return 'materials'
    
    # 公用事业相关
    if any(keyword in industry_lower for keyword in ['utility', 'electric', 'gas', 'water', 'power']):
        return 'utilities'
    
    # 运输相关
    if any(keyword in industry_lower for keyword in ['airline', 'railroad', 'trucking', 'shipping', 'transportation', 'airport']):
        return 'transportation'
    
    # 默认使用通用模板
    return 'general'

def _get_template_reasoning(industry: str, template: str) -> str:
    """获取模板选择的理由"""
    reasoning_map = {
        'banking': '金融服务业，重视财务稳健性和风险管理',
        'technology': '科技行业，重视成长性和创新能力',
        'healthcare': '医疗保健行业，重视研发投入和专利保护',
        'energy': '能源行业，受大宗商品价格影响大',
        'consumer_goods': '消费品行业，防御性较强，现金流稳定',
        'retail': '零售业，受经济周期影响，重视运营效率',
        'industrial': '工业制造业，周期性行业，技术壁垒较高',
        'real_estate': '房地产行业，重视租金收入和资产价值',
        'telecommunications': '通信服务业，基础设施投资大，监管环境复杂',
        'materials': '材料行业，大宗商品价格敏感，周期性明显',
        'utilities': '公用事业，防御性最强，监管定价',
        'transportation': '运输业，经济周期敏感，运营效率重要',
        'general': '通用模板，适用于大多数未分类行业'
    }
    return reasoning_map.get(template, '通用模板，适用于大多数未分类行业')

def _generate_yaml_mapping(new_industries: list) -> str:
    """生成 YAML 格式的映射建议"""
    yaml_lines = ["# 新增行业映射建议", ""]
    
    for item in new_industries:
        industry = item['industry']
        template = item['suggested_template']
        reasoning = item['reasoning']
        
        yaml_lines.append(f'  "{industry}": "{template}"  # {reasoning}')
    
    return "\n".join(yaml_lines)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 