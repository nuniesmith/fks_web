import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import { config } from '../services/config'

export type TradingMode = 'simulation' | 'live'
export type SessionStatus = 'idle' | 'starting' | 'active' | 'paused' | 'stopping' | 'stopped'

export type TradingSessionState = {
  status: SessionStatus
  startedAt?: string
  pausedAt?: string
  stoppedAt?: string
  strategiesAssigned: number
  activeAssets: number
}

export type LiveReadiness = {
  ok: boolean
  checks: Array<{ id: string; label: string; status: 'passed' | 'warning' | 'failed'; message?: string }>
}

// Legacy (uppercase) mode type expected by older components
export type LegacyTradingMode = 'SIMULATION' | 'LIVE'

// Persisted trading configuration (from legacy TradingEnvironmentContext)
export interface TradingConfig {
  mode: LegacyTradingMode
  accounts: string[]
  activeStrategies: string[]
  riskLimits: {
    maxDailyLoss: number
    maxPositionSize: number
    maxOpenPositions: number
  }
  notifications: {
    enabled: boolean
    email: boolean
    push: boolean
    discord: boolean
  }
}

const defaultTradingConfig: TradingConfig = {
  mode: (config.defaultTradingMode || 'SIMULATION') as LegacyTradingMode,
  accounts: ['demo-account-1'],
  activeStrategies: [],
  riskLimits: {
    maxDailyLoss: 1000,
    maxPositionSize: 10000,
    maxOpenPositions: 5
  },
  notifications: {
    enabled: true,
    email: false,
    push: true,
    discord: false
  }
}

export interface TradingEnvContextValue {
  // New / unified (lowercase) focus & session lifecycle
  focus: TradingMode
  setFocus: (mode: TradingMode) => void
  sim: TradingSessionState
  live: TradingSessionState
  start: (mode: TradingMode) => Promise<void>
  pause: (mode: TradingMode) => Promise<void>
  stop: (mode: TradingMode) => Promise<void>
  refresh: () => Promise<void>
  readiness: LiveReadiness
  // Persisted configuration (legacy shape)
  tradingConfig: TradingConfig
  updateConfig: (partial: Partial<TradingConfig>) => void
  updateEnvironment: (mode: LegacyTradingMode) => void
  environment: LegacyTradingMode
  isLive: boolean
  isSimulation: boolean
}

const TradingEnvContext = createContext<TradingEnvContextValue | undefined>(undefined)

async function verifyDatasetSplit(): Promise<boolean> {
  try {
    // Endpoint is defined as POST /api/data/dataset/verify
  const base = (config.apiBaseUrl || '/api').replace(/\/$/, '')
  const res = await fetch(`${base}/data/dataset/verify`, { method: 'POST' })
    if (!res.ok) {
      if (res.status === 404) {
        console.warn('[verifyDatasetSplit] 404: dataset verify endpoint not found')
      } else if (res.status === 405) {
        console.warn('[verifyDatasetSplit] 405: method not allowed – backend expects POST?')
      }
      return false
    }
    const j = await res.json().catch(() => ({}))
    return !!(j && (j.ok === true || j.valid === true))
  } catch (e) {
    console.warn('[verifyDatasetSplit] error', e)
    return false
  }
}

async function countAssigned(): Promise<{ strategiesAssigned: number; activeAssets: number }> {
  try {
    // Try API first
    const base = (config.apiBaseUrl || '/api').replace(/\/$/, '')
    const [assetsRes, assignsRes] = await Promise.all([
      fetch(`${base}/active-assets`),
      fetch(`${base}/strategy/assignments`).catch(() => undefined as any)
    ])
    if (assetsRes.ok) {
      const j = await assetsRes.json()
      const items = j.items || []
      let serverMap: Record<string, string[]> = {}
      if (assignsRes && assignsRes.ok) {
        const aj = await assignsRes.json().catch(() => ({} as any))
        serverMap = (aj && aj.assignments) || {}
      }
      // merge with local storage; local overrides
  const ls = typeof localStorage !== 'undefined' ? localStorage.getItem('fks.asset.strategy.assignments') : null
      const localMap: Record<string, string[]> = ls ? JSON.parse(ls) : {}
      const map = { ...serverMap, ...localMap }
      const strategiesAssigned = items.reduce((acc: number, it: any) => acc + ((map[String(it.id)]?.length) || 0), 0)
      return { strategiesAssigned, activeAssets: items.length }
    }
  } catch {}
  // Fallback entirely to local
  const ls = typeof localStorage !== 'undefined' ? localStorage.getItem('fks.asset.strategy.assignments') : null
  const map: Record<string, string[]> = ls ? JSON.parse(ls) : {}
  const ids = Object.keys(map)
  const strategiesAssigned = ids.reduce((a, k) => a + (map[k]?.length || 0), 0)
  return { strategiesAssigned, activeAssets: ids.length }
}

