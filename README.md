# FKS Web

Django-based web dashboard and user interface for the FKS Trading Platform.

**Port**: 8000  
**Framework**: Python 3.12 + Django + Gunicorn  
**Role**: Web dashboard and user interface

## 🎯 Purpose

FKS Web provides the primary user interface for the FKS Trading Platform. It offers:

- **Dashboard**: Real-time monitoring of all FKS services
- **Service Management**: Health checks, metrics, and service-specific features
- **AI Insights**: RAG-powered insights with Google AI API integration
- **API Key Management**: Secure API key storage and management
- **Authentication**: User authentication and session management
- **Service Integration**: Unified interface to interact with all FKS microservices

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐     ┌──────────────┐
│  fks_web    │────▶│  fks_main    │
│  (Django)   │     │ (Orchestrator)│
└──────┬──────┘     └──────┬───────┘
       │                    │
       │                    ▼
       │            ┌──────────────┐
       │            │ fks_monitor  │
       │            │  (Health)    │
       │            └──────────────┘
       │
       ▼
┌─────────────┐
│  PostgreSQL │
│  (Database) │
└─────────────┘
```

**Key Components**:
- **Django Framework**: Web application framework
- **Gunicorn**: WSGI HTTP server for production
- **RAG System**: Google AI API integration for intelligent insights
- **Service Registry**: Integration with fks_main for service discovery
- **Authentication**: Django authentication with API key management

## 🚀 Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver 0.0.0.0:8000
```

### Docker

```bash
# Build and run
docker-compose up --build

# Or using the unified start script
cd /home/jordan/Documents/code/fks
./start.sh --type compose
```

### Kubernetes

```bash
# Deploy to Kubernetes
cd /home/jordan/Documents/code/fks
./start.sh --type k8s

# Access via ingress
# https://fkstrading.xyz
```

## 📡 API Endpoints

### Health Checks

- `GET /health` - Health check
- `GET /ready` - Readiness check (checks database connection)
- `GET /live` - Liveness probe

### Web Interface

- `GET /` - Dashboard home page
- `GET /dashboard/` - Main dashboard
- `GET /services/` - Service list page
- `GET /services/{service_name}/` - Service detail page
- `GET /intelligence/` - AI Insights dashboard

### Authentication

- `GET /auth/login/` - Login page
- `POST /auth/login/` - Login endpoint
- `GET /auth/logout/` - Logout endpoint
- `GET /auth/api-keys/` - API key management (staff only)

### API Endpoints (Django REST Framework)

- `GET /api/health/` - Health check API
- `GET /api/services/` - Service list API
- `GET /api/services/{name}/` - Service details API

## 🔧 Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=fks_web
SERVICE_PORT=8000
PYTHONPATH=/app/src:/app

# Database
DATABASE_URL=postgresql://fks_user:password@db:5432/trading_db
DB_HOST=db
DB_PORT=5432
DB_NAME=trading_db
DB_USER=fks_user
DB_PASSWORD=your_password

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=fkstrading.xyz,www.fkstrading.xyz,localhost

# Redis (for caching and sessions)
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Google AI API (for RAG system)
GEMINI_API_KEY=your-google-ai-api-key

# OpenAI API (fallback for RAG)
OPENAI_API_KEY=your-openai-api-key

# External Service URLs
FKS_MAIN_URL=http://fks-main:8010
FKS_MONITOR_URL=http://fks-monitor:8006

# Security
CSRF_TRUSTED_ORIGINS=https://fkstrading.xyz,https://www.fkstrading.xyz
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

### Configuration Files

- `src/config/settings.py` - Django settings
- `src/config/urls.py` - URL routing
- `src/urls.py` - Application URLs

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Django test runner
python manage.py test
```

## 🐳 Docker

### Build

```bash
docker build -t nuniesmith/fks:web-latest .
```

### Run

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://fks_user:password@db:5432/trading_db \
  -e SECRET_KEY=your-secret-key \
  -e GEMINI_API_KEY=your-api-key \
  nuniesmith/fks:web-latest
```

