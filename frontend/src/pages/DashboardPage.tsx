import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Clock3 } from 'lucide-react'
import { dashboardApi } from '../lib/api/dashboard'
import { revisionDateRange, type RevisionRangeDays } from '../lib/dateRange'
import { formatDateTime } from '../lib/format'
import { queryKeys } from '../lib/queryKeys'
import { KpiGrid } from '../features/dashboard/KpiGrid'
import { RevisionActivityChart } from '../features/dashboard/RevisionActivityChart'
import { SourceMonitoring } from '../features/dashboard/SourceMonitoring'
import { TopTopics } from '../features/dashboard/TopTopics'
import { DomainTable } from '../features/dashboard/DomainTable'

export function DashboardPage() {
  const [range, setRange] = useState<RevisionRangeDays>(14)
  const dateRange = useMemo(() => revisionDateRange(range), [range])
  const summary = useQuery({
    queryKey: queryKeys.dashboard.summary,
    queryFn: ({ signal }) => dashboardApi.summary(signal),
  })
  const domains = useQuery({
    queryKey: queryKeys.dashboard.domains,
    queryFn: ({ signal }) => dashboardApi.domains(signal),
  })
  const activity = useQuery({
    queryKey: queryKeys.dashboard.revisionActivity(range, dateRange.start, dateRange.end),
    queryFn: ({ signal }) => dashboardApi.revisionActivity(dateRange.start, dateRange.end, signal),
  })

  return (
    <div className="space-y-5 lg:space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Live intelligence workspace</p>
          <div className="mt-2 font-display text-2xl font-semibold tracking-tight text-white sm:text-[28px]">Intelligence Overview</div>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">A grounded view of corpus scale, source coverage, and observed change—without synthetic metrics.</p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-500" aria-live="polite">
          <Clock3 size={13} aria-hidden="true" />
          {summary.isFetching && !summary.isPending
            ? 'Refreshing data…'
            : summary.data
              ? `Snapshot ${formatDateTime(summary.data.as_of)}`
              : 'Awaiting data snapshot'}
        </div>
      </div>

      <KpiGrid data={summary.data?.kpis} loading={summary.isPending} />
      {summary.isError && (
        <div className="rounded-xl border border-rose-400/15 bg-rose-400/[0.04] px-4 py-3 text-xs text-rose-200" role="alert">
          Summary metrics are unavailable: {summary.error.message}. Other dashboard widgets remain independent.
          <button className="focus-ring ml-2 underline underline-offset-2" onClick={() => void summary.refetch()} type="button">Retry</button>
        </div>
      )}

      <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.65fr)_minmax(340px,0.85fr)]">
        <RevisionActivityChart
          data={activity.data}
          loading={activity.isPending}
          error={activity.error}
          range={range}
          onRangeChange={setRange}
          onRetry={() => void activity.refetch()}
        />
        <SourceMonitoring
          data={summary.data?.kpis.freshness_status_counts}
          documentCount={summary.data?.kpis.document_count}
          loading={summary.isPending}
          error={summary.error}
          onRetry={() => void summary.refetch()}
        />
      </div>

      <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(300px,0.72fr)_minmax(0,1.68fr)]">
        <TopTopics
          data={summary.data?.top_topics}
          loading={summary.isPending}
          error={summary.error}
          onRetry={() => void summary.refetch()}
        />
        <DomainTable
          data={domains.data}
          loading={domains.isPending}
          error={domains.error}
          onRetry={() => void domains.refetch()}
        />
      </div>
    </div>
  )
}
