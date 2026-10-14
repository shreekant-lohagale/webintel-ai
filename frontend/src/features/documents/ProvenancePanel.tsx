import { ExternalLink, Info, Link2 } from 'lucide-react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { errorMessage } from '../../lib/error'
import { formatDateTime } from '../../lib/format'
import type { DocumentSourcesResponse } from '../../types/documents'

interface Props { data?: DocumentSourcesResponse; loading: boolean; error: Error | null; onRetry: () => void }

export function ProvenancePanel({ data, loading, error, onRetry }: Props) {
  return (
    <Panel>
      <PanelHeader title="Provenance inspector" description={data ? `${data.total} source observation record${data.total === 1 ? '' : 's'}.` : 'Source observations and extraction lineage.'} />
      {loading ? <div className="space-y-3 p-6"><Skeleton className="h-28 w-full" /><Skeleton className="h-28 w-full" /></div>
        : error ? <ErrorState message={errorMessage(error)} onRetry={onRetry} />
          : !data?.items.length ? <EmptyState title="No provenance records" description="This document has no associated source observation records." />
            : <div className="divide-y divide-white/[0.05]">{data.items.map((source) => (
              <article key={source.observation_id} className="p-5 sm:p-6">
                <div className="flex items-start gap-3"><span className="grid size-8 shrink-0 place-items-center rounded-lg bg-teal-300/[0.07] text-teal-300"><Link2 size={15} /></span><div className="min-w-0"><a href={source.source_url} target="_blank" rel="noreferrer" className="focus-ring inline-flex max-w-full items-start gap-1.5 break-all text-xs font-medium text-slate-300 hover:text-teal-300">{source.source_url}<ExternalLink size={11} className="mt-0.5 shrink-0" /></a><p className="mt-1 font-mono text-[9px] text-slate-600">{source.observation_id}</p></div></div>
                <dl className="mt-4 grid gap-3 text-[11px] sm:grid-cols-3"><div><dt className="text-slate-600">Extraction method</dt><dd className="mt-1 text-slate-300">{source.extraction_method}</dd></div><div><dt className="text-slate-600">First observed</dt><dd className="mt-1 text-slate-400">{formatDateTime(source.first_seen_at)}</dd></div><div><dt className="text-slate-600">Last observed</dt><dd className="mt-1 text-slate-400">{formatDateTime(source.last_seen_at)}</dd></div></dl>
              </article>
            ))}</div>}
      <div className="m-5 flex gap-2 rounded-xl border border-sky-300/10 bg-sky-300/[0.035] p-3 text-[11px] leading-5 text-slate-500 sm:m-6"><Info className="mt-0.5 shrink-0 text-sky-300/70" size={14} />Provenance records identify source and extraction lineage. Revisions preserve content versions. Observation timestamps describe when records were seen, not guaranteed crawl-event times or proof of freshness.</div>
    </Panel>
  )
}
