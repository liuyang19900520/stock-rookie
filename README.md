# Core Indicators Service

A Python service for collecting and storing core financial indicators using the Financial Modeling Prep (FMP) API.

## Features

- **Core Indicators Collection**: Collects 50+ core financial indicators from FMP API
- **Database Storage**: PostgreSQL storage with async SQLAlchemy ORM
- **Rate Limiting**: Built-in rate limiting for FMP API calls
- **Caching**: Request caching to reduce API calls
- **Scheduled Jobs**: Automated daily data collection
- **REST API**: FastAPI-based REST endpoints
- **Monitoring**: Comprehensive logging and metrics

## Technology Stack

- **Python 3.11**
- **FastAPI** - REST API framework
- **SQLAlchemy 2.x + asyncpg** - Async ORM and PostgreSQL driver
- **Alembic** - Database migrations
- **APScheduler** - Job scheduling
- **httpx** - Async HTTP client
- **aiolimiter** - Rate limiting
- **aiocache** - Caching
- **tenacity** - Retry logic
- **Pydantic v2** - Data validation
- **Docker & docker-compose** - Containerization

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and docker-compose
- FMP API key
- Access to AWS RDS PostgreSQL database

### Using Real AWS RDS Database (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd stock-rookie
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and add your FMP API key
   ```

3. **Test database connection:**
   ```bash
   python test_db_connection.py
   ```

4. **Initialize the real database:**
   ```bash
   # This will create tables, clean any test data, and import the indicator catalog
   python init_real_database.py
   ```

5. **Start the application:**
   ```bash
   # Using Docker
   docker-compose up -d
   
   # Or locally
   uvicorn app.main:app --reload
   ```

6. **Test the API:**
   ```bash
   curl http://localhost:8000/health
   
   # Ingest data for some symbols
   curl -X POST http://localhost:8000/v1/ingest/core \
     -H "Content-Type: application/json" \
     -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
   ```

### Using Local Database (Development)

If you prefer to use a local database for development:

### Local Development

1. Install dependencies:
```bash
pip install -e .
pip install -e ".[dev]"
```

2. Start PostgreSQL (using docker-compose):
```bash
docker-compose up -d db
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Core Indicators

- `GET /v1/indicators/catalog` - Get indicator catalog
- `POST /v1/indicators/catalog/import` - Import catalog from CSV

### Data Ingestion

- `POST /v1/ingest/core` - Ingest core indicators for symbols
- `GET /v1/tickers/{symbol}/core/latest` - Get latest indicators for a ticker

### System

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /config` - Configuration info

## Usage Examples

### Ingest Core Indicators

```bash
curl -X POST http://localhost:8000/v1/ingest/core \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
```

### Get Latest Indicators

```bash
curl http://localhost:8000/v1/tickers/AAPL/core/latest
```

### Get Indicator Catalog

```bash
curl "http://localhost:8000/v1/indicators/catalog?isCore=true"
```

## Core Indicators

The service collects 50+ core financial indicators including:

- **Price & Market Data**: Current price, market cap, enterprise value, beta
- **Valuation Metrics**: P/E, P/B, P/S, EV/EBITDA ratios
- **Profitability**: ROE, ROA, ROIC, margins
- **Growth**: Revenue/EPS growth rates, CAGR
- **Financial Health**: Debt ratios, liquidity ratios, Altman Z-score
- **Technical**: Moving averages, RSI, price changes
- **Dividends**: Dividend yield, payout ratio

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FMP_API_KEY` | FMP API key (required) | - |
| `FMP_BASE_URL` | FMP API base URL | `https://financialmodelingprep.com/api/v3` |
| `DB_URL` | Database connection URL | `postgresql+asyncpg://user:pass@db:5432/stockdb` |
| `RATE_LIMIT_RPS` | Rate limit requests per second | `3` |
| `RATE_LIMIT_BURST` | Rate limit burst capacity | `6` |
| `TIMEZONE` | Application timezone | `Asia/Tokyo` |
| `INGEST_SCHEDULE_CRON` | Daily ingest schedule | `0 0 18 * * *` |
| `CACHE_TTL` | Cache TTL in seconds | `300` |
| `MAX_RETRIES` | Maximum API retries | `3` |
| `COVERAGE_THRESHOLD` | Minimum coverage threshold | `0.8` |

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Architecture

### Directory Structure

```
app/
├── api/                    # API routes
│   ├── routes_catalog.py   # Catalog endpoints
│   └── routes_ingest.py    # Ingestion endpoints
├── core/                   # Core configuration
│   ├── config.py          # Settings
│   ├── logging.py         # Logging setup
│   ├── rate_limit.py      # Rate limiting
│   ├── retries.py         # Retry logic
│   └── timeutil.py        # Time utilities
├── data/                   # Data layer
│   ├── fmp_adapter.py     # FMP API client
│   ├── ingest_service.py  # Ingestion service
│   ├── mapping.py         # Indicator mappings
│   ├── repositories.py    # Database repositories
│   └── indicator_catalog_loader.py  # CSV loader
├── db/                     # Database
│   ├── base.py            # Database setup
│   ├── models.py          # SQLAlchemy models
│   └── migrations/        # Alembic migrations
├── jobs/                   # Scheduled jobs
│   └── scheduler.py       # Job scheduler
├── schemas/                # Pydantic schemas
│   ├── catalog.py         # Catalog schemas
│   └── ingest.py          # Ingestion schemas
├── static/                 # Static files
│   └── indicator_catalog_core.csv  # Indicator catalog
└── main.py                # FastAPI application
```

### Key Components

1. **FMP Adapter**: Handles API calls with rate limiting and caching
2. **Ingest Service**: Orchestrates data collection and storage
3. **Repositories**: Database access layer
4. **Mapping**: Indicator field mappings and value extraction
5. **Scheduler**: Automated job execution
6. **API Routes**: REST endpoints for data access

## Monitoring

The service provides comprehensive logging:

- **Ingest Logs**: Per-symbol ingestion results with coverage metrics
- **API Logs**: FMP API call success/failure tracking
- **Performance Logs**: Request duration and throughput metrics
- **Error Logs**: Detailed error tracking with stack traces

## License

[License information]
