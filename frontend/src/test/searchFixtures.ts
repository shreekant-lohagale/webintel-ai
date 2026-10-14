import type { SearchResponse } from '../types/search'
import { documentId } from './documentFixtures'

export const unsafeExcerpt = '<img src=x onerror=alert(1)> Indexed evidence remains plain text.'

export const searchFixture: SearchResponse = {
  query: 'intelligence pipelines',
  mode: 'hybrid',
  count: 1,
  results: [{
    rank: 1,
    chunk_id: 'chunk-a-0',
    document_id: documentId,
    title: 'Reliable Intelligence Pipelines',
    text: unsafeExcerpt,
    source_url: 'https://example.com/intelligence',
    source_domain: 'example.com',
    document_type: 'article',
    chunk_index: 0,
    content_hash: 'b'.repeat(64),
    config_key: 'model:test:120:25:384',
    semantic_score: 0.8123,
    bm25_score: 2.4512,
    hybrid_score: 0.0325,
    citation: {
      document_id: documentId,
      chunk_id: 'chunk-a-0',
      source_url: 'https://example.com/intelligence',
      title: 'Reliable Intelligence Pipelines',
    },
  }],
}
