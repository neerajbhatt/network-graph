import { useEffect, useState } from 'react';
import KpiCards from '../components/KpiCards';
import { getConfigRules, updateConfigRules, type ConfigRule } from '../lib/api';

export default function ConfigPage() {
  const [rules, setRules] = useState<ConfigRule[]>([]);
  const [edited, setEdited] = useState<Map<string, string>>(new Map());
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getConfigRules().then(setRules).catch(console.error);
  }, []);

  const handleChange = (rule: ConfigRule, newValue: string) => {
    const key = `${rule.rule_name}::${rule.parameter_name}`;
    setEdited((prev) => new Map(prev).set(key, newValue));
  };

  const getValue = (rule: ConfigRule): string => {
    const key = `${rule.rule_name}::${rule.parameter_name}`;
    return edited.get(key) ?? rule.parameter_value;
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      const updatedRules = rules.map((r) => ({
        ...r,
        parameter_value: getValue(r),
      }));
      const saved = await updateConfigRules(updatedRules);
      setRules(saved);
      setEdited(new Map());
      setMessage('Configuration saved successfully.');
    } catch (err) {
      setMessage(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  // Group rules by rule_name
  const grouped = rules.reduce<Record<string, ConfigRule[]>>((acc, r) => {
    (acc[r.rule_name] ??= []).push(r);
    return acc;
  }, {});

  const RULE_LABELS: Record<string, string> = {
    suspicious_fills: 'Suspicious Fills (R1)',
    network_buckets: 'Network Buckets (R2)',
    doctor_shopping: 'Doctor Shopping (R4.2)',
    pharmacy_hubs: 'Pharmacy Hubs (R4.3)',
    geo_anomaly: 'Geo Anomaly (R6)',
  };

  return (
    <div>
      <KpiCards />
      <div className="max-w-3xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Detection Configuration</h2>
          <button
            onClick={handleSave}
            disabled={saving || edited.size === 0}
            className="bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded px-4 py-2 text-sm font-medium"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>

        {message && (
          <div className={`mb-4 p-3 rounded text-sm ${message.startsWith('Error') ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
            {message}
          </div>
        )}

        <div className="space-y-6">
          {Object.entries(grouped).map(([ruleName, params]) => (
            <div key={ruleName} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-primary-400 mb-3">
                {RULE_LABELS[ruleName] ?? ruleName}
              </h3>
              <div className="space-y-3">
                {params.map((r) => (
                  <div key={`${r.rule_name}-${r.parameter_name}`} className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="text-sm text-gray-300">{r.parameter_name}</div>
                      {r.description && <div className="text-xs text-gray-500">{r.description}</div>}
                    </div>
                    <input
                      type="text"
                      value={getValue(r)}
                      onChange={(e) => handleChange(r, e.target.value)}
                      className="w-32 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-right"
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
