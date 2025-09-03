import { config } from './config'
import AuthentikService from './security/AuthentikService'

// Ensure API base always includes /api prefix expected by FastAPI routers
function resolveApiBase(): string {
  const base = (config.apiBaseUrl || (import.meta as any).env?.VITE_API_URL || '/api').replace(/\/$/, '')
  if (base.endsWith('/api')) return base
  // If user supplied root host (e.g. https://localhost), append /api
  return `${base}/api`
}
const API_BASE = resolveApiBase()

function currentAccessToken(): string | undefined {
  try {
    const raw = typeof window !== 'undefined' ? localStorage.getItem('auth_tokens') : null
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed?.access_token) return parsed.access_token as string
    }
  } catch {}
  // fallback to legacy env token / localStorage key
  try {
    const ls = typeof window !== 'undefined' ? localStorage.getItem('fks_api_token') : null
    return ls || (import.meta as any).env?.VITE_API_TOKEN
  } catch { return (import.meta as any).env?.VITE_API_TOKEN }
}

function buildHeaders(extra?: HeadersInit): HeadersInit {
  const h: HeadersInit = { 'Content-Type': 'application/json', ...(extra || {}) }
  const token = currentAccessToken()
  if (token) {
    (h as Record<string,string>).Authorization = `Bearer ${token}`
    ;(h as Record<string,string>)['X-API-Key'] = token
  }
  return h
}

async function tryRefreshToken(): Promise<string | undefined> {
  try {
    const raw = typeof window !== 'undefined' ? localStorage.getItem('auth_tokens') : null
    if (!raw) return
    const parsed = JSON.parse(raw)
    const refresh = parsed?.refresh_token as string | undefined
    if (!refresh) return
    const ak = AuthentikService.getInstance()
    const newTokens = await ak.refreshToken(refresh)
    localStorage.setItem('auth_tokens', JSON.stringify(newTokens))
    return newTokens.access_token
  } catch { return }
}

async function http<T>(path: string, init?: RequestInit, _retry = false): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, { ...init, headers: buildHeaders(init?.headers) })
  if (res.status === 401 && !_retry) {
    const refreshed = await tryRefreshToken()
    if (refreshed) {
      const retryHeaders: HeadersInit = { ...(init?.headers || {}) }
      ;(retryHeaders as any).Authorization = `Bearer ${refreshed}`
      ;(retryHeaders as any)['X-API-Key'] = refreshed
      const retryRes = await fetch(`${API_BASE}${path}`, { ...init, headers: buildHeaders(retryHeaders) })
      if (!retryRes.ok) throw new Error(`${retryRes.status} ${retryRes.statusText}: ${await retryRes.text().catch(() => '')}`)
      return retryRes.json() as Promise<T>
    }
  }
  if (!res.ok) {
    // Deduplicate noisy 404s for active-assets endpoint during development
    if (res.status === 404 && /\/active-assets(\/|$)/.test(path)) {
      try {
        const key = 'fks.logged.active_assets_api_404'
        if (typeof sessionStorage === 'undefined' || !sessionStorage.getItem(key)) {
          console.warn(`[ActiveAssetsApi] 404 for ${url} (service absent?)`)
          if (typeof sessionStorage !== 'undefined') sessionStorage.setItem(key, '1')
        }
      } catch {}
    }
    throw new Error(`${res.status} ${res.statusText}: ${await res.text().catch(() => '')}`)
  }
  return res.json() as Promise<T>
}

export type ActiveAsset = {
  id: number
  source: string
  symbol: string
  // Optional metadata for richer asset classification. Backend may ignore these.
  asset_type?: string | null
  exchange?: string | null
  intervals: string[]
  years?: number | null
  full_history?: boolean
  enabled: boolean
  created_at?: string
  updated_at?: string
  progress?: Array<{ interval: string; last_cursor?: string; target_start?: string | null; target_end?: string; last_rows?: number; last_run?: string }>
}

export async function listActiveAssets(): Promise<{ items: ActiveAsset[]; count: number }> {
  return http('/active-assets')
}

export async function addActiveAsset(payload: { source: string; symbol: string; intervals: string[]; years?: number; full_history?: boolean; asset_type?: string; exchange?: string }): Promise<{ id: number; ok: boolean }> {
  return http('/active-assets', { method: 'POST', body: JSON.stringify(payload) })
}

export async function removeActiveAsset(id: number): Promise<{ ok: boolean }> {
  return http(`/active-assets/${id}`, { method: 'DELETE' })
}

export async function setActiveAssetEnabled(id: number, enable: boolean): Promise<{ ok: boolean }> {
  return http(`/active-assets/${id}/enable?enable=${enable ? 'true' : 'false'}`, { method: 'POST' })
}

export async function startBackfillScheduler(): Promise<{ ok: boolean }> {
  return http('/active-assets/scheduler/start', { method: 'POST' })
}

export async function stopBackfillScheduler(): Promise<{ ok: boolean }> {
  return http('/active-assets/scheduler/stop', { method: 'POST' })
}
