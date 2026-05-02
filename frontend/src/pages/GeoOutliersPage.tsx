import { useEffect, useRef, useState } from 'react';
import type * as LType from 'leaflet';
import KpiCards from '../components/KpiCards';
import RiskBadge from '../components/RiskBadge';
import { getGeoOutliers, type GeoOutlier, type PaginatedResponse } from '../lib/api';

const LINE_COLORS: Record<string, string> = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#22c55e' };

export default function GeoOutliersPage() {
  const [data, setData] = useState<PaginatedResponse<GeoOutlier> | null>(null);
  const [minMiles, setMinMiles] = useState('50');
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<LType.Map | null>(null);
  const layerRef = useRef<LType.LayerGroup | null>(null);

  useEffect(() => {
    getGeoOutliers({ min_miles: minMiles }).then(setData).catch(console.error);
  }, [minMiles]);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapRef.current || leafletMapRef.current) return;

    const loadLeaflet = async () => {
      const L = await import('leaflet');

      const map = L.map(mapRef.current!, { zoomControl: true }).setView([39.8, -98.5], 4);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
      }).addTo(map);

      leafletMapRef.current = map;
      layerRef.current = L.layerGroup().addTo(map);
    };

    loadLeaflet().catch(console.error);

    return () => {
      leafletMapRef.current?.remove();
      leafletMapRef.current = null;
    };
  }, []);

  // Draw lines when data changes
  useEffect(() => {
    if (!layerRef.current || !data) return;

    const loadLeaflet = async () => {
      const L = await import('leaflet');
      const layer = layerRef.current!;
      layer.clearLayers();

      for (const o of data.data) {
        if (o.member_lat == null || o.member_lon == null || o.pharmacy_lat == null || o.pharmacy_lon == null) continue;

        const color = LINE_COLORS[o.risk_bucket] ?? '#6b7280';

        // Line from member to pharmacy
        L.polyline(
          [[o.member_lat, o.member_lon], [o.pharmacy_lat, o.pharmacy_lon]],
          { color, weight: 2, opacity: 0.7 },
        ).addTo(layer);

        // Member marker
        L.circleMarker([o.member_lat, o.member_lon], {
          radius: 4, fillColor: '#3b82f6', color: '#1e3a8a', weight: 1, fillOpacity: 0.8,
        }).bindPopup(`<b>${o.member_name ?? 'Member'}</b><br/>ID: ${o.member_id}<br/>${o.member_state} ${o.member_zip}`).addTo(layer);

        // Pharmacy marker
        L.circleMarker([o.pharmacy_lat, o.pharmacy_lon], {
          radius: 5, fillColor: '#a855f7', color: '#581c87', weight: 1, fillOpacity: 0.8,
        }).bindPopup(`<b>${o.pharmacy_name ?? 'Pharmacy'}</b><br/>${o.pharmacy_state} ${o.pharmacy_zip}`).addTo(layer);
      }
    };

    loadLeaflet().catch(console.error);
  }, [data]);

  return (
    <div>
      <KpiCards />
      <div className="flex items-center gap-4 mb-4">
        <h2 className="text-lg font-semibold">Geo Outliers</h2>
        <div className="flex items-center gap-2 text-sm">
          <label className="text-gray-500">Min Miles:</label>
          <input type="number" value={minMiles} min="0" onChange={(e) => setMinMiles(e.target.value)}
            className="w-20 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm" />
        </div>
        {data && <span className="text-sm text-gray-500">{data.total} results</span>}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Map */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div ref={mapRef} style={{ height: 500, width: '100%' }} />
        </div>

        {/* Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden max-h-[500px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-gray-900">
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left p-3">Member</th>
                <th className="text-left p-3">Pharmacy</th>
                <th className="text-left p-3">Drug</th>
                <th className="text-right p-3">Miles</th>
                <th className="text-right p-3">$ Amount</th>
                <th className="text-center p-3">Risk</th>
              </tr>
            </thead>
            <tbody>
              {data?.data.map((o) => (
                <tr key={o.claim_id} className="border-b border-gray-800/50 hover:bg-gray-800/50">
                  <td className="p-3">
                    <div className="font-medium">{o.member_name}</div>
                    <div className="text-xs text-gray-500">{o.member_state} {o.member_zip}</div>
                  </td>
                  <td className="p-3">
                    <div>{o.pharmacy_name}</div>
                    <div className="text-xs text-gray-500">{o.pharmacy_state} {o.pharmacy_zip}</div>
                  </td>
                  <td className="p-3 text-gray-400">{o.drug_name}</td>
                  <td className="p-3 text-right text-red-400">{o.distance_miles.toFixed(1)}</td>
                  <td className="p-3 text-right text-yellow-400">${o.paid_amount.toFixed(2)}</td>
                  <td className="p-3 text-center"><RiskBadge bucket={o.risk_bucket} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
