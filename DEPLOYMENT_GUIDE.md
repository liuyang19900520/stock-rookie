# Core Indicators Service - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database (AWS RDS recommended)
- FMP API key

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd stock-rookie
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Environment Configuration
```bash
cp env.example .env
# Edit .env with your actual credentials:
# - FMP_API_KEY=your_actual_api_key
# - DB_URL=your_database_connection_string
```

### 3. Database Setup
```bash
# Initialize database schema
python setup_dev_schema.py

# Or run migrations manually
alembic upgrade head
```

### 4. Start the Service
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Manual Docker Build
```bash
docker build -t core-indicators-service .
docker run -p 8000:8000 --env-file .env core-indicators-service
```

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Indicator Catalog
```bash
curl http://localhost:8000/v1/indicators/catalog?isCore=true
```

### Ingest Data
```bash
curl -X POST http://localhost:8000/v1/ingest/core \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
```

### Get Latest Indicators
```bash
curl http://localhost:8000/v1/tickers/AAPL/core/latest
```

## 🔧 Configuration

### Environment Variables
- `FMP_API_KEY`: Your FMP API key (required)
- `DB_URL`: PostgreSQL connection string
- `RATE_LIMIT_RPS`: API rate limit (default: 3)
- `TIMEZONE`: Application timezone (default: Asia/Tokyo)
- `INGEST_SCHEDULE_CRON`: Daily ingest schedule (default: 0 18 * * *)

### Database Schema
The service uses the `dev` schema by default. Tables:
- `indicator_catalog`: Core indicators metadata
- `core_indicators_history`: Historical indicator values

## 📈 Monitoring

### Logs
- Application logs: `app.log`
- Ingest metrics: Structured logging with coverage statistics

### Health Checks
- Database connectivity
- FMP API connectivity
- Service status

## 🔒 Security

### Sensitive Information
- `.env` file is gitignored
- API keys and database passwords should be kept secure
- Use environment variables for production deployment

### Rate Limiting
- Built-in rate limiting for FMP API calls
- Configurable via environment variables

## 🧪 Testing

### Run Tests
```bash
pytest tests/
```

### Manual Testing
```bash
# Test FMP API connection
python -c "from app.data.fmp_adapter import get_fmp_adapter; import asyncio; print(asyncio.run(get_fmp_adapter().fetch_quote('AAPL')))"
```

## 📝 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check `DB_URL` in `.env`
   - Ensure database is accessible
   - Verify SSL settings for AWS RDS

2. **FMP API Errors**
   - Verify `FMP_API_KEY` is valid
   - Check rate limiting settings
   - Monitor API quota usage

3. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -e .` to install package

### Logs
Check application logs for detailed error information:
```bash
tail -f app.log
```

## 🔄 Updates

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Code Updates
```bash
git pull origin main
pip install -e .
# Restart service
```

## 📞 Support

For issues and questions:
1. Check the logs for error details
2. Verify configuration settings
3. Test API connectivity manually
4. Review the README.md for detailed documentation
