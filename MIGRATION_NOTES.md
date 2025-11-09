# Migration Notes for API Key Management

## New Model: APIKey

A new Django model has been added for secure API key management. To use it:

### 1. Generate Encryption Key

First, generate an encryption key for storing API keys securely:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add this to your `.env` file:
```bash
ENCRYPTION_KEY=your_generated_key_here
```

### 2. Create and Run Migrations

```bash
cd repo/web
python manage.py makemigrations authentication
python manage.py migrate
```

### 3. Create Initial API Keys

You can create API keys via Django admin or Python shell:

```python
from authentication.api_keys import APIKey

# Create a global Polygon API key
polygon_key = APIKey(
    name="polygon_prod",
    provider="polygon",
    description="Production Polygon API key",
    is_global=True,
    is_active=True
)
polygon_key.key = "your-polygon-api-key"
polygon_key.save()

# Create a CoinMarketCap key
cmc_key = APIKey(
    name="cmc_free_tier",
    provider="coinmarketcap",
    description="CoinMarketCap free tier API key",
    is_global=True,
    is_active=True
)
cmc_key.key = "your-cmc-api-key"
cmc_key.save()
```

### 4. Access Keys in Code

```python
from authentication.api_keys import APIKey

# Get key by name
polygon_key = APIKey.get_key("polygon_prod")

# Get key by provider
polygon_key = APIKey.get_key_for_provider("polygon")

# Get user-specific key
user_key = APIKey.get_key_for_provider("polygon", user=request.user)
```

### 5. Use in Data Adapters

The adapters will automatically pick up keys from environment variables, but you can also configure them to use the APIKey model:

```python
import os
from authentication.api_keys import APIKey

# Set environment variable from database
polygon_key = APIKey.get_key_for_provider("polygon")
if polygon_key:
    os.environ["POLYGON_API_KEY"] = polygon_key
```

## Security Notes

- **Never commit ENCRYPTION_KEY to version control**
- **Rotate encryption keys periodically** (requires re-encrypting all keys)
- **Use different keys for development and production**
- **Monitor key usage** via `last_used` field
- **Set expiration dates** for temporary keys

## Admin Interface

Access the admin interface at `/admin/authentication/apikey/` to:
- View all API keys
- Create/edit keys (with masked input)
- Filter by provider, scope, status
- Track usage and expiration

