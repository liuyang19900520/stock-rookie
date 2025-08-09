from mangum import Mangum
from main import app

# 使用 Mangum 将 FastAPI 应用转换为 AWS Lambda 处理器
handler = Mangum(app, lifespan="off")

# Lambda 入口函数
def lambda_handler(event, context):
    """
    AWS Lambda 入口函数
    
    Args:
        event: Lambda 事件对象
        context: Lambda 上下文对象
        
    Returns:
        HTTP 响应
    """
    return handler(event, context) 