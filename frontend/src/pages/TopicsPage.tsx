import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { KeywordExplorer } from '../features/topics/KeywordExplorer'
import { DomainTopicBreakdown } from '../features/topics/DomainTopicBreakdown'
import { TrendComparison } from '../features/topics/TrendComparison'
import { topicsApi } from '../lib/api/topics'
import { validateTopicWindows, type TopicDateWindows } from '../lib/dateRange'
import { queryKeys } from '../lib/queryKeys'

function dateOnly(date: Date) { return date.toISOString().slice(0, 10) }
function defaultWindows(now = new Date()): TopicDateWindows {
  const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1))
  const afterStart = new Date(end); afterStart.setUTCDate(afterStart.getUTCDate() - 7)
  const beforeStart = new Date(afterStart); beforeStart.setUTCDate(beforeStart.getUTCDate() - 7)
  return { beforeStart: dateOnly(beforeStart), beforeEnd: dateOnly(afterStart), afterStart: dateOnly(afterStart), afterEnd: dateOnly(end) }
}
const supportedLimit = (value: string | null) => [10, 20, 50, 100].includes(Number(value)) ? Number(value) : 20

export function TopicsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const defaults = useMemo(() => defaultWindows(), [])
  const ngrams = searchParams.get('ngrams') === '2' ? 2 : 1
  const limit = supportedLimit(searchParams.get('limit'))
  const sourceDomain = searchParams.get('domain') ?? ''
  const breakdownDomain = searchParams.get('breakdown') ?? ''
  const windows: TopicDateWindows = { beforeStart: searchParams.get('before_start') ?? defaults.beforeStart, beforeEnd: searchParams.get('before_end') ?? defaults.beforeEnd, afterStart: searchParams.get('after_start') ?? defaults.afterStart, afterEnd: searchParams.get('after_end') ?? defaults.afterEnd }
  const validated = validateTopicWindows(windows)
  const topicParams = { sourceDomain: sourceDomain || undefined, limit, ngrams } as const
  const terms = useQuery({ queryKey: queryKeys.topics.terms(topicParams), queryFn: ({ signal }) => topicsApi.topics(topicParams, signal) })
  const domains = useQuery({ queryKey: queryKeys.topics.domains({ ngrams, limit }), queryFn: ({ signal }) => topicsApi.domains(100, Math.min(limit, 100), ngrams, signal) })
  const trendParams = validated.value ? { ...topicParams, ...validated.value } : null
  const trends = useQuery({ queryKey: queryKeys.topics.trends(trendParams ?? windows), queryFn: ({ signal }) => topicsApi.trends(trendParams!, signal), enabled: Boolean(trendParams) })
  const setParam = (key: string, value?: string) => setSearchParams((current) => { const next = new URLSearchParams(current); if (value) next.set(key, value); else next.delete(key); return next }, { replace: true })
  const setWindows = (next: TopicDateWindows) => setSearchParams((current) => { const params = new URLSearchParams(current); params.set('before_start', next.beforeStart); params.set('before_end', next.beforeEnd); params.set('after_start', next.afterStart); params.set('after_end', next.afterEnd); return params }, { replace: true })

  return <div className="space-y-5"><header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Deterministic lexical analytics</p><h2 className="mt-2 font-display text-2xl font-semibold text-white">Topic Intelligence</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Explore keyword document frequency across indexed content and revisions. These are lexical terms, not semantic classifications or measures of public interest.</p></div><button type="button" onClick={() => void queryClient.invalidateQueries({ queryKey: queryKeys.topics.all })} className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-white/10 px-3 text-xs text-slate-300 hover:bg-white/[0.04]"><RefreshCw size={13} />Refresh topics</button></header>
    <section className="grid gap-3 sm:grid-cols-3"><div className="panel p-4"><p className="text-[10px] uppercase text-slate-500">Indexed documents</p><p className="mt-2 text-2xl font-semibold text-white">{terms.data?.document_count ?? '—'}</p></div><div className="panel p-4"><p className="text-[10px] uppercase text-slate-500">Returned ranked terms</p><p className="mt-2 text-2xl font-semibold text-white">{terms.data?.terms.length ?? '—'}</p></div><label className="panel p-4 text-[10px] uppercase text-slate-500">Source-domain filter<input aria-label="Topic source domain" value={sourceDomain} onChange={(e) => setParam('domain', e.target.value.trim())} placeholder="All current domains" className="focus-ring mt-2 h-9 w-full rounded-lg border border-white/10 bg-ink px-3 text-xs normal-case text-slate-300 placeholder:text-slate-600" /></label></section>
    <KeywordExplorer data={terms.data} loading={terms.isPending} error={terms.error} ngrams={ngrams} limit={limit} onNgrams={(value) => setParam('ngrams', String(value))} onLimit={(value) => setParam('limit', String(value))} onRetry={() => void terms.refetch()} />
    <div className="grid gap-5 xl:grid-cols-[.7fr_1.3fr]"><DomainTopicBreakdown data={domains.data} loading={domains.isPending} error={domains.error} selected={breakdownDomain} onSelect={(value) => setParam('breakdown', value)} onRetry={() => void domains.refetch()} /><TrendComparison data={trends.data} loading={trends.isPending && Boolean(trendParams)} error={trends.error} windows={windows} validationError={validated.error} onWindows={setWindows} onRetry={() => void trends.refetch()} /></div>
  </div>
}
