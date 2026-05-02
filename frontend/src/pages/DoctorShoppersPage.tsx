import { useEffect, useState } from 'react';
import KpiCards from '../components/KpiCards';
import RiskBadge from '../components/RiskBadge';
import { getDoctorShoppers, type DoctorShopper, type PaginatedResponse } from '../lib/api';

export default function DoctorShoppersPage() {
  const [data, setData] = useState<PaginatedResponse<DoctorShopper> | null>(null);
  const [minPharm, setMinPharm] = useState('3');
  const [selected, setSelected] = useState<DoctorShopper | null>(null);

  useEffect(() => {
    getDoctorShoppers({ min_pharmacies: minPharm }).then(setData).catch(console.error);
  }, [minPharm]);

  return (
    <div>
      <KpiCards />
      <div className="flex gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-4">
            <h2 className="text-lg font-semibold">Doctor Shoppers</h2>
            <div className="flex items-center gap-2 text-sm">
              <label className="text-gray-500">Min Pharmacies:</label>
              <input type="number" value={minPharm} min="1" onChange={(e) => setMinPharm(e.target.value)}
                className="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm" />
            </div>
            {data && <span className="text-sm text-gray-500">{data.total} results</span>}
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                  <th className="text-left p-3">Member</th>
                  <th className="text-left p-3">State</th>
                  <th className="text-right p-3">Pharmacies</th>
                  <th className="text-right p-3">Prescribers</th>
                  <th className="text-right p-3">Fills</th>
                  <th className="text-right p-3">$ Exposure</th>
                  <th className="text-center p-3">Risk</th>
                </tr>
              </thead>
              <tbody>
                {data?.data.map((s) => (
                  <tr key={s.member_id}
                    onClick={() => setSelected(s)}
                    className="border-b border-gray-800/50 hover:bg-gray-800/50 cursor-pointer">
                    <td className="p-3 font-medium">{s.member_name}</td>
                    <td className="p-3 text-gray-400">{s.member_state}</td>
                    <td className="p-3 text-right">{s.pharmacy_count}</td>
                    <td className="p-3 text-right">{s.prescriber_count}</td>
                    <td className="p-3 text-right">{s.controlled_fill_count}</td>
                    <td className="p-3 text-right text-yellow-400">${s.total_exposure.toLocaleString()}</td>
                    <td className="p-3 text-center"><RiskBadge bucket={s.risk_bucket} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail drawer */}
        {selected && (
          <div className="w-80 flex-shrink-0 bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-semibold">{selected.member_name}</h3>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-gray-300 text-xs">Close</button>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Member ID</span><span>{selected.member_id}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">State</span><span>{selected.member_state}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Pharmacies</span><span className="text-red-400">{selected.pharmacy_count}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Prescribers</span><span className="text-red-400">{selected.prescriber_count}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Fills</span><span>{selected.controlled_fill_count}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Exposure</span><span className="text-yellow-400">${selected.total_exposure.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Risk</span><RiskBadge bucket={selected.risk_bucket} /></div>
              <div className="flex justify-between"><span className="text-gray-500">First Fill</span><span>{selected.first_fill_date}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Last Fill</span><span>{selected.last_fill_date}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
