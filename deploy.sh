#!/bin/bash

# Stock Rookie API 部署脚本
# 用法: ./deploy.sh "commit message"

set -e  # 遇到错误立即退出

# 检查是否提供了提交信息
if [ $# -eq 0 ]; then
    echo "请提供提交信息"
    echo "用法: ./deploy.sh \"your commit message\""
    exit 1
fi

COMMIT_MSG="$1"

echo "🚀 开始部署 Stock Rookie API..."

# 检查是否有未提交的更改
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "📝 发现未提交的更改，正在提交..."
    
    # 添加所有更改
    git add .
    
    # 提交更改
    git commit -m "$COMMIT_MSG"
    
    echo "✅ 更改已提交"
else
    echo "ℹ️  没有发现未提交的更改"
fi

# 推送到GitHub
echo "📤 推送到GitHub..."
git push origin main

echo "🎉 部署完成！"
echo "📋 项目地址: $(git remote get-url origin)"
echo "📚 API文档: http://localhost:8000/docs (本地运行时)"
