'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface SavingsDataPoint {
  date: string;
  balance: number;
  month: string;
}

interface SavingsLineChartProps {
  data: SavingsDataPoint[];
  growthRate: number;
}

export default function SavingsLineChart({ data, growthRate }: SavingsLineChartProps) {
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-sm">{payload[0].payload.month}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            Balance: {formatCurrency(payload[0].value)}
          </p>
        </div>
      );
    }
    return null;
  };

  const currentBalance = data[data.length - 1]?.balance || 0;
  const startBalance = data[0]?.balance || 0;
  const absoluteGrowth = currentBalance - startBalance;

  return (
    <div className="card-dark p-6 transition-smooth">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Savings Growth</h3>
        <div className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${
          growthRate >= 2 ? 'bg-slate-500/10 text-slate-700' :
          growthRate >= 0 ? 'bg-blue-500/10 text-blue-700' :
          'bg-red-500/10 text-red-700'
        }`}>
          {growthRate >= 0 ? '+' : ''}{growthRate.toFixed(1)}% Growth
        </div>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2c3e50" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#2c3e50" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#d4d4d2" opacity={0.5} />
          <XAxis
            dataKey="month"
            stroke="#6b6b6b"
            tick={{ fill: '#6b6b6b', fontSize: 12 }}
          />
          <YAxis
            stroke="#6b6b6b"
            tick={{ fill: '#6b6b6b', fontSize: 12 }}
            tickFormatter={formatCurrency}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="balance"
            stroke="#2c3e50"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorBalance)"
            className="transition-smooth"
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-xs text-[var(--text-muted)] mb-1">Current Balance</div>
          <div className="text-lg font-semibold">{formatCurrency(currentBalance)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-[var(--text-muted)] mb-1">Growth</div>
          <div className={`text-lg font-semibold ${absoluteGrowth >= 0 ? 'text-slate-700' : 'text-red-700'}`}>
            {absoluteGrowth >= 0 ? '+' : ''}{formatCurrency(absoluteGrowth)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-[var(--text-muted)] mb-1">Rate</div>
          <div className={`text-lg font-semibold ${growthRate >= 0 ? 'text-slate-700' : 'text-red-700'}`}>
            {growthRate >= 0 ? '+' : ''}{growthRate.toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
}
