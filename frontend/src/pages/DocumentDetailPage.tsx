import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, FileClock, FileText, Link2, RefreshCw } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/States'
import { DocumentOverview } from '../features/documents/DocumentOverview'
import { ProvenancePanel } from '../features/documents/ProvenancePanel'
import { RevisionComparisonPanel } from '../features/documents/RevisionComparisonPanel'
import { RevisionTimeline } from '../features/documents/RevisionTimeline'
import { documentsApi } from '../lib/api/documents'
import { ApiError } from '../lib/api/client'
import { queryKeys } from '../lib/queryKeys'

type Tab = 'document' | 'revisions' | 'provenance'

export function DocumentDetailPage() {
  const { documentId = '' } = useParams()
  const [tab, setTab] = useState<Tab>('document')
  const [fromRevision, setFromRevision] = useState('')
  const [toRevision, setToRevision] = useState('')
  const detail = useQuery({ queryKey: queryKeys.documents.detail(documentId), queryFn: ({ signal }) => documentsApi.detail(documentId, signal), retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 2 })
  const sources = useQuery({ queryKey: queryKeys.documents.sources(documentId), queryFn: ({ signal }) => documentsApi.sources(documentId, signal) })
  const revisions = useQuery({ queryKey: queryKeys.documents.revisions(documentId), queryFn: ({ signal }) => documentsApi.revisions(documentId, signal) })
  const timeline = useQuery({ queryKey: queryKeys.documents.timeline(documentId), queryFn: ({ signal }) => documentsApi.timeline(documentId, signal) })

  useEffect(() => {
    const items = revisions.data?.items
    if (!items || items.length < 2) return
    const ids = new Set(items.map((item) => item.revision_id))
    if (!ids.has(fromRevision) || !ids.has(toRevision)) {
      setFromRevision(items[1]!.revision_id)
      setToRevision(items[0]!.revision_id)
    }
  }, [fromRevision, revisions.data?.items, toRevision])

  const comparison = useQuery({
    queryKey: queryKeys.documents.comparison(documentId, fromRevision, toRevision),
    queryFn: ({ signal }) => documentsApi.compare(documentId, fromRevision, toRevision, signal),
    enabled: Boolean(fromRevision && toRevision && fromRevision !== toRevision),
  })

  const refresh = () => {
    void detail.refetch(); void sources.refetch(); void revisions.refetch(); void timeline.refetch()
    if (comparison.isEnabled) void comparison.refetch()
  }

  if (detail.isPending) return <div className="space-y-5"><Skeleton className="h-32 w-full" /><Skeleton className="h-96 w-full" /></div>
  if (detail.error instanceof ApiError && detail.error.status === 404) {
    return <section className="panel"><EmptyState title="Document not found" description="The requested document does not exist in the current corpus." /><div className="pb-8 text-center"><Link to="/documents" className="focus-ring text-xs font-medium text-teal-300 hover:underline">Return to Document Explorer</Link></div></section>
  }
  if (detail.error || !detail.data) return <section className="panel"><ErrorState message={detail.error?.message ?? 'Document details are unavailable.'} onRetry={() => void detail.refetch()} /></section>

  const tabs: { id: Tab; label: string; icon: typeof FileText; count?: number }[] = [
    { id: 'document', label: 'Document', icon: FileText },
    { id: 'revisions', label: 'Revisions', icon: FileClock, count: revisions.data?.total },
    { id: 'provenance', label: 'Provenance', icon: Link2, count: sources.data?.total },
  ]

  return (
    <div className="space-y-5">
      <section>
        <div className="flex items-center justify-between gap-4">
          <Link to="/documents" className="focus-ring inline-flex items-center gap-2 rounded-lg text-xs font-medium text-slate-500 hover:text-teal-300"><ArrowLeft size={14} />Document Explorer</Link>
          <button type="button" onClick={refresh} className="focus-ring inline-flex items-center gap-2 rounded-lg border border-white/[0.08] px-3 py-2 text-[11px] text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"><RefreshCw size={13} className={detail.isFetching ? 'animate-spin' : ''} />Refresh</button>
        </div>
        <div className="mt-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
          <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded-md border border-teal-300/15 bg-teal-300/[0.06] px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-teal-300">{detail.data.document_type}</span><span className="text-[11px] text-slate-500">{detail.data.source_domain}</span></div><h2 className="mt-3 max-w-4xl font-display text-2xl font-semibold leading-tight tracking-tight text-white sm:text-3xl">{detail.data.title}</h2></div>
          <div className="flex shrink-0 gap-3"><div className="rounded-xl border border-white/[0.06] bg-white/[0.025] px-4 py-3 text-center"><p className="font-mono text-lg text-slate-200">{revisions.data?.total ?? '—'}</p><p className="text-[9px] uppercase tracking-wider text-slate-600">Revisions</p></div><div className="rounded-xl border border-white/[0.06] bg-white/[0.025] px-4 py-3 text-center"><p className="font-mono text-lg text-slate-200">{sources.data?.total ?? '—'}</p><p className="text-[9px] uppercase tracking-wider text-slate-600">Sources</p></div></div>
        </div>
      </section>

      <div className="flex overflow-x-auto border-b border-white/[0.07]" role="tablist" aria-label="Document detail sections">
        {tabs.map(({ id, label, icon: Icon, count }) => <button key={id} type="button" role="tab" aria-selected={tab === id} onClick={() => setTab(id)} className={`focus-ring flex shrink-0 items-center gap-2 border-b-2 px-4 py-3 text-xs font-medium transition ${tab === id ? 'border-teal-300 text-teal-300' : 'border-transparent text-slate-500 hover:text-slate-300'}`}><Icon size={14} />{label}{count !== undefined && <span className="rounded-full bg-white/[0.06] px-1.5 py-0.5 font-mono text-[9px]">{count}</span>}</button>)}
      </div>

      {tab === 'document' && <DocumentOverview document={detail.data} />}
      {tab === 'revisions' && <div className="space-y-5"><RevisionTimeline revisions={revisions.data} timeline={timeline.data} loading={revisions.isPending || timeline.isPending} error={revisions.error ?? timeline.error} onRetry={() => { void revisions.refetch(); void timeline.refetch() }} /><RevisionComparisonPanel revisions={revisions.data} data={comparison.data} from={fromRevision} to={toRevision} onFromChange={setFromRevision} onToChange={setToRevision} loading={comparison.isPending && comparison.fetchStatus !== 'idle'} error={comparison.error} onRetry={() => void comparison.refetch()} /></div>}
      {tab === 'provenance' && <ProvenancePanel data={sources.data} loading={sources.isPending} error={sources.error} onRetry={() => void sources.refetch()} />}
    </div>
  )
}
