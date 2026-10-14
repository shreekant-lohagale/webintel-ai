import { useQuery } from '@tanstack/react-query'
import { Activity, BookOpen, Database, ShieldCheck } from 'lucide-react'
import { dashboardApi } from '../lib/api/dashboard'
import { queryKeys } from '../lib/queryKeys'

const configuredApiOrigin = (import.meta.env.VITE_API_BASE_URL ?? '').trim()

export function SettingsPage() {
  const health = useQuery({ queryKey: queryKeys.readiness, queryFn: ({ signal }) => dashboardApi.readiness(signal), retry: 1 })
  const diagnostics = [
    { label: 'API routing', value: configuredApiOrigin ? 'Configured public API origin' : 'Same-origin /api proxy', icon: Activity },
    { label: 'Frontend version', value: __APP_VERSION__, icon: BookOpen },
    { label: 'Build identifier', value: __BUILD_ID__, icon: Database },
    { label: 'Backend readiness', value: health.isPending ? 'Checking…' : health.isSuccess ? 'Ready' : 'Unavailable', icon: ShieldCheck },
  ]

  return <div className="space-y-5"><header><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Safe diagnostics</p><h2 className="mt-2 font-display text-2xl font-semibold text-white">Application status</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Connection diagnostics and methodology notes. Secrets, database connection strings, provider keys, and administrative controls are never exposed here.</p></header>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Application diagnostics">{diagnostics.map(({ label, value, icon: Icon }) => <article key={label} className="panel p-4"><div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-400"><Icon size={13} aria-hidden="true" />{label}</div><p className="mt-3 break-words text-sm font-medium text-slate-100" aria-live={label === 'Backend readiness' ? 'polite' : undefined}>{value}</p></article>)}</section>
    {health.isError && <div role="alert" className="rounded-xl border border-rose-300/15 bg-rose-300/[0.04] p-4 text-xs text-rose-100">The readiness endpoint is unavailable. Verify the same-origin reverse proxy and backend health before relying on other workspaces. <button type="button" onClick={() => void health.refetch()} className="focus-ring ml-2 underline">Retry</button></div>}
    <section className="panel p-5 sm:p-6"><h2 className="font-display text-base font-semibold text-slate-100">Data methodology</h2><div className="mt-4 grid gap-4 md:grid-cols-2"><div><h3 className="text-xs font-medium text-teal-200">Grounding and retrieval</h3><p className="mt-2 text-xs leading-5 text-slate-400">Search scores rank evidence; they are not confidence percentages. Assistant claims require backend-accepted evidence identifiers and verbatim quotations.</p></div><div><h3 className="text-xs font-medium text-teal-200">Topics and monitoring</h3><p className="mt-2 text-xs leading-5 text-slate-400">Keyword frequency is lexical, not semantic classification. Observation age and provenance coverage do not prove content freshness, source availability, crawl events, or full website coverage.</p></div></div></section>
    <section className="rounded-xl border border-amber-300/15 bg-amber-300/[0.035] p-4"><h2 className="text-xs font-medium text-amber-100">Production access requirement</h2><p className="mt-2 text-xs leading-5 text-slate-300">A public deployment must protect inference through server-side user authentication, durable distributed rate limiting, request budgets, and operational alerts. A browser-visible shared API key is not secure.</p></section>
  </div>
}