export const TradingEnvProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Lowercase focus used by new components
  const [focus, setFocus] = useState<TradingMode>('simulation')
  // Session state
  const [sim, setSim] = useState<TradingSessionState>({ status: 'idle', strategiesAssigned: 0, activeAssets: 0 })
  const [live, setLive] = useState<TradingSessionState>({ status: 'idle', strategiesAssigned: 0, activeAssets: 0 })
  const [readiness, setReadiness] = useState<LiveReadiness>({ ok: false, checks: [] })
  // Persisted configuration (single source of truth replacing legacy provider)
  const [tradingConfig, setTradingConfig] = useState<TradingConfig>(() => {
    try {
  const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('fks-trading-config') : null
      if (saved) {
        const parsed = JSON.parse(saved)
        return { ...defaultTradingConfig, ...parsed }
      }
    } catch (e) {
      console.warn('[TradingEnvProvider] failed to parse saved trading config', e)
    }
    return defaultTradingConfig
  })

  // Keep lowercase focus in sync with persisted config mode
  useEffect(() => {
    const desired = tradingConfig.mode === 'LIVE' ? 'live' : 'simulation'
    setFocus(desired)
  }, [tradingConfig.mode])

  // Persist whenever config changes
  useEffect(() => {
  try { if (typeof localStorage !== 'undefined') localStorage.setItem('fks-trading-config', JSON.stringify(tradingConfig)) } catch {}
  }, [tradingConfig])

  const updateConfig = useCallback((partial: Partial<TradingConfig>) => {
    setTradingConfig(prev => ({ ...prev, ...partial }))
  }, [])

  const updateEnvironment = useCallback((mode: LegacyTradingMode) => {
    setTradingConfig(prev => ({ ...prev, mode }))
    setFocus(mode === 'LIVE' ? 'live' : 'simulation')
  }, [])

  const mountedRef = useRef(true)
  useEffect(() => () => { mountedRef.current = false }, [])

  const computeReadiness = useCallback(async () => {
    const [splitOk, assigned] = await Promise.all([verifyDatasetSplit(), countAssigned()])
    if (!mountedRef.current) return
    const checks: LiveReadiness['checks'] = [
      { id: 'dataset', label: 'Dataset split verified (80/10/10)', status: splitOk ? 'passed' : 'failed' },
      { id: 'assignments', label: 'Strategies assigned to active assets', status: assigned.strategiesAssigned > 0 ? 'passed' : 'warning' },
    ]
    setReadiness({ ok: checks.every(c => c.status === 'passed'), checks })
  }, [])

  const refresh = useCallback(async () => {
    await computeReadiness()
    const assigned = await countAssigned()
    if (!mountedRef.current) return
    setSim(s => ({ ...s, strategiesAssigned: assigned.strategiesAssigned, activeAssets: assigned.activeAssets }))
    setLive(s => ({ ...s, strategiesAssigned: assigned.strategiesAssigned, activeAssets: assigned.activeAssets }))
  }, [computeReadiness])

  useEffect(() => { refresh() }, [refresh])

  const start = useCallback(async (mode: TradingMode) => {
    const setter = mode === 'simulation' ? setSim : setLive
    setter(s => ({ ...s, status: 'starting' }))
    const base = (config.apiBaseUrl || '/api').replace(/\/$/, '')
    await fetch(`${base}/trading/sessions/start?mode=${mode}`, { method: 'POST' }).catch(() => {})
    if (mountedRef.current) {
      setter(s => ({ ...s, status: 'active', startedAt: new Date().toISOString() }))
    }
  }, [])

  const pause = useCallback(async (mode: TradingMode) => {
    const setter = mode === 'simulation' ? setSim : setLive
    setter(s => ({ ...s, status: 'paused', pausedAt: new Date().toISOString() }))
    const base = (config.apiBaseUrl || '/api').replace(/\/$/, '')
    await fetch(`${base}/trading/sessions/pause?mode=${mode}`, { method: 'POST' }).catch(() => {})
  }, [])

  const stop = useCallback(async (mode: TradingMode) => {
    const setter = mode === 'simulation' ? setSim : setLive
    setter(s => ({ ...s, status: 'stopping' }))
    const base = (config.apiBaseUrl || '/api').replace(/\/$/, '')
    await fetch(`${base}/trading/sessions/stop?mode=${mode}`, { method: 'POST' }).catch(() => {})
    if (!mountedRef.current) return
    setter(s => ({ ...s, status: 'stopped', stoppedAt: new Date().toISOString() }))
  }, [])

  const value = useMemo<TradingEnvContextValue>(() => ({
    focus,
    setFocus,
    sim,
    live,
    start,
    pause,
    stop,
    refresh,
    readiness,
    tradingConfig,
    updateConfig,
    updateEnvironment,
    environment: tradingConfig.mode,
    isLive: tradingConfig.mode === 'LIVE',
    isSimulation: tradingConfig.mode === 'SIMULATION'
  }), [focus, sim, live, start, pause, stop, refresh, readiness, tradingConfig, updateConfig, updateEnvironment])

  return (
    <TradingEnvContext.Provider value={value}>{children}</TradingEnvContext.Provider>
  )
}

export function useTradingEnv(): TradingEnvContextValue {
  const ctx = useContext(TradingEnvContext)
  if (!ctx) throw new Error('useTradingEnv must be used within TradingEnvProvider')
  return ctx
}
