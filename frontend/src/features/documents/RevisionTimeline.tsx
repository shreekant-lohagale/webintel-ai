import { ArrowDown, FileClock, Minus, Plus } from 'lucide-react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { errorMessage } from '../../lib/error'
import { formatDateTime } from '../../lib/format'
import type { DocumentRevisionsResponse, DocumentTimeline } from '../../types/documents'

interface Props {
  revisions?: DocumentRevisionsResponse
  timeline?: DocumentTimeline
  loading: boolean
  error: Error | null
  onRetry: () => void
}

export function RevisionTimeline({ revisions, timeline, loading, error, onRetry }: Props) {
  if (loading) return <Panel><div className="space-y-4 p-6">{Array.from({ length: 3 }, (_, i) => <Skeleton className="h-24 w-full" key={i} />)}</div></Panel>
  if (error) return <Panel><ErrorState message={errorMessage(error)} onRetry={onRetry} /></Panel>
  if (!revisions?.items.length) return <Panel><EmptyState title="No revisions available" description="No immutable revision snapshots are associated with this document." /></Panel>
  const changeByRevision = new Map(timeline?.history.map((item) => [item.to_revision_id, item]) ?? [])
  const chronological = [...revisions.items].reverse()

  return (
    <Panel>
      <PanelHeader title="Revision history" description={`${revisions.total} immutable snapshot${revisions.total === 1 ? '' : 's'}, displayed chronologically.`} />
      <ol className="p-5 sm:p-6">
        {chronological.map((revision, index) => {
          const change = changeByRevision.get(revision.revision_id)
          return (
            <li key={revision.revision_id} className="relative grid grid-cols-[24px_minmax(0,1fr)] gap-3 pb-6 last:pb-0">
              {index < chronological.length - 1 && <span className="absolute bottom-0 left-[11px] top-6 w-px bg-white/[0.07]" />}
              <span className={`relative z-10 mt-0.5 grid size-6 place-items-center rounded-full border ${change?.content_changed ? 'border-teal-300/30 bg-teal-300/10 text-teal-300' : 'border-white/10 bg-[#111a29] text-slate-500'}`}><FileClock size={12} /></span>
              <article className="rounded-xl border border-white/[0.055] bg-black/10 p-4">
                <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                  <div><p className="text-xs font-medium text-slate-200">{revision.title}</p><p className="mt-1 font-mono text-[10px] text-slate-600" title={revision.revision_id}>{revision.revision_id}</p></div>
                  <time className="whitespace-nowrap text-[10px] text-slate-500">{formatDateTime(revision.observed_at)}</time>
                </div>
                {change ? (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-white/[0.05] pt-3 text-[10px]">
                    <span className={`rounded-md px-2 py-1 ${change.content_changed ? 'bg-teal-300/[0.07] text-teal-300' : 'bg-white/[0.04] text-slate-500'}`}>{change.content_changed ? 'Content changed' : 'Content unchanged'}</span>
                    {change.title_changed && <span className="rounded-md bg-indigo-300/[0.07] px-2 py-1 text-indigo-300">Title changed</span>}
                    <span className="flex items-center gap-1 text-emerald-300"><Plus size={11} />{change.added_words}</span>
                    <span className="flex items-center gap-1 text-rose-300"><Minus size={11} />{change.removed_words}</span>
                    <span className="text-slate-600">{Math.round(change.similarity_ratio * 100)}% similar</span>
                  </div>
                ) : (
                  <p className="mt-3 flex items-center gap-1.5 border-t border-white/[0.05] pt-3 text-[10px] text-slate-600"><ArrowDown size={11} />Baseline snapshot</p>
                )}
              </article>
            </li>
          )
        })}
      </ol>
    </Panel>
  )
}
