'use client'

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface SpendingCategory {
  category: string;
  amount: number;
  percentage: number;
}

interface SpendingPieChartProps {
  data: SpendingCategory[];
}

const COLORS = [
  '#2c3e50', // primary dark
  '#34495e', // secondary dark
  '#475569', // slate
  '#64748b', // light slate
  '#94a3b8', // lighter slate
  '#cbd5e1', // very light slate
  '#e2e8f0', // almost white
];

export default function SpendingPieChart({ data }: SpendingPieChartProps) {
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            {formatCurrency(payload[0].value)} ({payload[0].payload.percentage.toFixed(1)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-dark p-6 transition-smooth">
      <h3 className="text-lg font-semibold mb-4">Spending Breakdown</h3>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ percentage }) => `${percentage.toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="amount"
            nameKey="category"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                className="transition-smooth hover:opacity-80"
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Category List */}
      <div className="mt-6 space-y-2">
        {data.map((item, index) => (
          <div key={item.category} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full transition-smooth"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <span className="text-[var(--text-secondary)]">{item.category}</span>
            </div>
            <span className="font-semibold">{formatCurrency(item.amount)}</span>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="mt-4 pt-4 border-t border-[var(--border-color)] flex justify-between font-semibold">
        <span>Total Spending</span>
        <span>${data.reduce((sum, item) => sum + item.amount, 0).toLocaleString()}</span>
      </div>
    </div>
  );
}
