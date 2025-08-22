import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AllocationKey = 'active_trading' | 'long_term_etfs' | 'crypto' | 'futures' | 'stocks' | 'cash_buffer';

interface PortfolioState {
  allocations: Record<AllocationKey, number>;
  phaseView: 'phase1' | 'phase2';
  setAllocation: (k: AllocationKey, v: number) => void;
  setPhaseView: (v: 'phase1' | 'phase2') => void;
  rebalanceSuggestions: () => string[];
  normalize: () => void;
  incomeAllocation: { tfsa: number; rrsp: number; crypto: number; questrade: number };
  setIncomeAllocation: (k: keyof PortfolioState['incomeAllocation'], v: number) => void;
  hardwarePubKey: string;
  setHardwarePubKey: (v: string) => void;
}

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));

export const usePortfolioStore = create<PortfolioState>()(
  persist((set, get) => ({
  allocations: {
    active_trading: 60,
    long_term_etfs: 20,
    crypto: 10,
    futures: 5,
    stocks: 3,
    cash_buffer: 2,
  },
  phaseView: 'phase1',
  incomeAllocation: { tfsa: 20, rrsp: 20, crypto: 10, questrade: 50 },
  hardwarePubKey: '',
  setAllocation: (k, v) =>
    set((s) => ({ allocations: { ...s.allocations, [k]: clamp(Math.round(v), 0, 100) } })),
  setPhaseView: (v) =>
    set((s) => ({
      phaseView: v,
      allocations:
        v === 'phase1'
          ? { active_trading: 65, long_term_etfs: 15, crypto: 10, futures: 5, stocks: 3, cash_buffer: 2 }
          : { active_trading: 30, long_term_etfs: 45, crypto: 10, futures: 5, stocks: 5, cash_buffer: 5 },
    })),
  rebalanceSuggestions: () => {
    const total = Object.values(get().allocations).reduce((s, x) => s + x, 0);
    const out: string[] = [];
    if (total !== 100) out.push(`Allocations sum to ${total}%. Consider rebalancing to 100%.`);
    if (get().phaseView === 'phase1' && get().allocations.active_trading < 50)
      out.push('Phase 1 suggests >50% in Active Trading for cashflow.');
    if (get().phaseView === 'phase2' && get().allocations.long_term_etfs < 40)
      out.push('Phase 2 suggests >40% in Long-term ETFs for growth.');
    return out.length ? out : ['No alerts. Allocation looks good.'];
  },
  normalize: () => {
    const entries = Object.entries(get().allocations) as [AllocationKey, number][];
    const sum = entries.reduce((s, [, v]) => s + v, 0) || 1;
    const scaled = entries.reduce<Record<AllocationKey, number>>((acc, [k, v]) => {
      acc[k] = Math.round((v / sum) * 100);
      return acc;
    }, {} as any);
    set({ allocations: scaled });
  },
  setIncomeAllocation: (k, v) => set((s)=> ({ incomeAllocation: { ...s.incomeAllocation, [k]: clamp(Math.round(v), 0, 100) } })),
  setHardwarePubKey: (v) => set({ hardwarePubKey: v }),
  }), { name: 'fks-portfolio' })
);
