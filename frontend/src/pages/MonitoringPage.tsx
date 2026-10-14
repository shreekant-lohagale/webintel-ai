import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { MonitoringOverview } from '../features/monitoring/MonitoringOverview'
import { MonitoringDocumentsTable } from '../features/monitoring/MonitoringDocumentsTable'
import { DomainCoverage } from '../features/monitoring/DomainCoverage'
import { monitoringApi } from '../lib/api/monitoring'
import { queryKeys } from '../lib/queryKeys'
import type { FreshnessStatus, MonitoringControls } from '../types/monitoring'

const statuses: FreshnessStatus[] = ['recently_observed', 'aging_observation', 'stale_observation', 'future_timestamp', 'unknown']
const intIn = (value: string | null, fallback: number, min: number, max: number) => { const n = Number(value); return Number.isInteger(n) && n >= min && n <= max ? n : fallback }
const utcInputNow = () => new Date().toISOString().slice(0, 16)

export function MonitoringPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const initialAsOf = useMemo(utcInputNow, [])
  const domain = searchParams.get('domain') ?? ''
  const statusValue = searchParams.get('status')
  const status = statuses.includes(statusValue as FreshnessStatus) ? statusValue as FreshnessStatus : undefined
  const freshHours = intIn(searchParams.get('fresh'), 24, 1, 87599)
  const staleHours = intIn(searchParams.get('stale'), 168, 2, 87600)
  const limit = intIn(searchParams.get('limit'), 20, 1, 100)
  const requestedAsOf = searchParams.get('as_of')
  const asOfInput = requestedAsOf && !Number.isNaN(new Date(`${requestedAsOf}:00.000Z`).getTime()) ? requestedAsOf : initialAsOf
  const asOf = new Date(`${asOfInput}:00.000Z`).toISOString()
  const validationError = freshHours >= staleHours ? 'Fresh threshold must be lower than the stale threshold.' : null
  const controls: MonitoringControls = { sourceDomain: domain || undefined, status, asOf, freshHours, staleHours, limit }
  const enabled = !validationError
  const overview = useQuery({ queryKey: queryKeys.monitoring.overview(controls), queryFn: ({ signal }) => monitoringApi.overview(controls, signal), enabled })
  const documents = useQuery({ queryKey: queryKeys.monitoring.documents(controls), queryFn: ({ signal }) => monitoringApi.documents(controls, signal), enabled })
  const domains = useQuery({ queryKey: queryKeys.monitoring.domains({ asOf, freshHours, staleHours }), queryFn: ({ signal }) => monitoringApi.domains(controls, signal), enabled })
  const setParam = (key: string, value?: string) => setSearchParams((current) => { const next = new URLSearchParams(current); if (value) next.set(key, value); else next.delete(key); return next }, { replace: true })
  const refresh = () => void queryClient.invalidateQueries({ queryKey: queryKeys.monitoring.all })

  return <div className="space-y-5"><header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Provenance observation workspace</p><h2 className="mt-2 font-display text-2xl font-semibold text-white">Source Monitoring</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Inspect recorded observation age and provenance coverage. This does not verify content freshness, source availability, or complete website coverage.</p></div><button type="button" onClick={refresh} disabled={!enabled} className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-white/10 px-3 text-xs text-slate-300 hover:bg-white/[0.04] disabled:opacity-50"><RefreshCw size={13} />Refresh snapshot</button></header>
    <section className="panel grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-6"><label className="text-[10px] text-slate-500 xl:col-span-2">Source domain<input aria-label="Monitoring source domain" value={domain} onChange={(e) => setParam('domain', e.target.value.trim())} placeholder="All domains" className="focus-ring mt-1 block h-9 w-full rounded-lg border border-white/10 bg-ink px-3 text-xs text-slate-300" /></label><label className="text-[10px] text-slate-500">Freshness category<select aria-label="Freshness category" value={status ?? ''} onChange={(e) => setParam('status', e.target.value)} className="focus-ring mt-1 block h-9 w-full rounded-lg border border-white/10 bg-ink px-2 text-xs text-slate-300"><option value="">All categories</option>{statuses.map((item) => <option key={item} value={item}>{item.replaceAll('_', ' ')}</option>)}</select></label><label className="text-[10px] text-slate-500">Fresh through hours<input aria-label="Fresh hours" type="number" min="1" max="87599" value={freshHours} onChange={(e) => setParam('fresh', e.target.value)} className="focus-ring mt-1 block h-9 w-full rounded-lg border border-white/10 bg-ink px-2 text-xs text-slate-300" /></label><label className="text-[10px] text-slate-500">Stale after hours<input aria-label="Stale hours" type="number" min="2" max="87600" value={staleHours} onChange={(e) => setParam('stale', e.target.value)} className="focus-ring mt-1 block h-9 w-full rounded-lg border border-white/10 bg-ink px-2 text-xs text-slate-300" /></label><label className="text-[10px] text-slate-500">Result limit<select aria-label="Monitoring result limit" value={limit} onChange={(e) => setParam('limit', e.target.value)} className="focus-ring mt-1 block h-9 w-full rounded-lg border border-white/10 bg-ink px-2 text-xs text-slate-300">{[10, 20, 50, 100].map((n) => <option key={n}>{n}</option>)}</select></label><label className="text-[10px] text-slate-500 sm:col-span-2 xl:col-span-3">Fixed evaluation time (UTC)<input aria-label="Fixed evaluation time UTC" type="datetime-local" value={asOfInput} onChange={(e) => setParam('as_of', e.target.value)} className="focus-ring mt-1 block h-9 w-full rounded-lg border border-white/10 bg-ink px-2 text-xs text-slate-300" /></label><p className="self-end pb-2 text-[10px] leading-4 text-slate-500 sm:col-span-2 xl:col-span-3">All widgets share this exact <code>as_of</code> timestamp for reproducible classifications. Thresholds require 1 ≤ fresh &lt; stale ≤ 87,600 hours.</p></section>
    {validationError && <p role="alert" className="rounded-xl border border-rose-400/15 bg-rose-400/[0.04] p-3 text-xs text-rose-200">{validationError}</p>}
    {enabled && <><MonitoringOverview data={overview.data} loading={overview.isPending} error={overview.error} onRetry={() => void overview.refetch()} />
    <MonitoringDocumentsTable data={documents.data} loading={documents.isPending} error={documents.error} onRetry={() => void documents.refetch()} />
    <DomainCoverage data={domains.data} loading={domains.isPending} error={domains.error} onRetry={() => void domains.refetch()} /></>}
  </div>
}
