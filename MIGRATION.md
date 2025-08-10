# 🔄 API数据源迁移说明

## 📊 迁移概述

Stock Rookie API 已成功从 **Yahoo Finance** 迁移到 **Financial Modeling Prep (FMP) API**

### 🎯 迁移原因
- Yahoo Finance API频繁出现429错误（请求过多）
- 数据获取不稳定，影响用户体验
- FMP提供更稳定、专业的金融数据服务

### 📈 迁移优势
- ✅ **更稳定的数据源**：专业的金融数据API
- ✅ **更丰富的数据**：包含更多财务指标和公司信息
- ✅ **更好的性能**：响应速度更快，错误更少
- ✅ **专业级别**：机构级数据质量

## 🔧 技术变更

### 新增依赖
```bash
pip install requests python-dotenv
```

### 环境变量配置
创建 `.env` 文件：
```bash
FMP_API_KEY=your_api_key_here
CACHE_DIR=./cache
CACHE_DURATION_HOURS=24
DAILY_REQUEST_LIMIT=80
MIN_REQUEST_INTERVAL=1.0
MAX_REQUEST_INTERVAL=3.0
```

### 核心变更
- **数据源**: `yahoo_finance` → `financial_modeling_prep`
- **主类**: `StockDataFetcher` → `FMPStockDataFetcher`
- **依赖**: `yfinance` → `requests` + `python-dotenv`

## 📋 API接口保持不变

### 🔄 缓存接口
```http
GET /data?ticker=AAPL
```
- 优先使用缓存数据
- 24小时缓存有效期
- 节省API请求次数

### 🔥 最新数据接口  
```http
GET /data/fresh?ticker=AAPL
```
- 强制获取最新数据
- 跳过缓存机制
- 消耗API请求次数

### 📊 状态监控
```http
GET /status
```
- 显示FMP API连接状态
- API key配置检查
- 缓存系统状态

## 📊 数据结构对比

### 响应格式保持一致
```json
{
  "ticker": "AAPL",
  "data_source": "financial_modeling_prep",  // 变更
  "timestamp": "2025-08-10T00:28:04.414373",
  "price_data": [...],
  "company_info": {...},
  "financial_metrics": {...},
  "request_info": {
    "cache_mode": "enabled",
    "daily_requests_used": 1,
    "daily_limit": 80
  }
}
```

### 数据质量提升
- **历史价格数据**: 5年完整数据，更准确
- **公司信息**: 更详细的行业分类和公司资料
- **财务指标**: 更多专业指标（ROE, ROA, 债务比率等）
- **实时数据**: 当日价格、涨跌幅、成交量等

## 🔒 安全性改进

### API密钥保护
- 使用环境变量存储API密钥
- `.env` 文件已添加到 `.gitignore`
- 提供 `env.example` 作为配置模板

### 请求限制
- 每日80次请求限制
- 1-3秒随机延迟保护
- 智能缓存机制减少API调用

## 🚀 部署说明

### 本地开发
1. 复制 `env.example` 为 `.env`
2. 配置 `FMP_API_KEY`
3. 安装新依赖：`pip install -r requirements.txt`
4. 启动服务：`uvicorn main:app --reload`

### 生产环境
1. 设置环境变量 `FMP_API_KEY`
2. 配置其他可选环境变量
3. 确保 `.env` 文件不被部署到生产环境

### AWS Lambda
- `lambda_handler.py` 保持不变
- 在AWS Lambda环境中设置环境变量

## 📈 性能监控

### 请求统计
- 每日请求次数跟踪
- 缓存命中率监控
- API响应时间记录

### 健康检查
- `/status` 端点监控API状态
- 缓存系统健康检查
- 请求限制状态监控

## 🎉 迁移完成

✅ **数据源**: Yahoo Finance → Financial Modeling Prep  
✅ **稳定性**: 大幅提升  
✅ **数据质量**: 专业级别  
✅ **API接口**: 完全兼容  
✅ **缓存机制**: 优化升级  
✅ **安全性**: 环境变量保护  

---

*迁移日期: 2025年8月10日*  
*API版本: v2.0*  
*数据源: Financial Modeling Prep*
