import {
  Activity,
  AlertTriangle,
  Clock3,
  FileSearch,
  ShieldCheck,
} from 'lucide-react';
import SafetyIndexPanel from '../components/analytics/SafetyIndexPanel.jsx';
import TrendLineChart from '../components/charts/TrendLineChart.jsx';
import ViolationTypeChart from '../components/charts/ViolationTypeChart.jsx';
import EmptyState from '../components/states/EmptyState.jsx';
import ErrorState from '../components/states/ErrorState.jsx';
import LoadingState from '../components/states/LoadingState.jsx';
import MetricCard from '../components/ui/MetricCard.jsx';
import PageHeader from '../components/ui/PageHeader.jsx';
import ViolationTable from '../components/violations/ViolationTable.jsx';
import useAsyncData from '../hooks/useAsyncData.js';
import { getAnalytics, getViolations } from '../services/api.js';
import { formatNumber } from '../utils/formatters.js';

export default function Dashboard() {
  const { data, error, loading, reload } = useAsyncData(async () => {
    const [analytics, violations] = await Promise.all([
      getAnalytics(30),
      getViolations({ limit: 6, offset: 0 }),
    ]);
    return { analytics, violations };
  }, []);

  if (loading) {
    return <LoadingState label="Loading command dashboard" />;
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  const analytics = data.analytics;
  const recentViolations = data.violations?.items || [];
  const total = analytics?.total_violations || 0;
  const criticalAlerts = getCriticalAlertCount(analytics?.by_type || []);
  const peakWindow = analytics?.peak_hours || 'N/A';
  const safetyIndex = analytics?.safety_index?.score ?? 100;

  return (
    <>
      <PageHeader
        eyebrow="Operations Overview"
        title="Traffic Enforcement Dashboard"
        description="Live enforcement overview for AI-detected helmet, triple riding, wrong-side driving, and illegal parking events."
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          title="Total violations"
          value={formatNumber(total)}
          detail="Detected in the last 30 days"
          icon={FileSearch}
          tone="default"
        />
        <MetricCard
          title="Vehicles analyzed"
          value={formatNumber(total)}
          detail="Derived from processed events"
          icon={Activity}
          tone="success"
        />
        <MetricCard
          title="Critical alerts"
          value={formatNumber(criticalAlerts)}
          detail="Wrong-side and triple riding"
          icon={AlertTriangle}
          tone="danger"
        />
        <MetricCard
          title="Peak hours"
          value={peakWindow}
          detail="Based on available trend data"
          icon={Clock3}
          tone="warning"
        />
        <MetricCard
          title="Safety Index"
          value={`${safetyIndex}/100`}
          detail="Higher score means lower risk"
          icon={ShieldCheck}
          tone={safetyIndex >= 75 ? 'success' : safetyIndex >= 50 ? 'warning' : 'danger'}
        />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <div className="surface p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Violation Trend</h2>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">30 days</span>
          </div>
          {analytics.trend?.length ? (
            <div className="h-72">
              <TrendLineChart data={analytics.trend} />
            </div>
          ) : (
            <EmptyState title="No trend data" message="Daily violation counts will appear after uploads are processed." />
          )}
        </div>

        <div className="surface p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Violation Mix</h2>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">By type</span>
          </div>
          {analytics.by_type?.length ? (
            <div className="h-72">
              <ViolationTypeChart data={analytics.by_type} />
            </div>
          ) : (
            <EmptyState title="No violation mix" message="Type-level breakdown appears after detections are stored." />
          )}
        </div>
      </section>

      <section className="mt-5">
        <SafetyIndexPanel safetyIndex={analytics.safety_index} />
      </section>

      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-slate-950 dark:text-white">Recent Evidence</h2>
          <span className="text-sm text-slate-500 dark:text-slate-400">{formatNumber(data.violations?.total)} records</span>
        </div>
        {recentViolations.length ? (
          <ViolationTable violations={recentViolations} compact />
        ) : (
          <EmptyState title="No recent violations" message="Uploaded camera evidence will populate this review queue." />
        )}
      </section>
    </>
  );
}

function getCriticalAlertCount(byType) {
  return byType
    .filter((item) => ['wrong_side_driving', 'triple_riding'].includes(item.violation_type))
    .reduce((total, item) => total + item.count, 0);
}

