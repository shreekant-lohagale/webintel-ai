import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { DocumentListResponse } from '../../types/documents'

export function Pagination({ data, onPageChange, onPageSizeChange }: { data: DocumentListResponse; onPageChange: (page: number) => void; onPageSizeChange: (size: number) => void }) {
  return (
    <nav className="flex items-center justify-between gap-4" aria-label="Document pagination">
      <div className="flex items-center gap-3"><p className="text-[11px] text-slate-500">Page <span className="text-slate-300">{data.page}</span> of {Math.max(data.total_pages, 1)}</p><label className="flex items-center gap-2 text-[10px] text-slate-600">Rows<select aria-label="Rows per page" value={data.page_size} onChange={(event) => onPageSizeChange(Number(event.target.value))} className="focus-ring h-8 rounded-lg border border-white/[0.08] bg-[#0a111e] px-2 text-[10px] text-slate-400"><option value="10">10</option><option value="20">20</option><option value="50">50</option></select></label></div>
      <div className="flex gap-2">
        <button type="button" disabled={!data.has_previous} onClick={() => onPageChange(data.page - 1)} className="focus-ring inline-flex h-9 items-center gap-1 rounded-lg border border-white/[0.08] px-3 text-xs text-slate-400 hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-35"><ChevronLeft size={14} /> Previous</button>
        <button type="button" disabled={!data.has_next} onClick={() => onPageChange(data.page + 1)} className="focus-ring inline-flex h-9 items-center gap-1 rounded-lg border border-white/[0.08] px-3 text-xs text-slate-400 hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-35">Next <ChevronRight size={14} /></button>
      </div>
    </nav>
  )
}
