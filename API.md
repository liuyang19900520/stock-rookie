# Stock Rookie API 文档

## 概述

Stock Rookie API 是一个股票投资分析API，提供股票数据获取、财务分析、评分和SWOT分析功能。

- **基础URL**: `http://localhost:8000`
- **数据源**: Financial Modeling Prep (FMP) API
- **版本**: 3.0.0
- **特点**: 无缓存、无请求限制、实时数据

## 快速开始

### 启动服务器

```bash
# 开发环境
python start_server.py --env development --port 8000

# 或直接使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 基础端点

#### 1. 欢迎信息
```http
GET /
```

**响应示例**:
```json
{
  "message": "Welcome to Stock Rookie API"
}
```

#### 2. 健康检查
```http
GET /ping
```

**响应示例**:
```json
{
  "status": "ok"
}
```

#### 3. 详细健康状态
```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "service": "stock-rookie-api",
  "version": "1.0.0"
}
```

#### 4. API状态
```http
GET /status
```

**响应示例**:
```json
{
  "timestamp": "2025-08-14T00:20:19.301176",
  "api_version": "3.0.0",
  "status": "operational",
  "services": {
    "fmp_api": {
      "status": "healthy",
      "description": "Financial Modeling Prep API数据源",
      "api_key_configured": true
    },
    "rate_limiting": {
      "status": "disabled",
      "description": "无限制模式"
    }
  }
}
```

### 数据端点

#### 5. 获取股票基础数据
```http
GET /data?ticker={ticker}
```

**参数**:
- `ticker` (必需): 股票代码，如 AAPL、DIS

**响应示例**:
```json
{
  "ticker": "AAPL",
  "company_info": {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "industry": "Technology",
    "sector": "Consumer Electronics",
    "country": "US",
    "exchange": "NASDAQ",
    "market_cap": 3000000000000,
    "employees": 164000,
    "website": "https://www.apple.com",
    "description": "Apple Inc. designs, manufactures, and markets smartphones...",
    "ceo": "Tim Cook"
  },
  "financial_metrics": {
    "pe_ratio": 25.5,
    "pb_ratio": 15.2,
    "ps_ratio": 6.8,
    "dividend_yield": 0.5,
    "roe": 150.2,
    "roa": 25.8,
    "debt_to_equity": 1.2,
    "current_ratio": 1.1,
    "gross_profit_margin": 42.5,
    "net_profit_margin": 25.8
  },
  "data_source": "financial_modeling_prep",
  "timestamp": "2025-08-14T00:20:19.301176"
}
```

### 分析端点

#### 6. 股票评分
```http
GET /score?ticker={ticker}
```

**参数**:
- `ticker` (必需): 股票代码

**响应示例**:
```json
{
  "ticker": "AAPL",
  "total_score": 85.5,
  "decision": "买入",
  "category_scores": {
    "profitability": 90.0,
    "growth": 85.0,
    "financial_health": 80.0,
    "valuation": 75.0
  },
  "timestamp": "2025-08-14T00:20:19.301176"
}
```

#### 7. 详细财务分析
```http
GET /analysis/financial?ticker={ticker}
```

**参数**:
- `ticker` (必需): 股票代码

**响应示例**:
```json
{
  "ticker": "AAPL",
  "industry": "technology",
  "fmp_industry": "Technology",
  "timestamp": "2025-08-14T00:20:19.301176",
  "financial_analysis": {
    "key_indicators": {
      "pe_ratio": 25.5,
      "pb_ratio": 15.2,
      "ps_ratio": 6.8,
      "dividend_yield": 0.5,
      "roe": 150.2,
      "roa": 25.8,
      "debt_to_equity": 1.2,
      "current_ratio": 1.1,
      "gross_profit_margin": 42.5,
      "net_profit_margin": 25.8
    },
    "industry_comparison": {
      "pe_ratio": {
        "company": 25.5,
        "industry_avg": 18.0,
        "status": "worse"
      },
      "roe": {
        "company": 150.2,
        "industry_avg": 15.0,
        "status": "better"
      }
    },
    "dynamic_industry_averages": {
      "top_market_cap": {
        "pe_ratio": 29.71,
        "pb_ratio": 27.75,
        "ps_ratio": 2.13,
        "dividend_yield": 0.008,
        "roe": 0.50,
        "debt_to_equity": 4.74,
        "current_ratio": 0.98
      },
      "all_industry": {
        "pe_ratio": 29.52,
        "pb_ratio": 15.58,
        "ps_ratio": 2.09,
        "dividend_yield": 0.009,
        "roe": 0.25,
        "debt_to_equity": 2.95,
        "current_ratio": 1.06
      },
      "top_volume": {
        "pe_ratio": 19.05,
        "pb_ratio": 0.85,
        "ps_ratio": 1.05,
        "dividend_yield": 0.23,
        "roe": 0.17,
        "debt_to_equity": -0.43,
        "current_ratio": 0.87
      }
    },
    "growth_metrics": {
      "revenue_growth": 0.05,
      "net_income_growth": 0.12,
      "eps_growth": 0.15,
      "operating_cash_flow_growth": 0.08,
      "free_cash_flow_growth": 0.10
    },
    "efficiency_metrics": {
      "asset_turnover": 0.8,
      "inventory_turnover": 25.5,
      "receivables_turnover": 12.3
    },
    "liquidity_metrics": {
      "current_ratio": 1.1,
      "quick_ratio": 0.9,
      "cash_ratio": 0.3
    },
    "profitability_metrics": {
      "gross_margin": 42.5,
      "operating_margin": 30.2,
      "net_margin": 25.8,
      "return_on_equity": 150.2,
      "return_on_assets": 25.8
    },
    "valuation_metrics": {
      "enterprise_value": 3500000000000,
      "ev_to_ebitda": 20.5,
      "ev_to_revenue": 6.8,
      "price_to_book": 15.2,
      "price_to_sales": 6.8
    }
  }
}
```

#### 8. SWOT分析
```http
GET /analysis/swot?ticker={ticker}
```

**参数**:
- `ticker` (必需): 股票代码

**响应示例**:
```json
{
  "ticker": "AAPL",
  "industry": "technology",
  "fmp_industry": "Technology",
  "timestamp": "2025-08-14T00:20:19.301176",
  "swot_analysis": {
    "strengths": [
      "强大的品牌价值和市场地位",
      "优秀的盈利能力（ROE: 150.2%）",
      "稳定的现金流和财务状况",
      "创新的产品组合和生态系统"
    ],
    "weaknesses": [
      "对iPhone产品的依赖度过高",
      "市盈率相对较高（25.5倍）",
      "供应链集中度风险"
    ],
    "opportunities": [
      "服务业务增长潜力巨大",
      "新兴市场扩张机会",
      "AI和AR技术发展机遇"
    ],
    "threats": [
      "激烈的市场竞争",
      "监管政策变化风险",
      "技术变革带来的挑战"
    ]
  }
}
```

#### 9. 完整仪表板数据
```http
GET /analysis/dashboard?ticker={ticker}
```

**参数**:
- `ticker` (必需): 股票代码

**响应示例**:
```json
{
  "ticker": "AAPL",
  "company_info": {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "industry": "Technology",
    "sector": "Consumer Electronics"
  },
  "industry": "technology",
  "fmp_industry": "Technology",
  "timestamp": "2025-08-14T00:20:19.301176",
  "key_financial_indicators": {
    "pe_ratio": 25.5,
    "pb_ratio": 15.2,
    "ps_ratio": 6.8,
    "dividend_yield": 0.5,
    "roe": 150.2,
    "roa": 25.8,
    "debt_to_equity": 1.2,
    "current_ratio": 1.1
  },
  "industry_comparison": {
    "top_market_cap": {
      "pe_ratio": 29.71,
      "pb_ratio": 27.75,
      "ps_ratio": 2.13
    },
    "all_industry": {
      "pe_ratio": 29.52,
      "pb_ratio": 15.58,
      "ps_ratio": 2.09
    },
    "top_volume": {
      "pe_ratio": 19.05,
      "pb_ratio": 0.85,
      "ps_ratio": 1.05
    }
  },
  "swot_analysis": {
    "strengths": ["强大的品牌价值", "优秀的盈利能力"],
    "weaknesses": ["产品依赖度高", "市盈率较高"],
    "opportunities": ["服务业务增长", "新兴市场扩张"],
    "threats": ["激烈竞争", "监管风险"]
  },
  "scoring": {
    "total_score": 85.5,
    "decision": "买入",
    "category_scores": {
      "profitability": 90.0,
      "growth": 85.0,
      "financial_health": 80.0,
      "valuation": 75.0
    }
  },
  "financial_metrics": {
    "growth_metrics": {
      "revenue_growth": 0.05,
      "net_income_growth": 0.12,
      "eps_growth": 0.15
    },
    "efficiency_metrics": {
      "asset_turnover": 0.8,
      "inventory_turnover": 25.5
    },
    "liquidity_metrics": {
      "current_ratio": 1.1,
      "quick_ratio": 0.9
    },
    "profitability_metrics": {
      "gross_margin": 42.5,
      "operating_margin": 30.2,
      "net_margin": 25.8
    },
    "valuation_metrics": {
      "enterprise_value": 3500000000000,
      "ev_to_ebitda": 20.5,
      "price_to_book": 15.2
    }
  }
}
```

### 模板端点

#### 10. 获取行业模板列表
```http
GET /templates
```

**响应示例**:
```json
{
  "available_templates": [
    "technology",
    "healthcare",
    "financial",
    "consumer_goods",
    "energy",
    "telecommunications"
  ],
  "template_details": {
    "technology": {
      "name": "科技行业",
      "description": "科技公司评分模板",
      "weights": {
        "profitability": 0.3,
        "growth": 0.3,
        "financial_health": 0.2,
        "valuation": 0.2
      }
    }
  },
  "total_templates": 6
}
```

#### 11. 获取特定模板详情
```http
GET /templates/{template_name}
```

**参数**:
- `template_name` (路径参数): 模板名称

**响应示例**:
```json
{
  "name": "科技行业",
  "description": "科技公司评分模板",
  "weights": {
    "profitability": 0.3,
    "growth": 0.3,
    "financial_health": 0.2,
    "valuation": 0.2
  },
  "thresholds": {
    "buy": 80,
    "hold": 60,
    "sell": 40
  }
}
```

## 数据字段说明

### 财务指标

| 字段 | 描述 | 单位 |
|------|------|------|
| pe_ratio | 市盈率 | 倍数 |
| pb_ratio | 市净率 | 倍数 |
| ps_ratio | 市销率 | 倍数 |
| dividend_yield | 股息率 | 百分比 |
| roe | 净资产收益率 | 百分比 |
| roa | 总资产收益率 | 百分比 |
| debt_to_equity | 债务权益比 | 倍数 |
| current_ratio | 流动比率 | 倍数 |
| gross_profit_margin | 毛利率 | 百分比 |
| net_profit_margin | 净利率 | 百分比 |

### 动态行业平均数据

API提供三种动态行业平均数据：

1. **top_market_cap**: 同行业市值前10企业的平均值
2. **all_industry**: 全行业所有企业的平均值
3. **top_volume**: 同行业本周内成交量前10企业的平均值

### 行业对比状态

| 状态 | 描述 |
|------|------|
| better | 优于行业平均 |
| similar | 与行业平均相似 |
| worse | 低于行业平均 |
| no_data | 无数据 |

## 错误处理

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 使用示例

### Python示例

```python
import requests

