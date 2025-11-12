# Dev Interface - FKS Services Testing

**Purpose**: Development interface for testing and monitoring all FKS services

---

## 🎯 Overview

The Dev Interface provides a comprehensive testing and monitoring dashboard for all FKS services. It automatically discovers services from the service registry and tests their health, readiness, and functionality.

---

## 📋 Features

### Service Testing
- **Health Checks**: Tests `/health` endpoint for all services
- **Readiness Checks**: Tests `/ready` endpoint for all services
- **Service-Specific Tests**: Tests service-specific endpoints (e.g., portfolio API endpoints)
- **Auto-Discovery**: Automatically loads services from `service_registry.json`

### Dashboard
- **Service Status**: Visual status indicators for all services
- **Summary Statistics**: Total, healthy, unhealthy, and unreachable services
- **Individual Service Views**: Detailed test results for each service
- **Auto-Refresh**: Dashboard auto-refreshes every 30 seconds

### API Endpoints
- **Test All Services**: `/dev/api/test-all/` - Test all services
- **Test Single Service**: `/dev/api/test/<service_name>/` - Test a specific service
- **Service Info**: `/dev/api/info/<service_name>/` - Get service information

---

## 🚀 Usage

### Accessing the Dashboard
1. Navigate to `/dev/` in the web interface
2. View all services and their status
3. Click on a service to view detailed test results

### Testing Services
1. **Test All Services**: Click "Refresh Tests" button
2. **Test Single Service**: Click "Test Now" on a service card
3. **View Details**: Click "View Details" to see comprehensive test results

### Service-Specific Tests
The service tester automatically tests service-specific endpoints:
- **fks_portfolio**: Tests dashboard, signals, and portfolio endpoints
- **fks_ai**: Tests AI health endpoint
- **fks_data**: Tests data service endpoints
- **Other services**: Tests common API endpoints

---

## 🔧 Configuration

### Service Registry
The service tester loads services from:
- `repo/main/config/service_registry.json` (default)
- Environment variable: `SERVICE_REGISTRY_PATH`
- Fallback: Default service registry in code

### Service Configuration
Each service in the registry should have:
```json
{
  "name": "service_name",
  "port": 8000,
  "base_url": "http://service_name:8000",
  "health_url": "http://service_name:8000/health",
  "dependencies": ["other_service"]
}
```

---

## 📊 Service Status

### Status Types
- **Healthy**: Service is responding correctly
- **Unhealthy**: Service is responding but with errors
- **Unreachable**: Service is not responding or not running

### Test Results
Each service test includes:
- **Health Test**: Tests `/health` endpoint
- **Ready Test**: Tests `/ready` endpoint (if available)
- **Service-Specific Tests**: Tests service-specific endpoints

---

## 🛠️ Development

### Adding Service-Specific Tests
Edit `repo/web/src/dev/service_tester.py`:

```python
test_endpoints = {
    "your_service": [
        "/api/v1/endpoint1",
        "/api/v1/endpoint2",
    ],
}
```

### Customizing Tests
Modify `_test_service_specific` method to add custom test logic for specific services.

---

## 📝 Files

- **`service_tester.py`**: Core service testing logic
- **`views.py`**: Django views for dashboard and API endpoints
- **`urls.py`**: URL patterns for dev interface
- **`dashboard.html`**: Main dashboard template
- **`service_test.html`**: Individual service test template

---

## 🔍 Troubleshooting

### Service Not Found
- Check `service_registry.json` path
- Verify service is in registry
- Check service name spelling

### Service Unreachable
- Verify service is running
- Check service URL and port
- Verify network connectivity
- Check service health endpoint

### Test Timeout
- Increase timeout in `service_tester.py`
- Check service response time
- Verify service is not overloaded

---

## 🎯 Next Steps

1. **Add More Tests**: Add service-specific functionality tests
2. **Performance Metrics**: Add response time tracking
3. **Historical Data**: Store test results over time
4. **Alerts**: Add alerting for unhealthy services
5. **Integration**: Integrate with monitoring services

---

**Status**: ✅ Ready for Use  
**Last Updated**: 2025-01-XX

