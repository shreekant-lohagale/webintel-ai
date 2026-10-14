import { Info } from 'lucide-react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { formatInteger } from '../../lib/format'
import { errorMessage } from '../../lib/error'
import type { FreshnessCounts } from '../../types/dashboard'

const freshness = [
  { key: 'recently_observed', label: 'Recently observed', color: 'bg-teal-400', text: 'text-teal-300' },
  { key: 'aging_observation', label: 'Aging', color: 'bg-amber-400', text: 'text-amber-300' },
  { key: 'stale_observation', label: 'Stale', color: 'bg-orange-500', text: 'text-orange-300' },
  { key: 'unknown', label: 'Unknown / unobserved', color: 'bg-slate-500', text: 'text-slate-300' },
  { key: 'future_timestamp', label: 'Future timestamp', color: 'bg-rose-400', text: 'text-rose-300' },
] as const

interface Props {
  data?: FreshnessCounts
  documentCount?: number
  loading: boolean
  error: Error | null
  onRetry: () => void
}

export function SourceMonitoring({ data, documentCount = 0, loading, error, onRetry }: Props) {
  const total = data ? Object.values(data).reduce((sum, value) => sum + value, 0) : 0

  return (
    <Panel>
      <PanelHeader title="Source monitoring" description="Observation-age distribution across current documents." />
      {loading ? (
        <div className="space-y-5 p-6"><Skeleton className="h-3 w-full" /><Skeleton className="h-44 w-full" /></div>
      ) : error ? (
        <ErrorState message={errorMessage(error)} onRetry={onRetry} />
      ) : !data || documentCount === 0 ? (
        <EmptyState title="No monitoring data" description="Ingest documents to begin measuring provenance and observation coverage." />
      ) : (
        <div className="p-5 sm:p-6">
          <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-white/[0.04]" aria-label="Freshness status distribution">
            {freshness.map((item) => {
              const value = data[item.key]
              return value > 0 ? (
                <span
                  key={item.key}
                  className={item.color}
                  style={{ width: `${(value / Math.max(total, 1)) * 100}%` }}
                  title={`${item.label}: ${value}`}
                />
              ) : null
            })}
          </div>
          <div className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
            {freshness.map((item) => (
              <div key={item.key} className="flex items-center justify-between border-b border-white/[0.045] pb-3">
                <div className="flex items-center gap-2.5">
                  <span className={`size-2 rounded-full ${item.color}`} />
                  <span className="text-xs text-slate-400">{item.label}</span>
                </div>
                <span className={`font-mono text-xs font-semibold ${item.text}`}>{formatInteger(data[item.key])}</span>
              </div>
            ))}
          </div>
          <div className="mt-5 flex gap-2 rounded-xl border border-sky-300/10 bg-sky-300/[0.035] p-3 text-[11px] leading-5 text-slate-500">
            <Info className="mt-0.5 shrink-0 text-sky-300/70" size={14} aria-hidden="true" />
            Observation freshness measures when a source was last seen. It is not proof that the content is accurate or current.
          </div>
        </div>
      )}
    </Panel>
  )
}
