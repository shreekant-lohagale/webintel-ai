import { ArrowRight, Equal, Minus, Plus } from 'lucide-react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { errorMessage } from '../../lib/error'
import { formatDateTime } from '../../lib/format'
import type { DocumentRevisionsResponse, RevisionComparison } from '../../types/documents'

interface Props {
  revisions?: DocumentRevisionsResponse
  data?: RevisionComparison
  from: string
  to: string
  onFromChange: (value: string) => void
  onToChange: (value: string) => void
  loading: boolean
  error: Error | null
  onRetry: () => void
}

const shortRevision = (id: string) => `${id.slice(0, 10)}…`

export function RevisionComparisonPanel({ revisions, data, from, to, onFromChange, onToChange, loading, error, onRetry }: Props) {
  if (!revisions || revisions.total < 2) return <Panel><PanelHeader title="Revision comparison" description="Backend-generated word-level change analysis." /><EmptyState title="Comparison unavailable" description="At least two immutable revisions are required to compare changes." /></Panel>
  const selector = (
    <div className="grid w-full gap-2 sm:grid-cols-[1fr_auto_1fr] sm:items-center lg:w-auto">
      <label><span className="sr-only">Before revision</span><select aria-label="Before revision" value={from} onChange={(event) => onFromChange(event.target.value)} className="focus-ring h-9 w-full rounded-lg border border-white/[0.08] bg-[#0a111e] px-2 text-[10px] text-slate-300">{revisions.items.map((revision) => <option key={revision.revision_id} value={revision.revision_id}>{formatDateTime(revision.observed_at)} · {shortRevision(revision.revision_id)}</option>)}</select></label>
      <ArrowRight className="hidden text-slate-600 sm:block" size={14} />
      <label><span className="sr-only">After revision</span><select aria-label="After revision" value={to} onChange={(event) => onToChange(event.target.value)} className="focus-ring h-9 w-full rounded-lg border border-white/[0.08] bg-[#0a111e] px-2 text-[10px] text-slate-300">{revisions.items.map((revision) => <option key={revision.revision_id} value={revision.revision_id}>{formatDateTime(revision.observed_at)} · {shortRevision(revision.revision_id)}</option>)}</select></label>
    </div>
  )
  return (
    <Panel>
      <PanelHeader title="Revision comparison" description="Select two stored revisions; differences are computed by the backend." action={selector} />
      {from === to ? <EmptyState title="Select two distinct revisions" description="The before and after revisions must be different." />
        : loading ? <div className="space-y-4 p-6"><Skeleton className="h-20 w-full" /><Skeleton className="h-28 w-full" /></div>
          : error ? <ErrorState message={errorMessage(error)} onRetry={onRetry} />
            : data ? <div className="p-5 sm:p-6">
              <div className="grid gap-3 sm:grid-cols-4">
                <div className="rounded-xl bg-white/[0.025] p-3"><p className="text-[10px] text-slate-600">Similarity</p><p className="mt-1 font-mono text-lg text-slate-200">{Math.round(data.similarity_ratio * 100)}%</p></div>
                <div className="rounded-xl bg-emerald-300/[0.04] p-3"><p className="text-[10px] text-slate-600">Words added</p><p className="mt-1 flex items-center gap-1 font-mono text-lg text-emerald-300"><Plus size={14} />{data.added_words}</p></div>
                <div className="rounded-xl bg-rose-300/[0.04] p-3"><p className="text-[10px] text-slate-600">Words removed</p><p className="mt-1 flex items-center gap-1 font-mono text-lg text-rose-300"><Minus size={14} />{data.removed_words}</p></div>
                <div className="rounded-xl bg-white/[0.025] p-3"><p className="text-[10px] text-slate-600">Title</p><p className="mt-2 text-xs text-slate-300">{data.title_changed ? 'Changed' : 'Unchanged'}</p></div>
              </div>
              <p className="mt-4 text-xs leading-5 text-slate-400">{data.change_summary}</p>
              {!data.content_changed ? <div className="mt-5 flex items-center gap-2 rounded-xl border border-teal-300/10 bg-teal-300/[0.035] p-4 text-xs text-teal-200"><Equal size={16} />No content hash change between these revisions.</div>
                : <div className="mt-5 space-y-3">{data.changes.map((change, index) => <article key={`${change.kind}-${index}`} className="grid gap-3 rounded-xl border border-white/[0.055] bg-black/10 p-4 lg:grid-cols-2"><div><p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-rose-300">Deleted · {change.removed_words} words</p><p className="whitespace-pre-wrap break-words text-xs leading-5 text-rose-100/75">{change.before_excerpt || '—'}</p></div><div><p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-emerald-300">Inserted · {change.added_words} words</p><p className="whitespace-pre-wrap break-words text-xs leading-5 text-emerald-100/75">{change.after_excerpt || '—'}</p></div></article>)}{data.changes_truncated && <p className="text-[10px] text-amber-300">Additional changes were truncated by the backend response.</p>}</div>}
            </div> : null}
    </Panel>
  )
}
