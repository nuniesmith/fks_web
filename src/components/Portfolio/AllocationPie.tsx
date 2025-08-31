import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

interface Props { data: Record<string, number>; }
const palette = ['#60a5fa', '#a78bfa', '#34d399', '#f472b6', '#f59e0b', '#f87171'];

const AllocationPie: React.FC<Props> = ({ data }) => {
  const entries = Object.entries(data);
  const total = entries.reduce((a, [, v]) => a + v, 0) || 1;
  const chartData = entries.map(([name, value]) => ({ name, value }));
  return (
    <div className="p-4 bg-white/5 rounded border border-white/10">
      <h3 className="text-white text-sm font-semibold mb-2">Allocation Breakdown</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={40} outerRadius={70} stroke="none">
              {chartData.map((_, i) => <Cell key={i} fill={palette[i % palette.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', fontSize: '0.75rem' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-1 text-[11px] text-white/70">
        {chartData.map((d, i) => (
          <li key={d.name} className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-sm" style={{ background: palette[i % palette.length] }} />
            <span className="truncate" title={d.name}>{d.name}</span>
            <span className="ml-auto text-white/50">{((d.value / total) * 100).toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AllocationPie;
