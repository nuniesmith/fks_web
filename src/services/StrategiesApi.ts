import { config } from './config'

export type StrategySummary = {
  id: string
  name: string
  type: 'entry' | 'exit' | 'filter' | 'risk' | 'composite'
  description?: string
  status?: 'active' | 'inactive' | 'testing'
}

const API_BASE = (config.apiBaseUrl || '/api').replace(/\/$/, '')
const TOKEN = (import.meta as any).env?.VITE_API_TOKEN || ''

function headers(extra?: HeadersInit): HeadersInit {
  const h: HeadersInit = { ...(extra || {}) }
  if (TOKEN) (h as Record<string, string>)['Authorization'] = `Bearer ${TOKEN}`
  return h
}

export async function listStrategies(): Promise<StrategySummary[]> {
  try {
  const res = await fetch(`${API_BASE}/strategies`, { headers: headers() })
    if (!res.ok) throw new Error('bad status')
    const j = await res.json()
    return j.items || j.strategies || []
  } catch {
    return []
  }
}

export async function saveAssignments(assignments: Record<string, string[]>): Promise<boolean> {
  try {
  const res = await fetch(`${API_BASE}/strategy/assignments`, {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ assignments })
    })
    return res.ok
  } catch { return false }
}

export async function getAssignments(): Promise<Record<string, string[]>> {
  try {
  const res = await fetch(`${API_BASE}/strategy/assignments`, { headers: headers() })
    if (!res.ok) return {}
    const j = await res.json().catch(() => ({} as any))
    return (j && j.assignments) || {}
  } catch {
    return {}
  }
}
