from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
from data_fetcher import FMPStockDataFetcher
from scoring import score_stock, template_manager
from cors_config import get_cors_config, get_dev_cors_config
from financial_analysis import FinancialAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Stock Rookie API",
    description="股票投资分析 API",
    version="1.0.0"
)

# 配置 CORS 中间件
import os
environment = os.getenv("ENVIRONMENT", "development").lower()

if environment == "development":
    # 开发环境使用宽松配置
    cors_config = get_dev_cors_config()
    logger.info("使用开发环境CORS配置（允许所有来源）")
else:
    # 生产环境使用严格配置
    cors_config = get_cors_config()
    logger.info(f"使用{environment}环境CORS配置")

app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# 创建数据获取器实例
stock_fetcher = FMPStockDataFetcher()
financial_analyzer = FinancialAnalyzer()

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
async def get_stock_data(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取股票数据（简化版本）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含公司信息和财务指标的字典
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
        logger.info(f"开始处理股票数据请求: {ticker}")
        
        # 获取数据
        stock_data = stock_fetcher.get_stock_data(ticker)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=500,
                detail="无法获取股票数据，请稍后重试"
            )
        
        logger.info(f"成功返回股票 {ticker} 的数据")
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
    from datetime import datetime
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "api_version": "3.0.0",
        "status": "operational",
        "services": {
            "fmp_api": {"status": "unknown", "description": "Financial Modeling Prep API数据源"},
            "rate_limiting": {"status": "disabled", "description": "无限制模式"}
        }
    }
    
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
        stock_data = stock_fetcher.get_stock_data(ticker)
        
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

@app.get("/analysis/financial")
async def get_financial_analysis(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取详细的财务分析数据
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含关键财务指标、行业对比、增长率等详细分析数据
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
        logger.info(f"开始处理财务分析请求: {ticker}")
        
        # 获取股票数据以确定行业
        stock_data = stock_fetcher.get_stock_data(ticker)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=500,
                detail="无法获取股票数据，请稍后重试"
            )
        
        # 确定行业
        company_info = stock_data.get("company_info", {})
        fmp_industry = company_info.get("industry", "General")
        
        # 映射到模板行业
        industry = template_manager.map_fmp_industry(fmp_industry)
        
        # 获取详细财务分析
        financial_analysis = financial_analyzer.get_detailed_financial_metrics(ticker, industry, fmp_industry)
        
        # 添加基础信息
        result = {
            "ticker": ticker,
            "industry": industry,
            "fmp_industry": fmp_industry,
            "timestamp": datetime.now().isoformat(),
            "financial_analysis": financial_analysis
        }
        
        logger.info(f"成功返回股票 {ticker} 的财务分析")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 财务分析时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/analysis/swot")
async def get_swot_analysis(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取SWOT分析
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含优势、劣势、机会、威胁的SWOT分析
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
        logger.info(f"开始处理SWOT分析请求: {ticker}")
        
        # 获取股票数据以确定行业
        stock_data = stock_fetcher.get_stock_data(ticker)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=500,
                detail="无法获取股票数据，请稍后重试"
            )
        
        # 确定行业
        company_info = stock_data.get("company_info", {})
        fmp_industry = company_info.get("industry", "General")
        
        # 映射到模板行业
        industry = template_manager.map_fmp_industry(fmp_industry)
        
        # 生成SWOT分析
        swot_analysis = financial_analyzer.generate_swot_analysis(ticker, industry)
        
        # 添加基础信息
        result = {
            "ticker": ticker,
            "industry": industry,
            "fmp_industry": fmp_industry,
            "timestamp": datetime.now().isoformat(),
            "swot_analysis": swot_analysis
        }
        
        logger.info(f"成功返回股票 {ticker} 的SWOT分析")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} SWOT分析时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@app.get("/analysis/dashboard")
async def get_dashboard_data(ticker: str = Query(..., max_length=10, description="股票代码，如 AAPL")):
    """
    获取仪表板完整数据（包含财务指标、SWOT分析、评分等）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含所有分析数据的完整仪表板数据
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
        logger.info(f"开始处理仪表板数据请求: {ticker}")
        
        # 获取股票数据
        stock_data = stock_fetcher.get_stock_data(ticker)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=500,
                detail="无法获取股票数据，请稍后重试"
            )
        
        # 确定行业
        company_info = stock_data.get("company_info", {})
        fmp_industry = company_info.get("industry", "General")
        industry = template_manager.map_fmp_industry(fmp_industry)
        
        # 获取评分
        rating_result = score_stock(stock_data)
        
        # 获取财务分析
        financial_analysis = financial_analyzer.get_detailed_financial_metrics(ticker, industry, fmp_industry)
        
        # 获取SWOT分析
        swot_analysis = financial_analyzer.generate_swot_analysis(ticker, industry)
        
        # 构建仪表板数据
        dashboard_data = {
            "ticker": ticker,
            "company_info": company_info,
            "industry": industry,
            "fmp_industry": fmp_industry,
            "timestamp": datetime.now().isoformat(),
            
            # 关键财务指标
            "key_financial_indicators": financial_analysis.get("key_indicators", {}),
            "industry_comparison": financial_analysis.get("industry_comparison", {}),
            
            # SWOT分析
            "swot_analysis": swot_analysis,
            
            # 评分结果
            "scoring": rating_result,
            
            # 详细财务指标
            "financial_metrics": {
                "growth_metrics": financial_analysis.get("growth_metrics", {}),
                "efficiency_metrics": financial_analysis.get("efficiency_metrics", {}),
                "liquidity_metrics": financial_analysis.get("liquidity_metrics", {}),
                "profitability_metrics": financial_analysis.get("profitability_metrics", {}),
                "valuation_metrics": financial_analysis.get("valuation_metrics", {})
            }
        }
        
        # 添加请求统计信息
        request_count = stock_fetcher._get_request_count()
        dashboard_data["request_info"] = {
            "daily_requests_used": request_count,
            "daily_limit": stock_fetcher.daily_request_limit,
            "remaining_requests": stock_fetcher.daily_request_limit - request_count
        }
        
        logger.info(f"成功返回股票 {ticker} 的仪表板数据")
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 仪表板数据时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
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