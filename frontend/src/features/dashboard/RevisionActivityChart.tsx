import { BarChart3 } from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { formatChartDate } from '../../lib/format'
import { errorMessage } from '../../lib/error'
import type { RevisionRangeDays } from '../../lib/dateRange'
import type { RevisionActivity } from '../../types/dashboard'

interface Props {
  data?: RevisionActivity
  loading: boolean
  error: Error | null
  range: RevisionRangeDays
  onRangeChange: (range: RevisionRangeDays) => void
  onRetry: () => void
}

const rangeOptions: RevisionRangeDays[] = [7, 14, 30]

export function RevisionActivityChart({ data, loading, error, range, onRangeChange, onRetry }: Props) {
  const selector = (
    <div className="inline-flex rounded-lg border border-white/[0.07] bg-black/10 p-1" aria-label="Revision date range">
      {rangeOptions.map((days) => (
        <button
          key={days}
          type="button"
          onClick={() => onRangeChange(days)}
          aria-pressed={range === days}
          className={`focus-ring rounded-md px-2.5 py-1.5 text-[11px] font-medium transition ${
            range === days ? 'bg-white/[0.09] text-slate-100 shadow-sm' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          {days}D
        </button>
      ))}
    </div>
  )

  return (
    <Panel className="min-w-0">
      <PanelHeader
        title="Revision activity"
        description="Daily revision snapshots and unique documents, grouped by UTC day."
        action={selector}
      />
      {loading ? (
        <div className="p-6"><Skeleton className="h-[280px] w-full" /></div>
      ) : error ? (
        <ErrorState message={errorMessage(error)} onRetry={onRetry} />
      ) : !data || data.series.length === 0 || data.total_revisions === 0 ? (
        <EmptyState title="No revision activity" description={`No revisions were observed during the selected ${range}-day UTC window.`} />
      ) : (
        <div className="px-2 pb-4 pt-5 sm:px-4">
          <div
            className="h-[280px] w-full"
            role="img"
            aria-label={`Revision activity over ${range} days. ${data.total_revisions} total revisions.`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.series} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="revisionFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1d2a3d" strokeDasharray="3 5" vertical={false} />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={formatChartDate}
                  minTickGap={24}
                />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip
                  labelFormatter={(label) => `${formatChartDate(String(label))} (UTC)`}
                  formatter={(value, name) => [
                    Number(value).toLocaleString(),
                    name === 'revision_count' ? 'Revisions' : 'Unique documents',
                  ]}
                  contentStyle={{
                    background: '#0b1220',
                    border: '1px solid #243247',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '12px',
                    boxShadow: '0 16px 40px rgba(0,0,0,.4)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="revision_count"
                  stroke="#2dd4bf"
                  strokeWidth={2}
                  fill="url(#revisionFill)"
                  activeDot={{ r: 4, fill: '#2dd4bf', stroke: '#071019', strokeWidth: 2 }}
                />
                <Area
                  type="monotone"
                  dataKey="unique_document_count"
                  stroke="#818cf8"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  fill="transparent"
                  activeDot={{ r: 3, fill: '#818cf8' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-white/[0.05] px-3 pt-3 text-[11px] text-slate-500">
            <div className="flex flex-wrap gap-4">
              <span className="flex items-center gap-2"><i className="size-2 rounded-full bg-teal-300" /> Revisions</span>
              <span className="flex items-center gap-2"><i className="size-2 rounded-full bg-indigo-400" /> Unique documents</span>
            </div>
            <span className="hidden items-center gap-1.5 sm:flex"><BarChart3 size={13} /> {data.total_revisions.toLocaleString()} total</span>
          </div>
        </div>
      )}
    </Panel>
  )
}
