import type { DocumentType } from './documents'

export type SearchMode = 'keyword' | 'semantic' | 'hybrid'

export interface SearchRequest {
  query: string
  mode: SearchMode
  limit: number
  document_type?: DocumentType
  source_domain?: string
}

export interface SourceCitation {
  document_id: string
  chunk_id: string
  source_url: string
  title: string
}

export interface SearchHit {
  rank: number
  chunk_id: string
  document_id: string
  title: string
  text: string
  source_url: string
  source_domain: string
  document_type: string
  chunk_index: number
  content_hash: string
  config_key: string
  semantic_score: number | null
  bm25_score: number | null
  hybrid_score: number | null
  citation: SourceCitation
}

export interface SearchResponse {
  query: string
  mode: SearchMode
  count: number
  results: SearchHit[]
}
