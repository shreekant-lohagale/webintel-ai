import { useEffect, useMemo, useState } from 'react'
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query'
import { Database, RefreshCw } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { DocumentFilters } from '../features/documents/DocumentFilters'
import { DocumentListing } from '../features/documents/DocumentListing'
import { Pagination } from '../features/documents/Pagination'
import { documentsApi } from '../lib/api/documents'
import { formatInteger } from '../lib/format'
import { queryKeys } from '../lib/queryKeys'
import type { DocumentListParams, DocumentType } from '../types/documents'

function positivePage(value: string | null): number {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1
}

function supportedPageSize(value: string | null): number {
  const parsed = Number(value)
  return [10, 20, 50].includes(parsed) ? parsed : 20
}

export function DocumentsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const urlQuery = searchParams.get('q') ?? ''
  const [searchInput, setSearchInput] = useState(urlQuery)
  const documentType = (['article', 'quote'].includes(searchParams.get('type') ?? '')
    ? searchParams.get('type')
    : undefined) as DocumentType | undefined
  const sourceDomain = searchParams.get('domain') ?? ''
  const tag = searchParams.get('tag') ?? ''
  const page = positivePage(searchParams.get('page'))
  const pageSize = supportedPageSize(searchParams.get('size'))

  useEffect(() => setSearchInput(urlQuery), [urlQuery])
  useEffect(() => {
    if (searchInput.trim() === urlQuery) return
    const timer = window.setTimeout(() => {
      setSearchParams((current) => {
        const next = new URLSearchParams(current)
        const value = searchInput.trim()
        if (value) next.set('q', value)
        else next.delete('q')
        next.delete('page')
        return next
      }, { replace: true })
    }, 350)
    return () => window.clearTimeout(timer)
  }, [searchInput, setSearchParams, urlQuery])

  const updateParam = (key: string, value?: string) => {
    setSearchParams((current) => {
      const next = new URLSearchParams(current)
      if (value?.trim()) next.set(key, value.trim())
      else next.delete(key)
      if (key !== 'page') next.delete('page')
      return next
    })
  }
  const params = useMemo<DocumentListParams>(() => ({
    page,
    pageSize,
    documentType,
    sourceDomain: sourceDomain.trim() || undefined,
    tag: tag.trim() || undefined,
    query: urlQuery.trim() || undefined,
  }), [documentType, page, pageSize, sourceDomain, tag, urlQuery])
  const documents = useQuery({
    queryKey: queryKeys.documents.list(params),
    queryFn: ({ signal }) => documentsApi.list(params, signal),
    placeholderData: keepPreviousData,
  })
  const hasFilters = Boolean(searchInput || documentType || sourceDomain || tag)

  const reset = () => {
    setSearchInput('')
    setSearchParams({}, { replace: true })
  }

  return (
    <div className="space-y-5">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Indexed public web corpus</p>
          <div className="mt-2 flex items-end gap-3">
            <span className="font-display text-3xl font-semibold tracking-tight text-white">{documents.data ? formatInteger(documents.data.total) : '—'}</span>
            <span className="pb-1 text-xs text-slate-500">matching documents</span>
          </div>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Explore normalized documents, immutable revisions, and source provenance captured by WebIntel AI.</p>
        </div>
        <button
          type="button"
          onClick={() => void queryClient.invalidateQueries({ queryKey: queryKeys.documents.all })}
          disabled={documents.isFetching}
          className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-white/[0.08] px-3 text-xs font-medium text-slate-300 hover:bg-white/[0.04] disabled:cursor-wait disabled:opacity-50"
        >
          {documents.isFetching ? <RefreshCw className="animate-spin" size={14} /> : <Database size={14} />} Refresh corpus
        </button>
      </section>
      <DocumentFilters
        search={searchInput}
        documentType={documentType}
        sourceDomain={sourceDomain}
        tag={tag}
        onSearchChange={setSearchInput}
        onDocumentTypeChange={(value) => updateParam('type', value)}
        onSourceDomainChange={(value) => updateParam('domain', value)}
        onTagChange={(value) => updateParam('tag', value)}
        onReset={reset}
        hasFilters={hasFilters}
      />
      <DocumentListing data={documents.data} loading={documents.isPending} error={documents.error} onRetry={() => void documents.refetch()} />
      {documents.data && <Pagination data={documents.data} onPageChange={(value) => updateParam('page', String(value))} onPageSizeChange={(value) => updateParam('size', String(value))} />}
    </div>
  )
}
