import { useEffect, useState } from 'react';
import { getKpi, type KpiSummary } from '../lib/api';

function fmt$(n: number): string {
  return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export default function KpiCards() {
  const [kpi, setKpi] = useState<KpiSummary | null>(null);

  useEffect(() => {
    getKpi().then(setKpi).catch(console.error);
  }, []);

  if (!kpi) return <div className="text-gray-500 text-sm">Loading KPIs...</div>;

  const cards = [
    { label: 'Controlled Claims', value: kpi.total_claims.toLocaleString(), color: 'text-blue-400' },
    { label: '$ Exposure', value: fmt$(kpi.total_exposure), color: 'text-yellow-400' },
    { label: 'Members', value: kpi.total_members.toLocaleString(), color: 'text-green-400' },
    { label: 'Flagged', value: kpi.total_flagged.toLocaleString(), color: 'text-red-400' },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {cards.map((c) => (
        <div key={c.label} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide">{c.label}</div>
          <div className={`text-2xl font-bold mt-1 ${c.color}`}>{c.value}</div>
        </div>
      ))}
    </div>
  );
}
