from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
from data_fetcher import StockDataFetcher
from demo_data import get_demo_stock_data

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
stock_fetcher = StockDataFetcher()

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
    获取股票完整数据
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        包含价格数据、公司信息和财务指标的完整数据
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
        
        # 调用数据获取函数
        stock_data = stock_fetcher.get_stock_data(ticker)
        
        if stock_data is None:
            logger.warning(f"无法获取股票 {ticker} 的数据")
            raise HTTPException(
                status_code=400,
                detail="无法获取数据"
            )
        
        logger.info(f"成功返回股票 {ticker} 的数据")
        return stock_data
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"获取股票 {ticker} 数据时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="无法获取数据"
        )

@app.get("/demo")
async def get_demo_data(ticker: str = Query("DEMO", max_length=10, description="股票代码，如 AAPL")):
    """
    获取演示股票数据（用于测试和展示）
    
    Args:
        ticker: 股票代码，长度不超过10个字符
        
    Returns:
        模拟的完整股票数据，包含价格、公司信息和财务指标
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
        logger.info(f"生成演示数据: {ticker}")
        demo_data = get_demo_stock_data(ticker)
        logger.info(f"成功返回演示数据: {ticker}")
        return demo_data
        
    except Exception as e:
        logger.error(f"生成演示数据时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="生成演示数据失败"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 