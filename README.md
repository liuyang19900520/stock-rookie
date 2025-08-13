# Stock Rookie API 📈

一个功能完整的股票数据分析API，支持本地开发和AWS Lambda部署。

## 🚀 功能特性

### 核心功能
- **股票数据获取**：通过yfinance获取实时和历史股票数据
- **全面财务分析**：包含50+财务指标和比率
- **智能评分系统**：多维度股票评分和投资建议
- **RESTful API**：基于FastAPI的高性能API接口
- **云原生部署**：支持AWS Lambda无服务器部署

### 数据覆盖
- **公司信息**：基本面信息、行业分类、市值等
- **财务指标**：
  - 盈利能力：ROE、ROA、毛利率、净利率
  - 成长性：EPS增长、营收增长
  - 偿债能力：负债率、流动比率
  - 估值指标：PE、PB、PS比率
  - 现金流：自由现金流、经营现金流
- **动态行业对比**：
  - 同行业市值前10企业平均值
  - 全行业平均值
  - 同行业成交量前10企业平均值

## 📋 项目结构

```
stock-rookie/
├── main.py                    # FastAPI应用入口
├── data_fetcher.py            # 股票数据抓取模块（简化版）
├── financial_analysis.py      # 财务分析和SWOT分析模块
├── scoring.py                 # 股票评分逻辑
├── cors_config.py             # CORS配置
├── start_server.py            # 服务器启动脚本
├── requirements.txt           # Python依赖
├── env.example                # 环境变量示例
├── industry_templates.yaml    # 行业评分权重模板
├── industry_templates_updated.yaml # 更新的行业模板
├── API.md                     # 详细API文档
└── README.md                  # 项目文档
```

## 🛠️ 快速开始

### 本地开发

1. **克隆项目**
```bash
git clone https://github.com/your-username/stock-rookie.git
cd stock-rookie
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动服务**

```bash
# 开发环境启动（推荐）
python start_server.py --env development --port 8000

# 或者直接使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. **访问API**
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/ping

### CORS配置

项目已配置跨域资源共享（CORS）支持，解决前端应用访问API时的跨域问题：

- **开发环境**：允许所有来源，适合本地开发
- **生产环境**：只允许预定义域名，更安全
- **测试环境**：允许测试域名和本地开发域名

配置详情请查看 `cors_config.py` 文件。



## 📚 API接口

详细的API文档请参考 [API.md](API.md)

### 主要端点

| 方法 | 路径 | 参数 | 描述 |
|------|------|------|------|
| GET | `/` | - | 欢迎信息 |
| GET | `/ping` | - | 健康检查 |
| GET | `/health` | - | 详细健康状态 |
| GET | `/status` | - | API状态 |
| GET | `/data` | `ticker` | 获取股票基础数据 |
| GET | `/score` | `ticker` | 获取股票评分 |
| GET | `/analysis/financial` | `ticker` | 获取详细财务分析 |
| GET | `/analysis/swot` | `ticker` | 获取SWOT分析 |
| GET | `/analysis/dashboard` | `ticker` | 获取完整仪表板数据 |
| GET | `/templates` | - | 获取行业模板列表 |
| GET | `/templates/{name}` | `name` | 获取特定模板详情 |
| GET | `/analysis/financial` | `ticker` | 获取详细财务分析 |
| GET | `/analysis/swot` | `ticker` | 获取SWOT分析 |
| GET | `/analysis/dashboard` | `ticker` | 获取完整仪表板数据 |

### 使用示例

```bash
# 获取苹果公司股票数据
curl "http://localhost:8000/data?ticker=AAPL"

# 获取演示数据
curl "http://localhost:8000/demo?ticker=AAPL"

# 获取股票评分
curl "http://localhost:8000/score?ticker=AAPL"

# 获取详细财务分析
curl "http://localhost:8000/analysis/financial?ticker=AAPL"

# 获取SWOT分析
curl "http://localhost:8000/analysis/swot?ticker=AAPL"

# 获取完整仪表板数据
curl "http://localhost:8000/analysis/dashboard?ticker=AAPL"
```

### 响应格式

```json
{
  "price_data": [
    {
      "date": "2024-01-01",
      "open": 150.0,
      "high": 155.0,
      "low": 148.0,
      "close": 152.0,
      "volume": 1000000
    }
  ],
  "company_info": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "sector": "Technology",
    "market_cap": 2800000000000
  },
  "financial_metrics": {
    "return_on_equity": 0.25,
    "profit_margins": 0.21,
    "trailing_pe": 24.5,
    "beta": 1.15
  }
}
```

## 🧪 测试

```bash
# 测试API接口
curl http://localhost:8000/ping
curl "http://localhost:8000/data?ticker=AAPL"
curl "http://localhost:8000/score?ticker=AAPL"
```

## 📊 性能特性

- **高并发**：基于FastAPI的异步处理
- **实时数据**：直接从FMP API获取最新数据
- **错误处理**：完善的异常处理和日志记录
- **参数验证**：自动参数校验和错误提示

## 🔧 技术栈

- **后端框架**: FastAPI
- **数据源**: Financial Modeling Prep (FMP) API
- **数据处理**: Pandas, NumPy
- **部署**: Uvicorn
- **文档**: 自动生成OpenAPI/Swagger文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

⭐ 如果这个项目对您有帮助，请给它一个星标！
