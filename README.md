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
- **价格数据**：5年历史日线数据（开盘、收盘、最高、最低、成交量）
- **公司信息**：基本面信息、行业分类、市值等
- **财务指标**：
  - 盈利能力：ROE、ROA、毛利率、净利率
  - 成长性：EPS增长、营收增长
  - 偿债能力：负债率、流动比率
  - 估值指标：PE、PB、PS比率
  - 现金流：自由现金流、经营现金流

## 📋 项目结构

```
stock-rookie/
├── main.py                 # FastAPI应用入口
├── data_fetcher.py         # 股票数据抓取模块
├── scoring.py              # 股票评分逻辑
├── demo_data.py            # 演示数据生成
├── lambda_handler.py       # AWS Lambda适配器
├── requirements.txt        # Python依赖
├── industry_templates.yaml # 行业评分权重模板
└── README.md              # 项目文档
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
uvicorn main:app --reload
```

4. **访问API**
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/ping

### Docker部署

```bash
# 构建镜像
docker build -t stock-rookie .

# 运行容器
docker run -p 8000:8000 stock-rookie
```

## 📚 API接口

### 基础接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 欢迎信息 |
| GET | `/ping` | 健康检查 |
| GET | `/health` | 详细健康状态 |

### 数据接口

| 方法 | 路径 | 参数 | 描述 |
|------|------|------|------|
| GET | `/data` | `ticker` | 获取真实股票数据 |
| GET | `/demo` | `ticker` | 获取演示股票数据 |

### 使用示例

```bash
# 获取苹果公司股票数据
curl "http://localhost:8000/data?ticker=AAPL"

# 获取演示数据
curl "http://localhost:8000/demo?ticker=AAPL"
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

## ☁️ AWS Lambda部署

### 准备部署包

```bash
# 安装依赖到本地目录
pip install -r requirements.txt -t ./lambda-deployment

# 复制源代码
cp *.py lambda-deployment/

# 创建部署包
cd lambda-deployment
zip -r ../stock-rookie-lambda.zip .
```

### Lambda配置

- **Runtime**: Python 3.11
- **Handler**: `lambda_handler.lambda_handler`
- **Memory**: 512MB
- **Timeout**: 30秒

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 🧪 测试

```bash
# 运行基本测试
python -m pytest

# 测试API接口
curl http://localhost:8000/ping
curl "http://localhost:8000/demo?ticker=AAPL"
```

## 📊 性能特性

- **高并发**：基于FastAPI的异步处理
- **缓存优化**：数据获取缓存机制
- **错误处理**：完善的异常处理和日志记录
- **参数验证**：自动参数校验和错误提示

## 🔧 技术栈

- **后端框架**: FastAPI
- **数据源**: Yahoo Finance (yfinance)
- **数据处理**: Pandas, NumPy
- **部署**: Uvicorn, AWS Lambda (Mangum)
- **文档**: 自动生成OpenAPI/Swagger文档

## 📈 路线图

- [ ] 添加更多数据源支持
- [ ] 实现股票筛选功能
- [ ] 添加技术指标计算
- [ ] 支持投资组合分析
- [ ] 集成机器学习预测模型

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目地址: [https://github.com/your-username/stock-rookie](https://github.com/your-username/stock-rookie)
- 问题反馈: [Issues](https://github.com/your-username/stock-rookie/issues)

---

⭐ 如果这个项目对您有帮助，请给它一个星标！
