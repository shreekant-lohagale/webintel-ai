import { Send, Square, SlidersHorizontal } from 'lucide-react'
import type { KeyboardEvent, RefObject } from 'react'
import type { DocumentType } from '../../types/documents'
import type { SearchMode } from '../../types/search'

interface Props {
  value: string
  validationError: string | null
  generating: boolean
  mode: SearchMode
  topK: number
  documentType?: DocumentType
  sourceDomain: string
  textareaRef: RefObject<HTMLTextAreaElement | null>
  onChange: (value: string) => void
  onSubmit: () => void
  onCancel: () => void
  onModeChange: (mode: SearchMode) => void
  onTopKChange: (topK: number) => void
  onDocumentTypeChange: (type?: DocumentType) => void
  onSourceDomainChange: (domain: string) => void
}

export function ChatComposer(props: Props) {
  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); props.onSubmit() }
  }
  return (
    <div className="border-t border-white/[0.06] bg-ink/90 px-3 py-3 backdrop-blur-xl sm:px-6 sm:py-4">
      <div className="mx-auto max-w-4xl">
        <div className="mb-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-[150px_120px_150px_minmax(180px,1fr)]">
          <label><span className="sr-only">Assistant retrieval mode</span><select aria-label="Assistant retrieval mode" value={props.mode} onChange={(event) => props.onModeChange(event.target.value as SearchMode)} disabled={props.generating} className="focus-ring h-8 w-full rounded-lg border border-white/[0.07] bg-[#0a111e] px-2 text-[10px] text-slate-400 disabled:opacity-50"><option value="hybrid">Hybrid retrieval</option><option value="semantic">Semantic retrieval</option><option value="keyword">Keyword retrieval</option></select></label>
          <label><span className="sr-only">Evidence count</span><select aria-label="Evidence count" value={props.topK} onChange={(event) => props.onTopKChange(Number(event.target.value))} disabled={props.generating} className="focus-ring h-8 w-full rounded-lg border border-white/[0.07] bg-[#0a111e] px-2 text-[10px] text-slate-400 disabled:opacity-50">{Array.from({ length: 8 }, (_, i) => i + 1).map((count) => <option key={count} value={count}>Top {count}</option>)}</select></label>
          <label><span className="sr-only">Assistant document type</span><select aria-label="Assistant document type" value={props.documentType ?? ''} onChange={(event) => props.onDocumentTypeChange((event.target.value || undefined) as DocumentType | undefined)} disabled={props.generating} className="focus-ring h-8 w-full rounded-lg border border-white/[0.07] bg-[#0a111e] px-2 text-[10px] text-slate-400 disabled:opacity-50"><option value="">All document types</option><option value="article">Articles</option><option value="quote">Quotes</option></select></label>
          <label className="relative"><span className="sr-only">Assistant source domain</span><SlidersHorizontal className="pointer-events-none absolute left-2.5 top-2 text-slate-600" size={11} /><input aria-label="Assistant source domain" value={props.sourceDomain} onChange={(event) => props.onSourceDomainChange(event.target.value)} disabled={props.generating} maxLength={253} placeholder="Exact source domain" className="focus-ring h-8 w-full rounded-lg border border-white/[0.07] bg-black/10 pl-7 pr-2 text-[10px] text-slate-400 placeholder:text-slate-700 disabled:opacity-50" /></label>
        </div>
        <form onSubmit={(event) => { event.preventDefault(); props.onSubmit() }} noValidate>
          <div className={`flex items-end gap-2 rounded-2xl border bg-[#0b1220] p-2 shadow-panel ${props.validationError ? 'border-rose-400/35' : 'border-white/[0.09] focus-within:border-teal-300/30'}`}>
            <textarea ref={props.textareaRef} value={props.value} onChange={(event) => props.onChange(event.target.value)} onKeyDown={onKeyDown} disabled={props.generating} rows={2} maxLength={1000} aria-label="Question" aria-invalid={Boolean(props.validationError)} aria-describedby={props.validationError ? 'assistant-validation' : 'assistant-hint'} placeholder="Ask a question about the indexed sources…" className="max-h-40 min-h-12 min-w-0 flex-1 resize-y bg-transparent px-2 py-2 text-sm leading-6 text-slate-200 outline-none placeholder:text-slate-600 disabled:opacity-60" />
            {props.generating ? <button type="button" onClick={props.onCancel} className="focus-ring grid size-10 shrink-0 place-items-center rounded-xl border border-rose-300/15 bg-rose-300/[0.06] text-rose-200" aria-label="Cancel generation"><Square size={13} fill="currentColor" /></button>
              : <button type="submit" className="focus-ring grid size-10 shrink-0 place-items-center rounded-xl bg-teal-300 text-slate-950 hover:bg-teal-200" aria-label="Send question"><Send size={16} /></button>}
          </div>
          {props.validationError ? <p id="assistant-validation" role="alert" className="mt-2 text-[11px] text-rose-300">{props.validationError}</p> : <p id="assistant-hint" className="mt-2 text-center text-[9px] text-slate-700">Enter to send · Shift+Enter for a new line · Each question is independent</p>}
        </form>
      </div>
    </div>
  )
}
