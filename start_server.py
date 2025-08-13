#!/usr/bin/env python3
"""
服务器启动脚本
支持不同环境的CORS配置
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path

def setup_environment(env):
    """设置环境变量"""
    os.environ["ENVIRONMENT"] = env
    print(f"✅ 环境设置为: {env}")

def load_env_file():
    """加载.env文件"""
    env_file = Path(".env")
    if env_file.exists():
        print("📁 发现.env文件，正在加载环境变量...")
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载完成")
    else:
        print("⚠️  未发现.env文件，使用默认配置")

def print_cors_info(env):
    """打印CORS配置信息"""
    print("\n" + "="*50)
    print("🌐 CORS 配置信息")
    print("="*50)
    
    if env == "development":
        print("🔧 开发环境配置:")
        print("   - 允许所有来源 (*)")
        print("   - 允许所有HTTP方法")
        print("   - 允许所有请求头")
        print("   - 适合本地开发使用")
    elif env == "production":
        print("🚀 生产环境配置:")
        print("   - 只允许预定义的域名")
        print("   - 限制HTTP方法")
        print("   - 限制请求头")
        print("   - 更安全的配置")
    elif env == "test":
        print("🧪 测试环境配置:")
        print("   - 允许测试域名和本地开发域名")
        print("   - 介于开发和生产环境之间")
    
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description="启动Stock Rookie API服务器")
    parser.add_argument(
        "--env", 
        choices=["development", "test", "production"],
        default="development",
        help="运行环境 (默认: development)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载 (仅开发环境)"
    )
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment(args.env)
    
    # 加载环境变量
    load_env_file()
    
    # 打印CORS信息
    print_cors_info(args.env)
    
    # 配置服务器参数
    server_config = {
        "app": "main:app",
        "host": args.host,
        "port": args.port,
        "log_level": "info"
    }
    
    # 开发环境启用重载
    if args.env == "development" and args.reload:
        server_config["reload"] = True
        print("🔄 启用自动重载模式")
    
    print(f"\n🚀 启动服务器...")
    print(f"   环境: {args.env}")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   API文档: http://{args.host}:{args.port}/docs")
    print(f"   健康检查: http://{args.host}:{args.port}/health")
    print("\n按 Ctrl+C 停止服务器\n")
    
    try:
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动服务器时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
