# Stock Rookie API 端点总结

## 📊 数据获取端点

### 1. 带请求限制的端点（兼容版本）

#### `/data` - 获取股票数据（缓存模式）
- **描述**: 获取股票完整数据，优先使用缓存
- **请求限制**: ✅ 有每日请求限制
- **缓存**: ✅ 启用
- **用途**: 日常使用，节省 API 调用次数

```bash
curl -X GET "http://localhost:8000/data?ticker=AAPL"
```

#### `/data/fresh` - 获取股票数据（强制刷新）
- **描述**: 强制从 API 获取最新数据，不使用缓存
- **请求限制**: ✅ 有每日请求限制
- **缓存**: ❌ 跳过缓存
- **用途**: 需要最新数据时使用

```bash
curl -X GET "http://localhost:8000/data/fresh?ticker=AAPL"
```

### 2. 无请求限制的端点（新版本）

#### `/data/unlimited` - 获取股票数据（无限制版本）
- **描述**: 获取股票完整数据，无每日请求限制
- **请求限制**: ❌ 无每日限制
- **缓存**: ✅ 启用
- **速率限制**: ✅ 仅用于 API 保护（1-3秒延迟）
- **用途**: 推荐使用，适合高频调用

```bash
curl -X GET "http://localhost:8000/data/unlimited?ticker=AAPL"
```

#### `/data/unlimited/fresh` - 获取股票数据（无限制版本，强制刷新）
- **描述**: 强制从 API 获取最新数据，无每日请求限制
- **请求限制**: ❌ 无每日限制
- **缓存**: ❌ 跳过缓存
- **速率限制**: ✅ 仅用于 API 保护（1-3秒延迟）
- **用途**: 需要最新数据且无限制时使用

```bash
curl -X GET "http://localhost:8000/data/unlimited/fresh?ticker=AAPL"
```

## 📈 评分端点

### `/score` - 股票评分
- **描述**: 基于行业模板的股票评分
- **数据源**: 使用 `/data` 端点获取数据
- **用途**: 价值投资决策支持

```bash
curl -X GET "http://localhost:8000/score?ticker=AAPL"
```

## 🏭 行业分析端点

### `/industries` - 获取所有行业分类
- **描述**: 获取 FMP API 的所有行业分类及映射建议
- **用途**: 行业模板配置和更新

```bash
curl -X GET "http://localhost:8000/industries"
```

### `/templates` - 获取模板列表
- **描述**: 获取所有可用的行业评分模板
- **用途**: 查看当前配置的模板

```bash
curl -X GET "http://localhost:8000/templates"
```

### `/templates/{template_name}` - 获取特定模板信息
- **描述**: 获取指定模板的详细配置
- **用途**: 查看特定行业的评分配置

```bash
curl -X GET "http://localhost:8000/templates/banking"
```

### `/templates/reload` - 重新加载模板配置
- **描述**: 重新加载行业模板配置文件
- **方法**: POST
- **用途**: 配置更新后重新加载

```bash
curl -X POST "http://localhost:8000/templates/reload"
```

## 🔧 系统状态端点

### `/status` - API 状态检查
- **描述**: 检查系统状态和数据源可用性
- **用途**: 监控系统运行状态

```bash
curl -X GET "http://localhost:8000/status"
```

### `/health` - 健康检查
- **描述**: 基础健康检查
- **用途**: 负载均衡器健康检查

```bash
curl -X GET "http://localhost:8000/health"
```

### `/ping` - 连通性测试
- **描述**: 简单的连通性测试
- **用途**: 快速测试 API 是否可用

```bash
curl -X GET "http://localhost:8000/ping"
```

## 📋 端点对比表

| 端点 | 请求限制 | 缓存 | 速率限制 | 推荐用途 |
|------|----------|------|----------|----------|
| `/data` | ✅ 有 | ✅ 启用 | ✅ 有 | 日常使用 |
| `/data/fresh` | ✅ 有 | ❌ 跳过 | ✅ 有 | 需要最新数据 |
| `/data/unlimited` | ❌ 无 | ✅ 启用 | ✅ API保护 | **推荐使用** |
| `/data/unlimited/fresh` | ❌ 无 | ❌ 跳过 | ✅ API保护 | 高频最新数据 |

## 🚀 使用建议

### 1. 日常使用
推荐使用 `/data/unlimited` 端点：
- 无每日请求限制
- 启用缓存提高性能
- 仅保留 API 保护性延迟

### 2. 需要最新数据
使用 `/data/unlimited/fresh` 端点：
- 强制获取最新数据
- 无请求限制
- 适合实时分析

### 3. 兼容性考虑
如果您的应用依赖请求限制功能，可以继续使用：
- `/data` - 带缓存的限制版本
- `/data/fresh` - 强制刷新的限制版本

## 🔄 迁移指南

### 从限制版本迁移到无限制版本

1. **替换端点**：
   ```bash
   # 旧版本
   curl "http://localhost:8000/data?ticker=AAPL"
   
   # 新版本
   curl "http://localhost:8000/data/unlimited?ticker=AAPL"
   ```

2. **更新响应处理**：
   - 移除对 `daily_requests_used` 和 `daily_limit` 的检查
   - 注意 `data_source` 字段变化：`financial_modeling_prep_unlimited`

3. **错误处理**：
   - 移除对 429 状态码（请求限制）的处理
   - 保留对 500 状态码（服务器错误）的处理

## 📊 性能对比

| 指标 | 限制版本 | 无限制版本 |
|------|----------|------------|
| 每日请求限制 | 80 次 | 无限制 |
| 缓存性能 | 相同 | 相同 |
| API 延迟 | 1-3秒 | 1-3秒 |
| 错误处理复杂度 | 高（需处理限制） | 低 |
| 推荐指数 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

**更新时间**: 2025-08-10  
**版本**: 2.0.0  
**作者**: Stock Rookie API Team
