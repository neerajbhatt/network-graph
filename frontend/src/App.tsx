import { useState } from 'react';
import NetworksPage from './pages/NetworksPage';
import DoctorShoppersPage from './pages/DoctorShoppersPage';
import PharmacyHubsPage from './pages/PharmacyHubsPage';
import GeoOutliersPage from './pages/GeoOutliersPage';
import ConfigPage from './pages/ConfigPage';

const TABS = [
  { id: 'networks', label: 'Networks' },
  { id: 'doctor-shoppers', label: 'Doctor Shoppers' },
  { id: 'pharmacy-hubs', label: 'Pharmacy Hubs' },
  { id: 'geo-outliers', label: 'Geo Outliers' },
  { id: 'config', label: 'Config' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('networks');

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary-400">Network Graph</h1>
          <span className="text-sm text-gray-500">Pharmacy Fraud & Abuse Detection</span>
        </div>
      </header>

      {/* Tabs */}
      <nav className="border-b border-gray-800 bg-gray-900/50 px-6">
        <div className="flex space-x-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-primary-500 text-primary-400'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="p-6">
        {activeTab === 'networks' && <NetworksPage />}
        {activeTab === 'doctor-shoppers' && <DoctorShoppersPage />}
        {activeTab === 'pharmacy-hubs' && <PharmacyHubsPage />}
        {activeTab === 'geo-outliers' && <GeoOutliersPage />}
        {activeTab === 'config' && <ConfigPage />}
      </main>
    </div>
  );
}
