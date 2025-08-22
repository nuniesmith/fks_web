import { config } from './config'

const API_BASE = (config.apiBaseUrl || (import.meta as any).env?.VITE_API_URL || '/api').replace(/\/$/, '')
const API_TOKEN = (import.meta as any).env?.VITE_API_TOKEN || ''

function headers(extra?: HeadersInit): HeadersInit {
  const h: HeadersInit = { 'Content-Type': 'application/json', ...(extra || {}) }
  if (API_TOKEN) (h as Record<string, string>)["Authorization"] = `Bearer ${API_TOKEN}`
  return h
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers: headers(init?.headers) })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text().catch(() => '')}`)
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
