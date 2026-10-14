import { RotateCcw, Search, SlidersHorizontal } from 'lucide-react'
import type { DocumentType } from '../../types/documents'

interface Props {
  search: string
  documentType?: DocumentType
  sourceDomain: string
  tag: string
  onSearchChange: (value: string) => void
  onDocumentTypeChange: (value?: DocumentType) => void
  onSourceDomainChange: (value: string) => void
  onTagChange: (value: string) => void
  onReset: () => void
  hasFilters: boolean
}

export function DocumentFilters({
  search,
  documentType,
  sourceDomain,
  tag,
  onSearchChange,
  onDocumentTypeChange,
  onSourceDomainChange,
  onTagChange,
  onReset,
  hasFilters,
}: Props) {
  return (
    <section className="panel p-4 sm:p-5" aria-label="Document filters">
      <div className="grid gap-3 xl:grid-cols-[minmax(280px,1fr)_180px_220px_180px_auto]">
        <label className="relative block">
          <span className="sr-only">Search documents</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
          <input
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search title or content…"
            maxLength={200}
            className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-black/15 pl-10 pr-3 text-sm text-slate-200 placeholder:text-slate-600"
          />
        </label>
        <label>
          <span className="sr-only">Document type</span>
          <select
            value={documentType ?? ''}
            onChange={(event) => onDocumentTypeChange((event.target.value || undefined) as DocumentType | undefined)}
            className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-[#0a111e] px-3 text-xs text-slate-300"
          >
            <option value="">All document types</option>
            <option value="article">Articles</option>
            <option value="quote">Quotes</option>
          </select>
        </label>
        <label>
          <span className="sr-only">Source domain</span>
          <input
            value={sourceDomain}
            onChange={(event) => onSourceDomainChange(event.target.value)}
            placeholder="Source domain"
            maxLength={253}
            className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-black/15 px-3 text-xs text-slate-300 placeholder:text-slate-600"
          />
        </label>
        <label>
          <span className="sr-only">Tag</span>
          <input
            value={tag}
            onChange={(event) => onTagChange(event.target.value)}
            placeholder="Exact tag"
            maxLength={100}
            className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-black/15 px-3 text-xs text-slate-300 placeholder:text-slate-600"
          />
        </label>
        <button
          type="button"
          onClick={onReset}
          disabled={!hasFilters}
          className="focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-white/[0.08] px-4 text-xs font-medium text-slate-400 hover:bg-white/[0.04] hover:text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw size={14} aria-hidden="true" /> Reset
        </button>
      </div>
      <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-600">
        <SlidersHorizontal size={12} aria-hidden="true" /> Search covers title and content. Results use the API’s fixed newest-scraped ordering.
      </div>
    </section>
  )
}
