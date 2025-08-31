import React, { Suspense } from 'react';
// Dynamically imported heavy recharts primitives colocated in one lazy chunk
const LazyChartBundle = React.lazy(() => import('../../features/lazy/RechartsMonteCarlo'));

export interface MonteCarloChartRow {
  step: number;
  p5: number;
  p50: number;
  p95: number;
  bandLow: number;
  bandDiff: number;
  [k: string]: number; // sample paths p0..pN
}

interface Props {
  rows: MonteCarloChartRow[];
  sampleCount: number;
}

const MonteCarloPathsChart: React.FC<Props> = ({ rows, sampleCount }) => {
  return (
    <Suspense fallback={<div className="text-xs text-white/50">Loading simulation chart...</div>}>
      <LazyChartBundle rows={rows} sampleCount={sampleCount} />
    </Suspense>
  );
};

export default MonteCarloPathsChart;
