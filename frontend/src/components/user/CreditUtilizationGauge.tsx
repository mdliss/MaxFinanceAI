'use client'

import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface CreditUtilizationGaugeProps {
  utilization: number; // 0-100
  limit: number;
  balance: number;
}

export default function CreditUtilizationGauge({ utilization, limit, balance }: CreditUtilizationGaugeProps) {
  const getColor = () => {
    if (utilization >= 80) return '#1e40af'; // deep blue
    if (utilization >= 50) return '#3b82f6'; // medium blue
    if (utilization >= 30) return '#60a5fa'; // light blue
    return '#93c5fd'; // very light blue
  };

  const data = [
    { name: 'Used', value: utilization },
    { name: 'Available', value: 100 - utilization },
  ];

  const COLORS = [getColor(), '#e0e0de'];

  return (
    <div className="card-dark p-6 transition-smooth">
      <h3 className="text-lg font-semibold mb-4">Credit Utilization</h3>

      <div className="relative">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              startAngle={180}
              endAngle={0}
              innerRadius={60}
              outerRadius={80}
              paddingAngle={0}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center Text */}
        <div className="absolute inset-0 flex items-center justify-center" style={{ marginTop: '-20px' }}>
          <div className="text-center">
            <div className="text-3xl font-bold" style={{ color: getColor() }}>
              {utilization.toFixed(1)}%
            </div>
            <div className="text-xs text-[var(--text-muted)]">Utilized</div>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-[var(--text-secondary)]">Balance:</span>
          <span className="font-semibold">${balance.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--text-secondary)]">Limit:</span>
          <span className="font-semibold">${limit.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--text-secondary)]">Available:</span>
          <span className="font-semibold">${(limit - balance).toLocaleString()}</span>
        </div>
      </div>

      {/* Warning Message */}
      {utilization >= 30 && (
        <div className={`mt-4 p-3 rounded-lg text-sm transition-smooth ${
          utilization >= 80 ? 'bg-blue-500/10 text-blue-900 border border-blue-500/20' :
          utilization >= 50 ? 'bg-blue-400/10 text-blue-800 border border-blue-400/20' :
          'bg-blue-300/10 text-blue-700 border border-blue-300/20'
        }`}>
          {utilization >= 80 ? 'High utilization may impact your credit score' :
           utilization >= 50 ? 'Consider reducing utilization below 50%' :
           'Keeping utilization below 30% is ideal'}
        </div>
      )}
    </div>
  );
}
