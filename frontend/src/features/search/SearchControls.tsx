import { RotateCcw, Search, Square, X } from 'lucide-react'
import type { RefObject } from 'react'
import { SearchModeSelector } from './SearchModeSelector'
import type { DocumentType } from '../../types/documents'
import type { SearchMode } from '../../types/search'

interface Props {
  draft: string
  mode: SearchMode
  limit: number
  documentType?: DocumentType
  sourceDomain: string
  validationError: string | null
  searching: boolean
  inputRef: RefObject<HTMLInputElement | null>
  onDraftChange: (value: string) => void
  onSubmit: () => void
  onClearQuery: () => void
  onModeChange: (mode: SearchMode) => void
  onLimitChange: (limit: number) => void
  onDocumentTypeChange: (type?: DocumentType) => void
  onSourceDomainChange: (domain: string) => void
  onReset: () => void
  onCancel: () => void
}

export function SearchControls(props: Props) {
  return (
    <section className="panel p-4 sm:p-6" aria-label="Search controls">
      <form onSubmit={(event) => { event.preventDefault(); props.onSubmit() }} noValidate>
        <div className={`flex items-center rounded-2xl border bg-black/20 p-1.5 transition ${props.validationError ? 'border-rose-400/40' : 'border-white/[0.09] focus-within:border-teal-300/35'}`}>
          <Search className="ml-3 shrink-0 text-slate-500" size={19} aria-hidden="true" />
          <input ref={props.inputRef} type="search" value={props.draft} onChange={(event) => props.onDraftChange(event.target.value)} maxLength={1000} aria-invalid={Boolean(props.validationError)} aria-describedby={props.validationError ? 'search-validation' : undefined} placeholder="Search indexed intelligence…" className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-600 sm:text-base" />
          {props.draft && <button type="button" onClick={props.onClearQuery} aria-label="Clear search query" className="focus-ring rounded-lg p-2 text-slate-500 hover:bg-white/5 hover:text-slate-300"><X size={16} /></button>}
          {props.searching ? <button type="button" onClick={props.onCancel} className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-rose-300/15 bg-rose-300/[0.05] px-4 text-xs font-medium text-rose-200"><Square size={12} fill="currentColor" />Cancel</button>
            : <button type="submit" className="focus-ring h-10 rounded-xl bg-teal-300 px-5 text-xs font-semibold text-slate-950 shadow-[0_8px_24px_-10px_rgba(45,212,191,.7)] hover:bg-teal-200">Search</button>}
        </div>
        {props.validationError && <p id="search-validation" role="alert" className="mt-2 text-xs text-rose-300">{props.validationError}</p>}
      </form>

      <div className="mt-6"><SearchModeSelector value={props.mode} onChange={props.onModeChange} /></div>

      <div className="mt-5 grid gap-3 border-t border-white/[0.05] pt-5 sm:grid-cols-2 lg:grid-cols-[160px_180px_minmax(220px,1fr)_auto]">
        <label><span className="mb-1.5 block text-[10px] font-medium uppercase tracking-wider text-slate-600">Result count</span><select aria-label="Result count" value={props.limit} onChange={(event) => props.onLimitChange(Number(event.target.value))} className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-[#0a111e] px-3 text-xs text-slate-300"><option value="5">5 results</option><option value="10">10 results</option><option value="20">20 results</option><option value="50">50 results</option></select></label>
        <label><span className="mb-1.5 block text-[10px] font-medium uppercase tracking-wider text-slate-600">Document type</span><select aria-label="Search document type" value={props.documentType ?? ''} onChange={(event) => props.onDocumentTypeChange((event.target.value || undefined) as DocumentType | undefined)} className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-[#0a111e] px-3 text-xs text-slate-300"><option value="">All types</option><option value="article">Articles</option><option value="quote">Quotes</option></select></label>
        <label><span className="mb-1.5 block text-[10px] font-medium uppercase tracking-wider text-slate-600">Exact source domain</span><input aria-label="Source domain" value={props.sourceDomain} onChange={(event) => props.onSourceDomainChange(event.target.value)} maxLength={253} placeholder="example.com" className="focus-ring h-10 w-full rounded-xl border border-white/[0.08] bg-black/15 px-3 text-xs text-slate-300 placeholder:text-slate-600" /></label>
        <button type="button" onClick={props.onReset} className="focus-ring mt-auto inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-white/[0.08] px-4 text-xs font-medium text-slate-500 hover:bg-white/[0.04] hover:text-slate-300"><RotateCcw size={13} />Reset all</button>
      </div>
    </section>
  )
}
