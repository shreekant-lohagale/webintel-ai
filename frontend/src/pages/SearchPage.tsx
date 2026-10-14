import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { SearchControls } from '../features/search/SearchControls'
import { SearchResults } from '../features/search/SearchResults'
import { searchApi } from '../lib/api/search'
import { queryKeys } from '../lib/queryKeys'
import type { DocumentType } from '../types/documents'
import type { SearchMode, SearchRequest } from '../types/search'

const validModes: SearchMode[] = ['keyword', 'semantic', 'hybrid']
const validLimits = [5, 10, 20, 50]

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const queryClient = useQueryClient()
  const submittedQuery = (params.get('q') ?? '').trim()
  const mode = (validModes.includes(params.get('mode') as SearchMode) ? params.get('mode') : 'hybrid') as SearchMode
  const parsedLimit = Number(params.get('limit'))
  const limit = validLimits.includes(parsedLimit) ? parsedLimit : 10
  const documentType = (['article', 'quote'].includes(params.get('type') ?? '') ? params.get('type') : undefined) as DocumentType | undefined
  const sourceDomain = params.get('domain') ?? ''
  const [draft, setDraft] = useState(submittedQuery)
  const [validationError, setValidationError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => setDraft(submittedQuery), [submittedQuery])
  const update = (key: string, value?: string, replace = true) => setParams((current) => {
    const next = new URLSearchParams(current)
    if (value?.trim()) next.set(key, value.trim())
    else next.delete(key)
    return next
  }, { replace })

  const request = useMemo<SearchRequest>(() => ({
    query: submittedQuery,
    mode,
    limit,
    ...(documentType ? { document_type: documentType } : {}),
    ...(sourceDomain.trim() ? { source_domain: sourceDomain.trim() } : {}),
  }), [documentType, limit, mode, sourceDomain, submittedQuery])
  const results = useQuery({
    queryKey: queryKeys.search.results(request),
    queryFn: ({ signal }) => searchApi.search(request, signal),
    enabled: Boolean(submittedQuery),
    retry: 1,
  })

  const submit = () => {
    const query = draft.trim()
    if (!query) { setValidationError('Enter a search query before submitting.'); inputRef.current?.focus(); return }
    setValidationError(null)
    update('q', query, false)
  }
  const clearQuery = () => { setDraft(''); setValidationError(null); update('q', undefined); inputRef.current?.focus() }
  const reset = () => { setDraft(''); setValidationError(null); setParams({}, { replace: true }); inputRef.current?.focus() }
  const cancel = () => void queryClient.cancelQueries({ queryKey: queryKeys.search.results(request), exact: true })

  return (
    <div className="space-y-5">
      <section><p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Evidence retrieval</p><h2 className="mt-2 font-display text-2xl font-semibold tracking-tight text-white sm:text-[28px]">Intelligence Search</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Search indexed source chunks using lexical, semantic, or fused retrieval. Results identify relevant evidence—not verified claims.</p></section>
      <SearchControls
        draft={draft} mode={mode} limit={limit} documentType={documentType} sourceDomain={sourceDomain}
        validationError={validationError} searching={results.isFetching} inputRef={inputRef}
        onDraftChange={(value) => { setDraft(value); if (validationError) setValidationError(null) }}
        onSubmit={submit} onClearQuery={clearQuery} onModeChange={(value) => update('mode', value)}
        onLimitChange={(value) => update('limit', String(value))} onDocumentTypeChange={(value) => update('type', value)}
        onSourceDomainChange={(value) => update('domain', value)} onReset={reset} onCancel={cancel}
      />
      <SearchResults submitted={Boolean(submittedQuery)} data={results.data} loading={results.isPending && results.fetchStatus !== 'idle'} error={results.error} onRetry={() => void results.refetch()} />
    </div>
  )
}
