import { ExternalLink, FileSearch } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { AnswerCitation } from '../../types/assistant'

export function EvidencePanel({ citations }: { citations: AnswerCitation[] }) {
  if (!citations.length) return null
  return (
    <section className="mt-4 border-t border-white/[0.06] pt-4" aria-label="Supporting evidence">
      <div className="mb-2 flex items-center gap-2"><FileSearch size={13} className="text-teal-300" /><h3 className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Verified supporting evidence</h3></div>
      <div className="space-y-2">
        {citations.map((citation) => (
          <details key={citation.evidence_id} className="group rounded-xl border border-white/[0.06] bg-black/10 open:border-teal-300/15">
            <summary className="focus-ring flex cursor-pointer list-none items-center justify-between gap-3 rounded-xl px-3.5 py-3 text-xs text-slate-400 marker:hidden">
              <span className="flex min-w-0 items-center gap-2"><span className="rounded-md bg-teal-300/10 px-1.5 py-1 font-mono text-[9px] text-teal-300">{citation.evidence_id}</span><span className="truncate">{citation.title}</span></span>
              <span className="text-[9px] uppercase tracking-wider text-slate-600 group-open:text-teal-300">Inspect</span>
            </summary>
            <div className="border-t border-white/[0.05] px-3.5 pb-3.5 pt-3">
              <blockquote className="whitespace-pre-wrap break-words border-l-2 border-teal-300/25 pl-3 text-xs leading-5 text-slate-400">{citation.quote}</blockquote>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px]">
                <Link to={`/documents/${encodeURIComponent(citation.document_id)}`} className="focus-ring font-medium text-teal-300 hover:underline">Open document</Link>
                <a href={citation.source_url} target="_blank" rel="noreferrer" className="focus-ring inline-flex items-center gap-1 text-slate-500 hover:text-slate-300">Open source <ExternalLink size={10} /></a>
                <span className="font-mono text-slate-700" title={citation.chunk_id}>Chunk {citation.chunk_id.slice(0, 12)}{citation.chunk_id.length > 12 ? '…' : ''}</span>
              </div>
            </div>
          </details>
        ))}
      </div>
    </section>
  )
}
