# Database Setup for Data Collection

## Models Created

The data collection app includes three Django models for storing market data:

1. **MarketDataPoint** - Individual OHLCV data points
2. **MarketOverview** - Market-wide statistics
3. **DataCollectionLog** - Collection operation logs

## Migration Steps

1. **Create migrations**:
   ```bash
   cd repo/web
   python manage.py makemigrations data_collection
   ```

2. **Apply migrations**:
   ```bash
   python manage.py migrate data_collection
   ```

3. **Verify tables created**:
   ```sql
   \dt market_data_points
   \dt market_overview
   \dt data_collection_logs
   ```

## Database Schema

### market_data_points
- Stores OHLCV data for all asset types
- Indexed on: symbol, timestamp, granularity, provider
- Unique constraint: (symbol, timestamp, granularity, provider)

### market_overview
- Stores hourly/daily market statistics
- Indexed on: timestamp, provider

### data_collection_logs
- Tracks all collection operations
- Includes performance metrics and error details
- Indexed on: task_name, status, started_at

## Usage

Once migrations are applied, the Celery tasks will automatically save collected data to the database. You can:

1. **View data in Django admin**: `/admin/data_collection/`
2. **Query data programmatically**:
   ```python
   from data_collection.models import MarketDataPoint
   
   # Get latest BTC data
   btc_data = MarketDataPoint.objects.filter(
       symbol="BTC",
       granularity="1h"
   ).order_by("-timestamp")[:100]
   
   # Get collection logs
   from data_collection.models import DataCollectionLog
   recent_logs = DataCollectionLog.objects.filter(
       status="success"
   ).order_by("-started_at")[:10]
   ```

## Performance Considerations

- **Indexes**: All models have appropriate indexes for time-series queries
- **Bulk Operations**: Tasks use `update_or_create` to prevent duplicates efficiently
- **Transactions**: Data saving uses atomic transactions for consistency
- **Unique Constraints**: Prevent duplicate data points automatically

## Monitoring

Use the `DataCollectionLog` model to monitor:
- Collection success rates
- Provider performance
- Task duration
- Error rates

Access logs via Django admin or query programmatically.

