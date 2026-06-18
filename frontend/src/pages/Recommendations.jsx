import { RefreshCcw, ShieldAlert, ShieldCheck } from 'lucide-react';
import EmptyState from '../components/states/EmptyState.jsx';
import ErrorState from '../components/states/ErrorState.jsx';
import LoadingState from '../components/states/LoadingState.jsx';
import Button from '../components/ui/Button.jsx';
import PageHeader from '../components/ui/PageHeader.jsx';
import useAsyncData from '../hooks/useAsyncData.js';
import { getRecommendations } from '../services/api.js';
import { cn } from '../utils/cn.js';
import { formatNumber, formatViolationType } from '../utils/formatters.js';

const priorityClass = {
  high: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200',
  medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
  low: 'bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-200',
};

export default function Recommendations() {
  const { data, error, loading, reload } = useAsyncData(() => getRecommendations({ days: 30 }), []);

  if (loading) {
    return <LoadingState label="Loading recommendations" />;
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  const recommendations = data?.recommendations || [];

  return (
    <>
      <PageHeader
        eyebrow="Decision Support"
        title="AI Recommendations"
        description="Prioritized operational actions generated from recurring violation patterns and review backlogs."
        actions={
          <Button icon={RefreshCcw} variant="secondary" onClick={reload}>
            Refresh
          </Button>
        }
      />

      <section className="surface mb-5 p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">Recommendation Basis</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Generated from {formatNumber(data?.generated_from_violations)} violation records with a safety index of{' '}
              {data?.safety_index ?? 100}/100.
            </p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center bg-slate-100 text-civic-authority dark:bg-slate-900 dark:text-teal-300">
            <ShieldCheck size={22} />
          </div>
        </div>
      </section>

      {recommendations.length ? (
        <section className="grid gap-4 lg:grid-cols-2">
          {recommendations.map((recommendation) => (
            <article key={recommendation.id} className="surface p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center bg-slate-100 text-civic-authority dark:bg-slate-900 dark:text-teal-300">
                    <ShieldAlert size={19} />
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-base font-semibold text-slate-950 dark:text-white">
                      {recommendation.title}
                    </h2>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                      {recommendation.description}
                    </p>
                  </div>
                </div>
                <span
                  className={cn(
                    'inline-flex min-h-7 shrink-0 items-center px-2.5 text-xs font-semibold capitalize',
                    priorityClass[recommendation.priority],
                  )}
                >
                  {recommendation.priority}
                </span>
              </div>
              <div className="mt-5 grid gap-3 border-t border-slate-200 pt-4 text-sm dark:border-slate-800 sm:grid-cols-2">
                <Meta label="Location" value={recommendation.location_name || 'Network-wide'} />
                <Meta label="Violation" value={formatViolationType(recommendation.violation_type)} />
                <Meta label="Camera" value={recommendation.camera_name || 'All cameras'} />
                <Meta label="Impact" value={recommendation.estimated_impact} />
                <Meta label="Severity" value={formatNumber(recommendation.severity_score)} />
                <Meta label="Action" value={recommendation.action || 'Review enforcement posture'} />
              </div>
            </article>
          ))}
        </section>
      ) : (
        <EmptyState
          title="No recommendations"
          message="Recommendations appear when recurring violation patterns cross configured thresholds."
        />
      )}
    </>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
      <div className="mt-1 font-medium text-slate-950 dark:text-white">{value}</div>
    </div>
  );
}