# 获取股票基础数据
response = requests.get("http://localhost:8000/data?ticker=AAPL")
data = response.json()
print(f"公司名称: {data['company_info']['company_name']}")

# 获取股票评分
response = requests.get("http://localhost:8000/score?ticker=AAPL")
score = response.json()
print(f"评分: {score['total_score']}, 决策: {score['decision']}")

# 获取完整仪表板数据
response = requests.get("http://localhost:8000/analysis/dashboard?ticker=AAPL")
dashboard = response.json()
print(f"SWOT分析: {dashboard['swot_analysis']['strengths']}")
```

### JavaScript示例

```javascript
// 获取股票基础数据
fetch('http://localhost:8000/data?ticker=AAPL')
  .then(response => response.json())
  .then(data => {
    console.log('公司名称:', data.company_info.company_name);
  });

// 获取股票评分
fetch('http://localhost:8000/score?ticker=AAPL')
  .then(response => response.json())
  .then(score => {
    console.log('评分:', score.total_score, '决策:', score.decision);
  });
```

## 注意事项

1. **API限制**: 当前版本无请求限制，但建议合理控制请求频率
2. **数据实时性**: 所有数据都从FMP API实时获取，无缓存
3. **股票代码**: 支持美股代码，如AAPL、GOOGL、MSFT等
4. **行业映射**: 自动将FMP行业分类映射到内部模板
5. **错误处理**: 建议实现适当的错误重试机制

## 更新日志

### v3.0.0 (2025-08-14)
- 移除缓存系统
- 移除请求限制
- 移除价格数据
- 简化API端点
- 优化响应速度
- 添加动态行业平均数据
