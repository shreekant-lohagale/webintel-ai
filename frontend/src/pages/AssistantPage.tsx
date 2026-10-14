import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { MessageSquarePlus, Trash2 } from 'lucide-react'
import { assistantApi } from '../lib/api/assistant'
import { ChatComposer } from '../features/assistant/ChatComposer'
import { MessageList } from '../features/assistant/MessageList'
import { SuggestedQuestions } from '../features/assistant/SuggestedQuestions'
import type { AskRequest, AskResponse, AssistantTurn } from '../types/assistant'
import type { DocumentType } from '../types/documents'
import type { SearchMode } from '../types/search'

interface MutationInput { turnId: string; request: AskRequest; signal: AbortSignal }

export function AssistantPage() {
  const [turns, setTurns] = useState<AssistantTurn[]>([])
  const [draft, setDraft] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)
  const [mode, setMode] = useState<SearchMode>('hybrid')
  const [topK, setTopK] = useState(4)
  const [documentType, setDocumentType] = useState<DocumentType | undefined>()
  const [sourceDomain, setSourceDomain] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const controllerRef = useRef<AbortController | null>(null)
  const idRef = useRef(0)

  const mutation = useMutation<AskResponse, Error, MutationInput>({
    mutationFn: ({ request, signal }) => assistantApi.ask(request, signal),
    onSuccess: (response, input) => setTurns((current) => current.map((turn) => turn.id === input.turnId ? { ...turn, state: response.status, response, error: undefined } : turn)),
    onError: (error, input) => setTurns((current) => current.map((turn) => turn.id === input.turnId ? { ...turn, state: error instanceof DOMException && error.name === 'AbortError' ? 'cancelled' : 'error', error } : turn)),
    onSettled: () => { controllerRef.current = null },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turns])

  const runRequest = (turnId: string, request: AskRequest) => {
    const controller = new AbortController()
    controllerRef.current = controller
    mutation.mutate({ turnId, request, signal: controller.signal })
  }
  const submit = () => {
    const question = draft.trim()
    if (!question) { setValidationError('Enter a question before sending.'); textareaRef.current?.focus(); return }
    const request: AskRequest = { question, mode, top_k: topK, ...(documentType ? { document_type: documentType } : {}), ...(sourceDomain.trim() ? { source_domain: sourceDomain.trim() } : {}) }
    const id = `turn-${Date.now()}-${++idRef.current}`
    setTurns((current) => [...current, { id, request, state: 'pending' }])
    setDraft(''); setValidationError(null)
    runRequest(id, request)
  }
  const retry = (turn: AssistantTurn) => {
    if (mutation.isPending) return
    setTurns((current) => current.map((item) => item.id === turn.id ? { ...item, state: 'pending', response: undefined, error: undefined } : item))
    runRequest(turn.id, turn.request)
  }
  const clear = (resetSettings: boolean) => {
    controllerRef.current?.abort(); mutation.reset(); setTurns([]); setValidationError(null)
    if (resetSettings) { setDraft(''); setMode('hybrid'); setTopK(4); setDocumentType(undefined); setSourceDomain('') }
    textareaRef.current?.focus()
  }

  return (
    <div className="-mx-4 -my-6 flex min-h-[calc(100vh-5rem)] flex-col sm:-mx-6 lg:-mx-8 lg:-my-8">
      <header className="border-b border-white/[0.06] px-4 py-4 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-4xl flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Grounded research workspace</p><div className="mt-1 font-display text-xl font-semibold text-white">Evidence-first answers</div><p className="mt-1 text-xs text-slate-400">Source-grounded answers with backend-verified quotations. Conversation history is visual only.</p></div><div className="flex gap-2"><button type="button" onClick={() => clear(false)} disabled={!turns.length} className="focus-ring inline-flex h-9 items-center gap-2 rounded-lg border border-white/[0.07] px-3 text-[10px] text-slate-400 hover:bg-white/[0.04] hover:text-slate-200 disabled:opacity-35"><Trash2 size={12} />Clear conversation</button><button type="button" onClick={() => clear(true)} className="focus-ring inline-flex h-9 items-center gap-2 rounded-lg border border-teal-300/15 bg-teal-300/[0.05] px-3 text-[10px] font-medium text-teal-300 hover:bg-teal-300/[0.09]"><MessageSquarePlus size={12} />New conversation</button></div></div>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto">{turns.length ? <MessageList turns={turns} onRetry={retry} /> : <SuggestedQuestions onSelect={(question) => { setDraft(question); setValidationError(null); textareaRef.current?.focus() }} />}<div ref={bottomRef} /></div>
      <ChatComposer value={draft} validationError={validationError} generating={mutation.isPending} mode={mode} topK={topK} documentType={documentType} sourceDomain={sourceDomain} textareaRef={textareaRef} onChange={(value) => { setDraft(value); if (validationError) setValidationError(null) }} onSubmit={submit} onCancel={() => controllerRef.current?.abort()} onModeChange={setMode} onTopKChange={setTopK} onDocumentTypeChange={setDocumentType} onSourceDomainChange={setSourceDomain} />
    </div>
  )
}
