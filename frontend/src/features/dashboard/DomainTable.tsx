import { ExternalLink } from 'lucide-react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { errorMessage } from '../../lib/error'
import { formatDateTime, formatInteger, formatPercentage } from '../../lib/format'
import type { DomainSummary } from '../../types/dashboard'

interface Props {
  data?: DomainSummary
  loading: boolean
  error: Error | null
  onRetry: () => void
}

function StatusDots({ counts }: { counts: DomainSummary['domains'][number]['status_counts'] }) {
  const statuses = [
    { key: 'recently_observed', color: 'bg-teal-400', label: 'recent' },
    { key: 'aging_observation', color: 'bg-amber-400', label: 'aging' },
    { key: 'stale_observation', color: 'bg-orange-500', label: 'stale' },
    { key: 'unknown', color: 'bg-slate-500', label: 'unknown' },
    { key: 'future_timestamp', color: 'bg-rose-400', label: 'future' },
  ] as const
  return (
    <div className="flex flex-wrap gap-2">
      {statuses.filter(({ key }) => counts[key] > 0).map(({ key, color, label }) => (
        <span key={key} className="flex items-center gap-1 text-[10px] text-slate-500" title={`${label}: ${counts[key]}`}>
          <i className={`size-1.5 rounded-full ${color}`} /> {counts[key]}
        </span>
      ))}
    </div>
  )
}

export function DomainTable({ data, loading, error, onRetry }: Props) {
  return (
    <Panel>
      <PanelHeader
        title="Domain intelligence"
        description="Coverage and observation health by source domain."
        action={data ? <span className="text-[11px] text-slate-500">{formatInteger(data.total_domains)} domains</span> : undefined}
      />
      {loading ? (
        <div className="space-y-3 p-6">{Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-14 w-full" />)}</div>
      ) : error ? (
        <ErrorState message={errorMessage(error)} onRetry={onRetry} />
      ) : !data?.domains.length ? (
        <EmptyState title="No domains found" description="Source domains will appear after documents have been ingested." />
      ) : (
        <>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[760px] text-left">
              <thead>
                <tr className="border-b border-white/[0.055] text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-600">
                  <th className="px-6 py-3.5">Source domain</th>
                  <th className="px-4 py-3.5">Documents</th>
                  <th className="px-4 py-3.5">Observed</th>
                  <th className="px-4 py-3.5">Coverage</th>
                  <th className="px-4 py-3.5">Freshness</th>
                  <th className="px-6 py-3.5">Last observed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.045]">
                {data.domains.map((domain) => (
                  <tr key={domain.source_domain} className="transition hover:bg-white/[0.018]">
                    <td className="px-6 py-4"><span className="flex items-center gap-2 text-xs font-medium text-slate-200">{domain.source_domain}<ExternalLink size={11} className="text-slate-600" /></span></td>
                    <td className="px-4 py-4 font-mono text-xs text-slate-400">{formatInteger(domain.document_count)}</td>
                    <td className="px-4 py-4 font-mono text-xs text-slate-400">{formatInteger(domain.observed_document_count)}</td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-14 overflow-hidden rounded-full bg-white/[0.05]"><div className="h-full rounded-full bg-teal-400" style={{ width: `${domain.coverage_ratio * 100}%` }} /></div>
                        <span className="font-mono text-[11px] text-slate-400">{formatPercentage(domain.coverage_ratio)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4"><StatusDots counts={domain.status_counts} /></td>
                    <td className="whitespace-nowrap px-6 py-4 text-[11px] text-slate-500">{formatDateTime(domain.latest_observed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="divide-y divide-white/[0.05] md:hidden">
            {data.domains.map((domain) => (
              <article key={domain.source_domain} className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div><h3 className="text-sm font-medium text-slate-200">{domain.source_domain}</h3><p className="mt-1 text-[11px] text-slate-600">{formatDateTime(domain.latest_observed_at)}</p></div>
                  <span className="font-mono text-xs text-teal-300">{formatPercentage(domain.coverage_ratio)}</span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs"><div><p className="text-slate-600">Documents</p><p className="mt-1 font-mono text-slate-300">{domain.document_count}</p></div><div><p className="text-slate-600">Observed</p><p className="mt-1 font-mono text-slate-300">{domain.observed_document_count}</p></div></div>
                <div className="mt-4"><StatusDots counts={domain.status_counts} /></div>
              </article>
            ))}
          </div>
        </>
      )}
    </Panel>
  )
}
