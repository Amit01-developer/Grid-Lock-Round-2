import { Filter, RefreshCcw } from 'lucide-react';
import { useState } from 'react';
import HeatmapMap from '../components/maps/HeatmapMap.jsx';
import EmptyState from '../components/states/EmptyState.jsx';
import ErrorState from '../components/states/ErrorState.jsx';
import LoadingState from '../components/states/LoadingState.jsx';
import Button from '../components/ui/Button.jsx';
import PageHeader from '../components/ui/PageHeader.jsx';
import useAsyncData from '../hooks/useAsyncData.js';
import { getHeatmap } from '../services/api.js';
import { formatNumber, formatViolationType } from '../utils/formatters.js';

const violationTypes = [
  { value: '', label: 'All violations' },
  { value: 'helmet_non_compliance', label: 'Helmet non-compliance' },
  { value: 'triple_riding', label: 'Triple riding' },
  { value: 'wrong_side_driving', label: 'Wrong-side driving' },
  { value: 'illegal_parking', label: 'Illegal parking' },
];

export default function Heatmap() {
  const [days, setDays] = useState(30);
  const [violationType, setViolationType] = useState('');

  const { data, error, loading, reload } = useAsyncData(
    () => getHeatmap({ days, violationType }),
    [days, violationType],
  );

  return (
    <>
      <PageHeader
        eyebrow="Spatial Intelligence"
        title="Violation Heatmap"
        description="Map recurring traffic violation hotspots using camera coordinates and detection intensity."
        actions={
          <Button icon={RefreshCcw} variant="secondary" onClick={reload}>
            Refresh
          </Button>
        }
      />

      <section className="surface mb-5 p-4">
        <div className="grid gap-4 md:grid-cols-[180px_minmax(220px,260px)_1fr] md:items-end">
          <label className="block">
            <span className="mb-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">Window</span>
            <select
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
              className="focus-ring w-full border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">Violation type</span>
            <select
              value={violationType}
              onChange={(event) => setViolationType(event.target.value)}
              className="focus-ring w-full border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
            >
              {violationTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            <Filter size={16} />
            <span>{formatViolationType(violationType || 'all violations')}</span>
          </div>
        </div>
      </section>

      {loading ? <LoadingState label="Loading heatmap" /> : null}
      {error ? <ErrorState message={error.message} onRetry={reload} /> : null}
      {!loading && !error ? (
        <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="surface overflow-hidden">
            <HeatmapMap points={data?.points || []} />
          </div>
          <div className="surface p-5">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Hotspot Ranking</h2>
            {data?.points?.length ? (
              <div className="mt-4 space-y-3">
                {data.points.slice(0, 8).map((point) => (
                  <div key={point.camera_id || point.camera_name} className="border border-slate-200 p-3 dark:border-slate-800">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-950 dark:text-white">{point.camera_name}</div>
                        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{point.location_name}</div>
                      </div>
                      <div className="text-sm font-semibold text-civic-authority dark:text-teal-300">
                        {formatNumber(point.intensity)}
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                      Dominant: {formatViolationType(point.dominant_violation_type)}
                    </div>
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      Severity: {formatNumber(point.severity_score)} | Safety Index: {point.safety_index ?? 100}/100
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No mapped hotspots" message="Heatmap points require violations linked to camera coordinates." />
            )}
          </div>
        </section>
      ) : null}
    </>
  );
}

