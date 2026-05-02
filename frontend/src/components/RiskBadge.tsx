interface RiskBadgeProps {
  bucket: string;
}

export default function RiskBadge({ bucket }: RiskBadgeProps) {
  const colors: Record<string, string> = {
    HIGH: 'bg-red-500/20 text-red-400 border-red-500/30',
    MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    LOW: 'bg-green-500/20 text-green-400 border-green-500/30',
  };
  const cls = colors[bucket] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30';

  return (
    <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded border ${cls}`}>
      {bucket}
    </span>
  );
}
