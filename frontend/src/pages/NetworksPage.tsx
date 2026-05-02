import { useCallback, useEffect, useRef, useState } from 'react';
import KpiCards from '../components/KpiCards';
import { drillNetwork, getNetworks, type DrillResponse, type NetworkGraphData, type NetworkNode } from '../lib/api';

const BUCKET_COLORS: Record<string, string> = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#22c55e' };
const NODE_COLORS: Record<string, string> = { prescriber: '#3b82f6', pharmacy: '#a855f7' };

interface GraphNode extends NetworkNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  shared_member_count: number;
  risk_bucket: string;
  total_exposure: number;
}

export default function NetworksPage() {
  const [data, setData] = useState<NetworkGraphData | null>(null);
  const [drill, setDrill] = useState<DrillResponse | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [bucket, setBucket] = useState<string>('');
  const [drugClass, setDrugClass] = useState<string>('');
  const [minShared, setMinShared] = useState<string>('1');
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (bucket) params.bucket = bucket;
    if (drugClass) params.drug_class = drugClass;
    if (minShared && parseInt(minShared) > 1) params.min_shared = minShared;
    getNetworks(params).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [bucket, drugClass, minShared]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
    drillNetwork(nodeId).then(setDrill).catch(console.error);
  };

  return (
    <div>
      <KpiCards />
      <div className="flex gap-6">
        {/* Left rail filters */}
        <div className="w-56 flex-shrink-0 space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase">Filters</h3>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Risk Bucket</label>
            <select value={bucket} onChange={(e) => setBucket(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm">
              <option value="">All</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Drug Class</label>
            <select value={drugClass} onChange={(e) => setDrugClass(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm">
              <option value="">All</option>
              <option value="opioids">Opioids</option>
              <option value="benzodiazepines">Benzodiazepines</option>
              <option value="stimulants">Stimulants</option>
              <option value="gabapentinoids">Gabapentinoids</option>
              <option value="muscle_relaxants">Muscle Relaxants</option>
              <option value="sedatives">Sedatives</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Min Shared Members</label>
            <input type="number" value={minShared} min="1" onChange={(e) => setMinShared(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm" />
          </div>
          <button onClick={fetchData}
            className="w-full bg-primary-600 hover:bg-primary-700 text-white rounded px-3 py-2 text-sm font-medium">
            Apply Filters
          </button>

          <div className="pt-4 space-y-2 text-xs text-gray-500">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" /> Prescriber
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-purple-500 inline-block" /> Pharmacy
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1 bg-red-500 inline-block" /> HIGH
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1 bg-yellow-500 inline-block" /> MEDIUM
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1 bg-green-500 inline-block" /> LOW
            </div>
          </div>
        </div>

        {/* Graph area */}
        <div className="flex-1 bg-gray-900 border border-gray-800 rounded-lg overflow-hidden" style={{ minHeight: 500 }}>
          {loading && <div className="p-8 text-gray-500">Loading network...</div>}
          {!loading && data && <ForceGraph data={data} onNodeClick={handleNodeClick} selectedNode={selectedNode} />}
          {!loading && !data && <div className="p-8 text-gray-500">No data</div>}
        </div>

        {/* Drill panel */}
        {drill && (
          <div className="w-80 flex-shrink-0 bg-gray-900 border border-gray-800 rounded-lg p-4 max-h-[600px] overflow-y-auto">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-semibold text-gray-300">
                {drill.prescriber_name ?? drill.pharmacy_name ?? selectedNode}
              </h3>
              <button onClick={() => { setDrill(null); setSelectedNode(null); }}
                className="text-gray-500 hover:text-gray-300 text-xs">Close</button>
            </div>
            <div className="text-xs text-gray-500 mb-3">{drill.members.length} members</div>
            {drill.members.slice(0, 20).map((m) => (
              <div key={m.member_id} className="mb-3 border-b border-gray-800 pb-2">
                <div className="text-sm font-medium text-gray-300">{m.member_name}</div>
                {m.fills.map((f) => (
                  <div key={f.claim_id} className="text-xs text-gray-500 ml-2">
                    {f.fill_date} &middot; {f.drug_name} &middot; ${f.paid_amount.toFixed(2)}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ForceGraph({ data, onNodeClick, selectedNode }: {
  data: NetworkGraphData;
  onNodeClick: (id: string) => void;
  selectedNode: string | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<GraphNode[]>([]);
  const linksRef = useRef<GraphLink[]>([]);
  const animRef = useRef<number>(0);

  useEffect(() => {
    const nodes: GraphNode[] = data.nodes.map((n, i) => ({
      ...n,
      x: 300 + Math.cos(i * 0.5) * 200 + Math.random() * 100,
      y: 250 + Math.sin(i * 0.5) * 200 + Math.random() * 100,
      vx: 0,
      vy: 0,
    }));
    const links: GraphLink[] = data.edges.map((e) => ({ ...e }));
    nodesRef.current = nodes;
    linksRef.current = links;

    // Simple force simulation
    let iteration = 0;
    const maxIter = 200;

    function simulate() {
      const ns = nodesRef.current;
      const ls = linksRef.current;

      // Repulsion
      for (let i = 0; i < ns.length; i++) {
        for (let j = i + 1; j < ns.length; j++) {
          const dx = (ns[i].x ?? 0) - (ns[j].x ?? 0);
          const dy = (ns[i].y ?? 0) - (ns[j].y ?? 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 500 / (dist * dist);
          ns[i].vx = (ns[i].vx ?? 0) + (dx / dist) * force;
          ns[i].vy = (ns[i].vy ?? 0) + (dy / dist) * force;
          ns[j].vx = (ns[j].vx ?? 0) - (dx / dist) * force;
          ns[j].vy = (ns[j].vy ?? 0) - (dy / dist) * force;
        }
      }

      // Attraction along links
      const nodeMap = new Map(ns.map((n) => [n.id, n]));
      for (const link of ls) {
        const srcId = typeof link.source === 'string' ? link.source : link.source.id;
        const tgtId = typeof link.target === 'string' ? link.target : link.target.id;
        const src = nodeMap.get(srcId);
        const tgt = nodeMap.get(tgtId);
        if (!src || !tgt) continue;
        const dx = (tgt.x ?? 0) - (src.x ?? 0);
        const dy = (tgt.y ?? 0) - (src.y ?? 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 80) * 0.01;
        src.vx = (src.vx ?? 0) + (dx / dist) * force;
        src.vy = (src.vy ?? 0) + (dy / dist) * force;
        tgt.vx = (tgt.vx ?? 0) - (dx / dist) * force;
        tgt.vy = (tgt.vy ?? 0) - (dy / dist) * force;
      }

      // Center gravity
      for (const n of ns) {
        n.vx = ((n.vx ?? 0) + (300 - (n.x ?? 0)) * 0.001) * 0.9;
        n.vy = ((n.vy ?? 0) + (250 - (n.y ?? 0)) * 0.001) * 0.9;
        n.x = (n.x ?? 0) + (n.vx ?? 0);
        n.y = (n.y ?? 0) + (n.vy ?? 0);
      }

      draw();
      iteration++;
      if (iteration < maxIter) {
        animRef.current = requestAnimationFrame(simulate);
      }
    }

    function draw() {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      canvas.width = canvas.parentElement?.clientWidth ?? 600;
      canvas.height = 500;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw edges
      const nodeMap = new Map(nodesRef.current.map((n) => [n.id, n]));
      for (const link of linksRef.current) {
        const srcId = typeof link.source === 'string' ? link.source : link.source.id;
        const tgtId = typeof link.target === 'string' ? link.target : link.target.id;
        const src = nodeMap.get(srcId);
        const tgt = nodeMap.get(tgtId);
        if (!src || !tgt) continue;
        ctx.beginPath();
        ctx.moveTo(src.x ?? 0, src.y ?? 0);
        ctx.lineTo(tgt.x ?? 0, tgt.y ?? 0);
        ctx.strokeStyle = BUCKET_COLORS[link.risk_bucket] ?? '#666';
        ctx.lineWidth = Math.min(link.shared_member_count / 10, 5);
        ctx.globalAlpha = 0.6;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // Draw nodes
      for (const node of nodesRef.current) {
        ctx.beginPath();
        const r = node.type === 'prescriber' ? 6 : 8;
        ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, Math.PI * 2);
        ctx.fillStyle = NODE_COLORS[node.type] ?? '#888';
        if (selectedNode === node.id) {
          ctx.fillStyle = '#ffffff';
        }
        ctx.fill();
        ctx.strokeStyle = '#1f2937';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }

    simulate();
    return () => cancelAnimationFrame(animRef.current);
  }, [data, selectedNode]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    for (const node of nodesRef.current) {
      const dx = (node.x ?? 0) - x;
      const dy = (node.y ?? 0) - y;
      if (Math.sqrt(dx * dx + dy * dy) < 10) {
        onNodeClick(node.id);
        return;
      }
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <canvas ref={canvasRef} onClick={handleClick} className="cursor-pointer" style={{ width: '100%', height: 500 }} />
      <div className="absolute top-2 right-2 text-xs text-gray-500">
        {data.nodes.length} nodes, {data.total_edges} edges
      </div>
    </div>
  );
}
