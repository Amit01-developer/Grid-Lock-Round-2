import { ShieldCheck } from 'lucide-react';
import { formatNumber } from '../../utils/formatters.js';
import { cn } from '../../utils/cn.js';

export default function SafetyIndexPanel({ safetyIndex }) {
  const score = safetyIndex?.score ?? 100;
  const tone =
    score >= 80
      ? 'text-teal-700 dark:text-teal-300'
      : score >= 60
        ? 'text-amber-700 dark:text-amber-300'
        : 'text-red-700 dark:text-red-300';

  return (
    <div className="surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Smart City Safety Index
          </p>
          <div className={cn('mt-3 text-4xl font-semibold', tone)}>{score}/100</div>
          <p className="mt-2 text-sm capitalize text-slate-600 dark:text-slate-400">
            {safetyIndex?.risk_level || 'low'} risk posture
          </p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center bg-slate-100 text-civic-authority dark:bg-slate-900 dark:text-teal-300">
          <ShieldCheck size={22} />
        </div>
      </div>
      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
        <Metric label="Severity" value={formatNumber(safetyIndex?.total_severity)} />
        <Metric label="Average" value={safetyIndex?.average_severity ?? 0} />
        <Metric label="Night cases" value={formatNumber(safetyIndex?.night_violations)} />
        <Metric label="School zone" value={formatNumber(safetyIndex?.school_zone_violations)} />
      </dl>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="border border-slate-200 p-3 dark:border-slate-800">
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="mt-1 font-semibold text-slate-950 dark:text-white">{value}</dd>
    </div>
  );
}

