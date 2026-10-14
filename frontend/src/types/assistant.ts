import type { DocumentType } from './documents'
import type { SearchMode } from './search'

export interface AskRequest {
  question: string
  mode: SearchMode
  top_k: number
  document_type?: DocumentType
  source_domain?: string
}

export interface AnswerCitation {
  evidence_id: string
  document_id: string
  chunk_id: string
  title: string
  source_url: string
  quote: string
}

export interface AnswerClaim {
  text: string
  citations: AnswerCitation[]
}

export interface AskResponse {
  question: string
  status: 'answered' | 'abstained'
  answer: string
  claims: AnswerClaim[]
  citations: AnswerCitation[]
  retrieved_chunks: number
  model: string | null
  abstention_reason: string | null
}

export type AssistantTurnState = 'pending' | 'answered' | 'abstained' | 'error' | 'cancelled'

export interface AssistantTurn {
  id: string
  request: AskRequest
  state: AssistantTurnState
  response?: AskResponse
  error?: Error
}
