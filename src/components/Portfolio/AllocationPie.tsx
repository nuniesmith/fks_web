import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import React from 'react';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface Props {
  data: Record<string, number>;
}

const AllocationPie: React.FC<Props> = ({ data }) => {
  const labels = Object.keys(data);
  const values = Object.values(data);
  const colors = ['#60a5fa', '#a78bfa', '#34d399', '#f472b6', '#f59e0b', '#f87171'];
  return (
    <Doughnut
      data={{
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: values.map((_, i) => colors[i % colors.length]),
            borderWidth: 0,
          },
        ],
      }}
      options={{
        plugins: { legend: { labels: { color: '#e5e7eb' } } },
      }}
    />
  );
};

export default AllocationPie;
