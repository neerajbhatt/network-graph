const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/network-graph`
  : '/api/network-graph';

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function putJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// --- Types ---
export interface NetworkNode {
  id: string;
  label: string;
  type: 'prescriber' | 'pharmacy';
  npi?: string;
  specialty?: string;
  state?: string;
  latitude?: number;
  longitude?: number;
}

export interface NetworkEdge {
  source: string;
  target: string;
  shared_member_count: number;
  risk_bucket: string;
  total_exposure: number;
}

export interface NetworkGraphData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  total_edges: number;
}

export interface PaginatedResponse<T> {
  total: number;
  offset: number;
  limit: number;
  data: T[];
}

export interface DoctorShopper {
  member_id: number;
  member_name: string;
  member_state?: string;
  pharmacy_count: number;
  prescriber_count: number;
  controlled_fill_count: number;
  total_exposure: number;
  risk_bucket: string;
  first_fill_date?: string;
  last_fill_date?: string;
}

export interface PharmacyHub {
  pharmacy_id: number;
  pharmacy_name: string;
  pharmacy_npi?: string;
  pharmacy_state?: string;
  distinct_prescriber_count: number;
  distinct_member_count: number;
  total_claims: number;
  total_exposure: number;
  risk_bucket: string;
}

export interface GeoOutlier {
  claim_id: number;
  member_id: number;
  member_name?: string;
  member_state?: string;
  member_zip?: string;
  pharmacy_id: number;
  pharmacy_name?: string;
  pharmacy_state?: string;
  pharmacy_zip?: string;
  drug_name?: string;
  drug_class?: string;
  fill_date?: string;
  paid_amount: number;
  distance_miles: number;
  risk_bucket: string;
  member_lat?: number;
  member_lon?: number;
  pharmacy_lat?: number;
  pharmacy_lon?: number;
}

export interface ConfigRule {
  rule_id?: number;
  rule_name: string;
  parameter_name: string;
  parameter_value: string;
  description?: string;
  updated_at?: string;
}

export interface KpiSummary {
  total_claims: number;
  total_exposure: number;
  total_members: number;
  total_flagged: number;
}

export interface DrillFill {
  claim_id: number;
  drug_name: string;
  ndc: string;
  fill_date: string;
  days_supply?: number;
  quantity?: number;
  paid_amount: number;
}

export interface DrillMember {
  member_id: number;
  member_name: string;
  fills: DrillFill[];
}

export interface DrillResponse {
  prescriber_id?: number;
  prescriber_name?: string;
  pharmacy_id?: number;
  pharmacy_name?: string;
  members: DrillMember[];
}

// --- API Calls ---
export function getNetworks(params?: Record<string, string>): Promise<NetworkGraphData> {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchJson<NetworkGraphData>(`/networks${qs}`);
}

export function drillNetwork(networkId: string): Promise<DrillResponse> {
  return fetchJson<DrillResponse>(`/networks/${networkId}/drill`);
}

export function getDoctorShoppers(params?: Record<string, string>): Promise<PaginatedResponse<DoctorShopper>> {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchJson<PaginatedResponse<DoctorShopper>>(`/doctor-shoppers${qs}`);
}

export function getPharmacyHubs(params?: Record<string, string>): Promise<PaginatedResponse<PharmacyHub>> {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchJson<PaginatedResponse<PharmacyHub>>(`/pharmacy-hubs${qs}`);
}

export function getGeoOutliers(params?: Record<string, string>): Promise<PaginatedResponse<GeoOutlier>> {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchJson<PaginatedResponse<GeoOutlier>>(`/geo-outliers${qs}`);
}

export function getConfigRules(): Promise<ConfigRule[]> {
  return fetchJson<ConfigRule[]>('/config/rules');
}

export function updateConfigRules(rules: ConfigRule[]): Promise<ConfigRule[]> {
  return putJson<ConfigRule[]>('/config/rules', { rules });
}

export function getKpi(): Promise<KpiSummary> {
  return fetchJson<KpiSummary>('/kpi');
}
