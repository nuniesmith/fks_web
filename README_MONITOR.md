# FKS Web – Central Monitor Integration

The web UI can consume the centralized Rust monitor (`fks_master`) aggregate health endpoint instead of performing individual browser-side pings.

## Enable

Set an env var in your web `.env` (or export before `npm run dev`):

```bash
VITE_FKS_MONITOR_URL=http://localhost:3030
VITE_ENABLE_REAL_HEALTH=true  # optional; if set AND monitor unavailable falls back to direct checks
```

`useServiceMonitoring` will:

1. Attempt `GET <VITE_FKS_MONITOR_URL>/health/aggregate`.
2. If successful, map statuses (healthy|warning|error|offline) from monitor output.
3. If it fails, fall back to legacy per-endpoint simulated/real fetch logic.

## Aggregate JSON Shape (from monitor)

```json
{
  "overallStatus": "healthy",
  "totalServices": 12,
  "healthyServices": 10,
  "warningServices": 1,
  "errorServices": 0,
  "offlineServices": 1,
  "lastUpdate": "2025-09-01T12:34:56Z",
  "services": [
    {"id":"fks_api","name":"FKS API Service","status":"healthy","rawStatus":"Healthy","lastCheck":"2025-09-01T12:34:50Z","responseTimeMs":42,"critical":true}
  ]
}
```

## React Hook Behavior

If central data is used, latency history continues to accumulate using responseTimeMs (or 0 when absent). Metrics field is currently limited (critical flag); extend in monitor then map here.

## Troubleshooting

- 404: Ensure monitor started with port 3030 (CLI flags or env `FKS_MASTER_PORT`).
- CORS: Monitor uses permissive CORS by default.
- Mixed Content: Use HTTPS for both frontend & monitor when deploying under TLS.

## Auth Token Handling (Unified)

Authentication headers are unified via `src/services/authToken.ts`:

- `getCurrentAccessToken()` selects token in priority: Authentik `auth_tokens.access_token` → `fks_api_token` (localStorage) → `VITE_API_TOKEN` env.
- `refreshAccessToken()` attempts refresh with stored `refresh_token` (Authentik) and persists new tokens.
- `buildAuthHeaders()` injects `Authorization: Bearer <token>`, `X-API-Key`, and `api-key` (FastAPI custom header) for maximum backend compatibility.
- `authFetch()` wraps `fetch` adding headers and a single automatic retry on 401 after refresh.

Migrated clients: ActiveAssets, Data, Strategies, Engine, Training. Axios-based generic `apiClient` & `dataClient` already handle refresh via interceptors; future raw `fetch` clients should use `authFetch`.

Local dev quick tokens:

```js
localStorage.setItem('fks_api_token', 'dev-token')
// or via .env.local / shell
// VITE_API_TOKEN=dev-token
```
 
Authentik login flow (once integrated) will overwrite with real access & refresh tokens.

