import { Check, Copy, ExternalLink, FileSearch, SearchX } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState, Skeleton } from '../../components/ui/States'
import { ApiError } from '../../lib/api/client'
import type { SearchHit, SearchMode, SearchResponse } from '../../types/search'

function activeScore(hit: SearchHit, mode: SearchMode): { label: string; value: number | null } {
  if (mode === 'keyword') return { label: 'BM25', value: hit.bm25_score }
  if (mode === 'semantic') return { label: 'Cosine', value: hit.semantic_score }
  return { label: 'RRF', value: hit.hybrid_score }
}

function ResultCard({ hit, mode }: { hit: SearchHit; mode: SearchMode }) {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle')
  const score = activeScore(hit, mode)
  const copyUrl = async () => {
    try { await navigator.clipboard.writeText(hit.source_url); setCopyStatus('copied') }
    catch { setCopyStatus('error') }
    window.setTimeout(() => setCopyStatus('idle'), 1500)
  }
  return (
    <article className="panel group overflow-hidden p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl border border-white/[0.07] bg-white/[0.025] font-mono text-xs text-teal-300">{hit.rank}</span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
            <div className="min-w-0"><Link to={`/documents/${encodeURIComponent(hit.document_id)}`} className="focus-ring line-clamp-2 font-display text-base font-semibold leading-6 text-slate-100 hover:text-teal-300">{hit.title}</Link><p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-slate-600"><span>{hit.source_domain}</span><span aria-hidden="true">·</span><span className="uppercase tracking-wider">{hit.document_type}</span><span aria-hidden="true">·</span><span>Chunk {hit.chunk_index + 1}</span></p></div>
            <span className="shrink-0 rounded-lg border border-white/[0.06] bg-black/10 px-2.5 py-1.5 font-mono text-[10px] text-slate-400">{score.value === null ? `Rank #${hit.rank}` : `${score.label} ${score.value.toFixed(4)}`}</span>
          </div>
          <p className="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-slate-400">{hit.text}</p>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.05] pt-3">
            <a href={hit.source_url} target="_blank" rel="noreferrer" className="focus-ring inline-flex min-w-0 items-center gap-1.5 text-[11px] text-slate-500 hover:text-teal-300"><span className="max-w-[260px] truncate sm:max-w-md">{hit.source_url}</span><ExternalLink size={11} className="shrink-0" /></a>
            <div className="flex items-center gap-2"><button type="button" onClick={() => void copyUrl()} className="focus-ring inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[10px] text-slate-500 hover:bg-white/[0.04] hover:text-slate-300">{copyStatus === 'copied' ? <Check size={12} className="text-teal-300" /> : <Copy size={12} />}{copyStatus === 'copied' ? 'Copied' : copyStatus === 'error' ? 'Copy failed' : 'Copy URL'}</button><Link to={`/documents/${encodeURIComponent(hit.document_id)}`} className="focus-ring rounded-lg border border-white/[0.07] px-2.5 py-1.5 text-[10px] font-medium text-slate-400 hover:bg-teal-300/[0.06] hover:text-teal-300">View document</Link></div>
          </div>
        </div>
      </div>
    </article>
  )
}

function SearchError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const apiError = error instanceof ApiError ? error : null
  const title = apiError?.status === 503 ? 'Search service unavailable' : apiError?.status === 422 ? 'Search request rejected' : apiError?.kind === 'invalid-response' ? 'Invalid search response' : 'Search failed'
  return <section className="panel"><div className="flex min-h-52 flex-col items-center justify-center px-6 py-9 text-center" role="alert"><span className="grid size-11 place-items-center rounded-xl bg-rose-400/10 text-rose-300"><SearchX size={20} /></span><h2 className="mt-3 text-sm font-semibold text-slate-200">{title}</h2><p className="mt-1 max-w-md text-xs leading-5 text-slate-500">{error.message}</p><button type="button" onClick={onRetry} className="focus-ring mt-4 rounded-lg border border-white/[0.08] px-3 py-2 text-xs text-slate-300 hover:bg-white/[0.04]">Retry search</button></div></section>
}

interface Props { submitted: boolean; data?: SearchResponse; loading: boolean; error: Error | null; onRetry: () => void }

export function SearchResults({ submitted, data, loading, error, onRetry }: Props) {
  if (!submitted) return <section className="panel"><EmptyState title="Search the intelligence corpus" description="Enter a query, choose a retrieval mode, and search indexed source chunks. Results are retrieval evidence, not verified facts." /></section>
  if (loading) return <section className="space-y-3" aria-label="Searching"><div className="flex items-center gap-2 px-1 text-xs text-slate-500"><span className="size-1.5 animate-pulse rounded-full bg-teal-300" />Retrieving indexed evidence…</div>{Array.from({ length: 4 }, (_, i) => <div className="panel p-6" key={i}><Skeleton className="h-5 w-2/5" /><Skeleton className="mt-4 h-16 w-full" /><Skeleton className="mt-4 h-4 w-3/5" /></div>)}</section>
  if (error) return <SearchError error={error} onRetry={onRetry} />
  if (!data?.results.length) return <section className="panel"><EmptyState title="No indexed matches" description="No chunks matched this query and filter combination. Try another retrieval mode or broaden the filters." /></section>
  return (
    <section aria-label="Search results">
      <div className="mb-3 flex flex-col justify-between gap-2 px-1 sm:flex-row sm:items-center"><p className="text-xs text-slate-500"><span className="font-medium text-slate-300">{data.count}</span> result{data.count === 1 ? '' : 's'} for “{data.query}”</p><p className="flex items-center gap-1.5 text-[10px] text-slate-600"><FileSearch size={12} />Scores are mode-specific ranking signals, not confidence.</p></div>
      <div className="space-y-3">{data.results.map((hit) => <ResultCard key={hit.chunk_id} hit={hit} mode={data.mode} />)}</div>
    </section>
  )
}
