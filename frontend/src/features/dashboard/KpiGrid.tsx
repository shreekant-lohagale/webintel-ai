import { Activity, Eye, FileStack, History } from 'lucide-react'
import type { DashboardKpis } from '../../types/dashboard'
import { formatInteger, formatPercentage } from '../../lib/format'
import { Skeleton } from '../../components/ui/States'

const cards = [
  { key: 'document_count', label: 'Total documents', detail: 'Current bounded corpus', icon: FileStack },
  { key: 'revision_count', label: 'Total revisions', detail: 'Immutable snapshots', icon: History },
  { key: 'source_observation_count', label: 'Source observations', detail: 'Provenance records', icon: Activity },
] as const

export function KpiGrid({ data, loading }: { data?: DashboardKpis; loading: boolean }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ key, label, detail, icon: Icon }) => (
        <article className="panel group relative overflow-hidden p-5" key={key}>
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-teal-300/20 to-transparent opacity-0 transition group-hover:opacity-100" />
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">{label}</p>
              {loading ? (
                <Skeleton className="mt-3 h-8 w-24" />
              ) : (
                <p className="mt-2 font-display text-2xl font-semibold tracking-tight text-slate-50">
                  {data ? formatInteger(data[key]) : '—'}
                </p>
              )}
            </div>
            <span className="grid size-9 place-items-center rounded-xl bg-white/[0.04] text-slate-400 transition group-hover:bg-teal-300/10 group-hover:text-teal-300">
              <Icon size={18} strokeWidth={1.7} aria-hidden="true" />
            </span>
          </div>
          <p className="mt-3 text-[11px] text-slate-600">{detail}</p>
        </article>
      ))}
      <article className="panel group relative overflow-hidden p-5">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-teal-300/20 to-transparent opacity-0 transition group-hover:opacity-100" />
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">Observation coverage</p>
            {loading ? (
              <Skeleton className="mt-3 h-8 w-20" />
            ) : (
              <p className="mt-2 font-display text-2xl font-semibold tracking-tight text-slate-50">
                {data ? formatPercentage(data.coverage_ratio) : '—'}
              </p>
            )}
          </div>
          <span className="grid size-9 place-items-center rounded-xl bg-white/[0.04] text-slate-400 transition group-hover:bg-teal-300/10 group-hover:text-teal-300">
            <Eye size={18} strokeWidth={1.7} aria-hidden="true" />
          </span>
        </div>
        <p className="mt-3 text-[11px] text-slate-600">Documents with provenance</p>
      </article>
    </div>
  )
}
