"""
CORS 配置模块
提供不同环境下的跨域资源共享配置
"""

import os
from typing import List

# 开发环境允许的源
DEV_ORIGINS = [
    "http://localhost:3000",      # React 开发服务器
    "http://localhost:8080",      # Vue 开发服务器
    "http://localhost:4200",      # Angular 开发服务器
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:4200",
    "http://localhost:5173",      # Vite 开发服务器
    "http://127.0.0.1:5173",
]

# 生产环境允许的源（需要根据实际部署情况修改）
PROD_ORIGINS = [
    "https://yourdomain.com",     # 替换为你的实际域名
    "https://www.yourdomain.com", # 替换为你的实际域名
    "https://app.yourdomain.com", # 替换为你的实际域名
]

# 测试环境允许的源
TEST_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://test.yourdomain.com", # 替换为你的测试域名
]

def get_cors_origins() -> List[str]:
    """
    根据环境变量获取CORS允许的源
    
    Returns:
        List[str]: 允许的源列表
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return PROD_ORIGINS
    elif environment == "test":
        return TEST_ORIGINS
    else:
        return DEV_ORIGINS

def get_cors_config():
    """
    获取CORS配置字典
    
    Returns:
        dict: CORS配置
    """
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
        ],
    }

# 开发环境下的宽松配置（仅用于开发）
def get_dev_cors_config():
    """
    获取开发环境的宽松CORS配置
    
    Returns:
        dict: 开发环境CORS配置
    """
    return {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
