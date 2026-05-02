import { useEffect, useState } from 'react';
import KpiCards from '../components/KpiCards';
import RiskBadge from '../components/RiskBadge';
import { getPharmacyHubs, type PharmacyHub, type PaginatedResponse } from '../lib/api';

const BAR_COLORS: Record<string, string> = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#22c55e' };

export default function PharmacyHubsPage() {
  const [data, setData] = useState<PaginatedResponse<PharmacyHub> | null>(null);
  const [minPresc, setMinPresc] = useState('5');

  useEffect(() => {
    getPharmacyHubs({ min_prescribers: minPresc }).then(setData).catch(console.error);
  }, [minPresc]);

  const top20 = data?.data.slice(0, 20) ?? [];
  const maxPresc = top20.length ? Math.max(...top20.map((h) => h.distinct_prescriber_count)) : 1;

  return (
    <div>
      <KpiCards />
      <div className="flex items-center gap-4 mb-4">
        <h2 className="text-lg font-semibold">Pharmacy Hubs</h2>
        <div className="flex items-center gap-2 text-sm">
          <label className="text-gray-500">Min Prescribers:</label>
          <input type="number" value={minPresc} min="1" onChange={(e) => setMinPresc(e.target.value)}
            className="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm" />
        </div>
        {data && <span className="text-sm text-gray-500">{data.total} results</span>}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Bar chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Top Hubs by Prescriber Count</h3>
          <div className="space-y-2">
            {top20.map((h) => (
              <div key={h.pharmacy_id} className="flex items-center gap-2">
                <span className="w-32 text-xs text-gray-400 truncate" title={h.pharmacy_name}>
                  {h.pharmacy_name}
                </span>
                <div className="flex-1 bg-gray-800 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${(h.distinct_prescriber_count / maxPresc) * 100}%`,
                      backgroundColor: BAR_COLORS[h.risk_bucket] ?? '#6b7280',
                    }}
                  />
                </div>
                <span className="text-xs text-gray-300 w-8 text-right">{h.distinct_prescriber_count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left p-3">Pharmacy</th>
                <th className="text-left p-3">State</th>
                <th className="text-right p-3">Prescribers</th>
                <th className="text-right p-3">Members</th>
                <th className="text-right p-3">$ Exposure</th>
                <th className="text-center p-3">Risk</th>
              </tr>
            </thead>
            <tbody>
              {data?.data.map((h) => (
                <tr key={h.pharmacy_id} className="border-b border-gray-800/50 hover:bg-gray-800/50">
                  <td className="p-3 font-medium">{h.pharmacy_name}</td>
                  <td className="p-3 text-gray-400">{h.pharmacy_state}</td>
                  <td className="p-3 text-right">{h.distinct_prescriber_count}</td>
                  <td className="p-3 text-right">{h.distinct_member_count}</td>
                  <td className="p-3 text-right text-yellow-400">${h.total_exposure.toLocaleString()}</td>
                  <td className="p-3 text-center"><RiskBadge bucket={h.risk_bucket} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
