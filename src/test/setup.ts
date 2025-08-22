import '@testing-library/jest-dom'
import { vi, beforeEach } from 'vitest'

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
} as any

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
} as Storage
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
} as Storage
global.sessionStorage = sessionStorageMock

// Mock console methods for cleaner test output
const consoleMock = {
  warn: vi.fn(),
  error: vi.fn(),
  log: vi.fn(),
}
global.console = { ...console, ...consoleMock }

// Reset all mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
})

// Global mock for lightweight-charts (so individual tests need not redefine)
vi.mock('lightweight-charts', () => ({
  createChart: () => ({
    addSeries: (_kind: string, _opts: any) => ({ setData: () => {}, update: () => {} }),
    applyOptions: () => {},
    timeScale: () => ({ fitContent: () => {} }),
    remove: () => {}
  })
}))
