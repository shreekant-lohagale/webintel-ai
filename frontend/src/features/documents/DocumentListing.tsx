import { ArrowRight, CalendarDays, FileText, Globe2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { errorMessage } from '../../lib/error'
import { formatDateTime } from '../../lib/format'
import type { DocumentListResponse } from '../../types/documents'

interface Props {
  data?: DocumentListResponse
  loading: boolean
  error: Error | null
  onRetry: () => void
}

const shortId = (value: string) => `${value.slice(0, 8)}…${value.slice(-6)}`

function TypeBadge({ type }: { type: 'article' | 'quote' }) {
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${
      type === 'article'
        ? 'border-teal-300/15 bg-teal-300/[0.06] text-teal-300'
        : 'border-indigo-300/15 bg-indigo-300/[0.06] text-indigo-300'
    }`}>
      {type}
    </span>
  )
}

export function DocumentListing({ data, loading, error, onRetry }: Props) {
  if (loading) {
    return <section className="panel space-y-3 p-5" aria-label="Loading documents">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-16 w-full" />)}</section>
  }
  if (error) return <section className="panel"><ErrorState message={errorMessage(error)} onRetry={onRetry} /></section>
  if (!data?.items.length) {
    return <section className="panel"><EmptyState title="No documents found" description="No indexed documents match the current server-side filters. Try resetting or broadening the query." /></section>
  }

  return (
    <section className="panel overflow-hidden" aria-label="Documents">
      <div className="hidden overflow-x-auto lg:block">
        <table className="w-full min-w-[900px] text-left">
          <thead>
            <tr className="border-b border-white/[0.055] text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-600">
              <th className="px-6 py-3.5">Document</th>
              <th className="px-4 py-3.5">Type</th>
              <th className="px-4 py-3.5">Source</th>
              <th className="px-4 py-3.5">Published</th>
              <th className="px-4 py-3.5">Scraped</th>
              <th className="px-6 py-3.5"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.045]">
            {data.items.map((document) => (
              <tr key={document.document_id} className="group transition hover:bg-white/[0.02]">
                <td className="max-w-md px-6 py-4">
                  <Link to={`/documents/${document.document_id}`} className="focus-ring line-clamp-1 text-sm font-medium text-slate-200 hover:text-teal-300">{document.title}</Link>
                  <p className="mt-1 font-mono text-[10px] text-slate-600" title={document.document_id}>{shortId(document.document_id)}</p>
                </td>
                <td className="px-4 py-4"><TypeBadge type={document.document_type} /></td>
                <td className="px-4 py-4"><span className="flex items-center gap-2 text-xs text-slate-400"><Globe2 size={13} className="text-slate-600" />{document.source_domain}</span></td>
                <td className="whitespace-nowrap px-4 py-4 text-[11px] text-slate-500">{formatDateTime(document.published_at)}</td>
                <td className="whitespace-nowrap px-4 py-4 text-[11px] text-slate-500">{formatDateTime(document.scraped_at)}</td>
                <td className="px-6 py-4 text-right"><Link to={`/documents/${document.document_id}`} aria-label={`View ${document.title}`} className="focus-ring inline-flex rounded-lg p-2 text-slate-500 hover:bg-teal-300/10 hover:text-teal-300"><ArrowRight size={16} /></Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="divide-y divide-white/[0.05] lg:hidden">
        {data.items.map((document) => (
          <article key={document.document_id} className="p-5">
            <div className="flex items-start justify-between gap-3"><TypeBadge type={document.document_type} /><Link to={`/documents/${document.document_id}`} aria-label={`View ${document.title}`} className="focus-ring rounded-lg p-1.5 text-slate-500 hover:text-teal-300"><ArrowRight size={16} /></Link></div>
            <h3 className="mt-3 text-sm font-medium leading-5 text-slate-200">{document.title}</h3>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-slate-500">
              <span className="flex items-center gap-1.5"><Globe2 size={12} />{document.source_domain}</span>
              <span className="flex items-center gap-1.5"><CalendarDays size={12} />{formatDateTime(document.scraped_at)}</span>
              <span className="flex items-center gap-1.5 font-mono"><FileText size={12} />{shortId(document.document_id)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
