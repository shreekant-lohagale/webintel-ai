import { AlertTriangle, Bot, Check, Copy, RefreshCw, Search, StopCircle } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../../lib/api/client'
import type { AssistantTurn } from '../../types/assistant'
import { EvidencePanel } from './EvidencePanel'

function errorPresentation(error?: Error): { title: string; detail: string } {
  if (!error) return { title: 'Answer generation failed', detail: 'An unexpected error occurred.' }
  if (error instanceof ApiError) {
    if (error.kind === 'timeout') return { title: 'Generation timed out', detail: 'The retrieval or language-model request exceeded the response window.' }
    if (error.kind === 'invalid-response') return { title: 'Invalid assistant response', detail: error.message }
    if (error.status === 502) return { title: 'Provider returned invalid output', detail: error.message }
    if (error.status === 503 && /LLM provider/i.test(error.message)) return { title: 'Language-model provider unavailable', detail: error.message }
    if (error.status === 503) return { title: 'RAG service unavailable', detail: error.message }
    if (error.status === 422) return { title: 'Question rejected', detail: error.message }
  }
  return { title: 'Answer generation failed', detail: error.message }
}

export function AssistantMessage({ turn, onRetry }: { turn: AssistantTurn; onRetry: (turn: AssistantTurn) => void }) {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle')
  const copyAnswer = async () => {
    if (!turn.response) return
    try { await navigator.clipboard.writeText(turn.response.answer); setCopyStatus('copied') }
    catch { setCopyStatus('error') }
  }

  if (turn.state === 'pending') return (
    <div className="flex gap-3" aria-live="polite"><span className="grid size-8 shrink-0 place-items-center rounded-xl bg-teal-300/10 text-teal-300"><Bot size={15} /></span><div className="rounded-2xl rounded-tl-sm border border-white/[0.06] bg-panel/75 px-4 py-3"><div className="flex items-center gap-2 text-xs text-slate-400"><span className="flex gap-1"><i className="size-1.5 animate-pulse rounded-full bg-teal-300" /><i className="size-1.5 animate-pulse rounded-full bg-teal-300 [animation-delay:150ms]" /><i className="size-1.5 animate-pulse rounded-full bg-teal-300 [animation-delay:300ms]" /></span>Retrieving evidence and generating a grounded answer…</div><p className="mt-1.5 text-[10px] text-slate-600">Non-streaming request · prior messages are not sent</p></div></div>
  )
  if (turn.state === 'cancelled') return (
    <div className="ml-11 rounded-xl border border-amber-300/10 bg-amber-300/[0.035] p-4"><p className="flex items-center gap-2 text-xs font-medium text-amber-200"><StopCircle size={14} />Request cancelled</p><p className="mt-1 text-[11px] text-slate-500">No answer was generated for this question.</p><button type="button" onClick={() => onRetry(turn)} className="focus-ring mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium text-slate-300 hover:text-teal-300"><RefreshCw size={12} />Try again</button></div>
  )
  if (turn.state === 'error') {
    const presentation = errorPresentation(turn.error)
    return <div className="ml-11 rounded-xl border border-rose-300/10 bg-rose-300/[0.035] p-4" role="alert"><p className="flex items-center gap-2 text-xs font-medium text-rose-200"><AlertTriangle size={14} />{presentation.title}</p><p className="mt-1 text-[11px] leading-5 text-slate-500">{presentation.detail}</p><button type="button" onClick={() => onRetry(turn)} className="focus-ring mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium text-slate-300 hover:text-teal-300"><RefreshCw size={12} />Retry question</button></div>
  }
  if (!turn.response) return null
  if (turn.state === 'abstained') return (
    <div className="flex gap-3"><span className="grid size-8 shrink-0 place-items-center rounded-xl bg-amber-300/10 text-amber-300"><Bot size={15} /></span><article className="min-w-0 flex-1 rounded-2xl rounded-tl-sm border border-amber-300/10 bg-amber-300/[0.025] p-4 sm:p-5"><p className="text-sm leading-6 text-slate-300">{turn.response.answer}</p><div className="mt-3 rounded-xl border border-white/[0.05] bg-black/10 p-3"><p className="text-[11px] leading-5 text-slate-500">The indexed corpus did not provide enough accepted evidence. Refine the question, broaden retrieval settings, or inspect search results.</p><Link to={`/search?q=${encodeURIComponent(turn.request.question)}&mode=${turn.request.mode}`} className="focus-ring mt-2 inline-flex items-center gap-1.5 text-[11px] font-medium text-teal-300 hover:underline"><Search size={12} />Search the corpus</Link></div><p className="mt-3 font-mono text-[9px] text-slate-700">Reason: {turn.response.abstention_reason}</p></article></div>
  )
  return (
    <div className="flex gap-3"><span className="grid size-8 shrink-0 place-items-center rounded-xl bg-teal-300/10 text-teal-300"><Bot size={15} /></span><article className="min-w-0 flex-1 rounded-2xl rounded-tl-sm border border-white/[0.065] bg-panel/80 p-4 shadow-panel sm:p-5">
      <div className="space-y-4">{turn.response.claims.map((claim, index) => <p key={`${index}-${claim.text}`} className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-300">{claim.text}{' '}<span className="inline-flex flex-wrap gap-1">{claim.citations.map((citation) => <span key={citation.evidence_id} className="rounded bg-teal-300/10 px-1 py-0.5 align-middle font-mono text-[9px] text-teal-300">[{citation.evidence_id}]</span>)}</span></p>)}</div>
      <EvidencePanel citations={turn.response.citations} />
      <footer className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.05] pt-3"><p className="text-[9px] text-slate-600">{turn.response.retrieved_chunks} accepted evidence chunk{turn.response.retrieved_chunks === 1 ? '' : 's'}{turn.response.model ? ` · ${turn.response.model}` : ''}</p><button type="button" onClick={() => void copyAnswer()} className="focus-ring inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[10px] text-slate-500 hover:bg-white/[0.04] hover:text-slate-300">{copyStatus === 'copied' ? <Check size={12} className="text-teal-300" /> : <Copy size={12} />}{copyStatus === 'copied' ? 'Copied' : copyStatus === 'error' ? 'Copy failed' : 'Copy answer'}</button></footer>
    </article></div>
  )
}