### Docker Compose

```yaml
services:
  fks_web:
    build: .
    image: nuniesmith/fks:web-latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://fks_user:password@db:5432/trading_db
      - SECRET_KEY=${SECRET_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - db
      - redis
```

## ☸️ Kubernetes

### Deployment

```bash
# Deploy using Helm
cd repo/main/k8s/charts/fks-platform
helm install fks-platform . -n fks-trading

# Or using manifests
kubectl apply -f repo/main/k8s/manifests/all-services.yaml -n fks-trading
```

### Ingress

The service is exposed via ingress at:
- `https://fkstrading.xyz`
- `https://www.fkstrading.xyz`

### Health Checks

Kubernetes probes:
- **Liveness**: `GET /live`
- **Readiness**: `GET /ready`

## 📚 Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Deployment Guide](docs/DEPLOYMENT.md) - Deployment instructions
- [Architecture Details](docs/ARCHITECTURE.md) - System architecture

## 🔗 Integration

### Dependencies

- **fks_main** (port 8010): Service orchestration and management
- **fks_monitor** (port 8006): Health checks and metrics aggregation
- **PostgreSQL**: Database for user data, API keys, sessions
- **Redis**: Caching and Celery task queue

### Consumers

- **Users**: Primary interface for all FKS platform interactions
- **fks_main**: Web UI provides management interface for orchestration

### Service Integration

The web service integrates with all FKS microservices through:

1. **fks_main API**: Service discovery and orchestration
2. **fks_monitor API**: Health checks and metrics
3. **Direct Service APIs**: For service-specific features (analyze, AI, etc.)

## 📊 Monitoring

### Health Check Endpoints

- `GET /health` - Basic health status
- `GET /ready` - Readiness (checks database, Redis)
- `GET /live` - Liveness (process alive)

### Metrics

- Django metrics via Prometheus (if configured)
- Service health status from fks_monitor
- Database connection status
- Redis connection status

### Logging

- Django logging configuration
- Structured logging for production
- Log levels: DEBUG, INFO, WARNING, ERROR

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/nuniesmith/fks_web.git
cd fks_web

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Code Structure

```
repo/web/
├── src/
│   ├── config/              # Django configuration
│   │   ├── settings.py     # Main settings
│   │   └── urls.py         # URL routing
│   ├── authentication/     # Authentication app
│   │   ├── models.py       # User, APIKey models
│   │   ├── views.py        # Authentication views
│   │   └── api_keys.py     # API key management
│   ├── views/              # Application views
│   │   ├── services.py     # Service management views
│   │   └── intelligence.py # AI Insights views
│   ├── rag/                # RAG system
│   │   ├── intelligence.py # RAG orchestrator
│   │   └── google_ai.py    # Google AI client
│   ├── templates/          # Django templates
│   ├── static/             # Static files (CSS, JS)
│   └── urls.py             # Application URLs
├── tests/                   # Test suite
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Contributing

1. Follow Django best practices
2. Write tests for new features
3. Update documentation
4. Follow PEP 8 style guide
5. Use type hints where appropriate

## 🔐 Security

### Authentication

- Django authentication system
- Session-based authentication
- API key management for service integration

### API Key Management

- Encrypted storage using Fernet (cryptography)
- Staff-only access to API key management
- Secure key retrieval for service integration

### CSRF Protection

- Django CSRF middleware enabled
- Trusted origins configured for production

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check database connectivity
python manage.py dbshell

# Run migrations
python manage.py migrate
```

### Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput
```

### RAG System Not Working

- Verify `GEMINI_API_KEY` is set
- Check Google AI API rate limits
- Review logs for API errors

---

**Repository**: [nuniesmith/fks_web](https://github.com/nuniesmith/fks_web)  
**Docker Image**: `nuniesmith/fks:web-latest`  
**Status**: Active
