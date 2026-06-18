import { AlertTriangle, CalendarDays, Moon, School, ShieldCheck } from 'lucide-react';
import SafetyIndexPanel from '../components/analytics/SafetyIndexPanel.jsx';
import DailyStatisticsChart from '../components/charts/DailyStatisticsChart.jsx';
import StatusDoughnutChart from '../components/charts/StatusDoughnutChart.jsx';
import TrendLineChart from '../components/charts/TrendLineChart.jsx';
import ViolationTypeChart from '../components/charts/ViolationTypeChart.jsx';
import WeeklyStatisticsChart from '../components/charts/WeeklyStatisticsChart.jsx';
import EmptyState from '../components/states/EmptyState.jsx';
import ErrorState from '../components/states/ErrorState.jsx';
import LoadingState from '../components/states/LoadingState.jsx';
import MetricCard from '../components/ui/MetricCard.jsx';
import PageHeader from '../components/ui/PageHeader.jsx';
import useAsyncData from '../hooks/useAsyncData.js';
import { getAnalytics } from '../services/api.js';
import { formatNumber } from '../utils/formatters.js';

export default function Analytics() {
  const { data, error, loading, reload } = useAsyncData(() => getAnalytics(30), []);

  if (loading) {
    return <LoadingState label="Loading analytics" />;
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  return (
    <>
      <PageHeader
        eyebrow="Performance Analytics"
        title="Violation Analytics"
        description="Operational metrics grouped by type, status, camera location, and reporting trend."
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Total" value={formatNumber(data.total_violations)} detail="All violation records" />
        <MetricCard title="Pending review" value={formatNumber(data.pending_review)} detail="Awaiting officer decision" tone="warning" />
        <MetricCard title="Confirmed" value={formatNumber(data.confirmed)} detail="Validated enforcement cases" tone="success" />
        <MetricCard title="Rejected" value={formatNumber(data.rejected)} detail="Dismissed records" />
      </section>

      <section className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Safety Index"
          value={`${data.safety_index?.score ?? 100}/100`}
          detail={`${data.safety_index?.risk_level || 'low'} risk posture`}
          icon={ShieldCheck}
          tone={(data.safety_index?.score ?? 100) >= 75 ? 'success' : 'warning'}
        />
        <MetricCard
          title="Severity score"
          value={formatNumber(data.safety_index?.total_severity)}
          detail="Weighted policy risk"
          icon={AlertTriangle}
          tone="danger"
        />
        <MetricCard
          title="Night violations"
          value={formatNumber(data.safety_index?.night_violations)}
          detail="Includes +10 severity"
          icon={Moon}
          tone="warning"
        />
        <MetricCard
          title="School zone"
          value={formatNumber(data.safety_index?.school_zone_violations)}
          detail="Includes +15 severity"
          icon={School}
          tone="default"
        />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-3">
        <div className="surface p-5 xl:col-span-2">
          <h2 className="mb-4 text-base font-semibold text-slate-950 dark:text-white">Daily Trend</h2>
          {data.trend?.length ? (
            <div className="h-80">
              <TrendLineChart data={data.trend} />
            </div>
          ) : (
            <EmptyState title="No trend available" message="Trend points are created from stored violation timestamps." />
          )}
        </div>

        <div className="surface p-5">
          <h2 className="mb-4 text-base font-semibold text-slate-950 dark:text-white">Review Status</h2>
          {data.by_status?.length ? (
            <div className="h-80">
              <StatusDoughnutChart data={data.by_status} />
            </div>
          ) : (
            <EmptyState title="No status data" message="Status counts appear after violations are created." />
          )}
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="surface p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Daily Statistics</h2>
            <CalendarDays size={18} className="text-slate-500" />
          </div>
          {data.daily_statistics?.length ? (
            <div className="h-80">
              <DailyStatisticsChart data={data.daily_statistics} />
            </div>
          ) : (
            <EmptyState title="No daily statistics" message="Daily totals and safety index appear after violations are detected." />
          )}
        </div>
        <SafetyIndexPanel safetyIndex={data.safety_index} />
      </section>

      <section className="mt-5">
        <div className="surface p-5">
          <h2 className="mb-4 text-base font-semibold text-slate-950 dark:text-white">Weekly Statistics</h2>
          {data.weekly_statistics?.length ? (
            <div className="h-80">
              <WeeklyStatisticsChart data={data.weekly_statistics} />
            </div>
          ) : (
            <EmptyState title="No weekly statistics" message="Weekly severity and volume will appear as evidence accumulates." />
          )}
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="surface p-5">
          <h2 className="mb-4 text-base font-semibold text-slate-950 dark:text-white">Violation Types</h2>
          {data.by_type?.length ? (
            <div className="h-80">
              <ViolationTypeChart data={data.by_type} />
            </div>
          ) : (
            <EmptyState title="No type data" message="Helmet, triple riding, wrong-side, and parking counts will appear here." />
          )}
        </div>

        <div className="surface overflow-hidden">
          <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Camera Ranking</h2>
          </div>
          {data.by_camera?.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left dark:divide-slate-800">
                <thead className="bg-slate-50 dark:bg-slate-900">
                  <tr>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Camera</th>
                    <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Location</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {data.by_camera.map((camera) => (
                    <tr key={camera.camera_id || camera.camera_name}>
                      <td className="px-4 py-3 text-sm font-medium text-slate-950 dark:text-white">{camera.camera_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">{camera.location_name}</td>
                      <td className="px-4 py-3 text-right text-sm font-semibold text-slate-950 dark:text-white">
                        {formatNumber(camera.count)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-5">
              <EmptyState title="No camera ranking" message="Camera-level analytics require violations linked to cameras." />
            </div>
          )}
        </div>
      </section>
    </>
  );
}

