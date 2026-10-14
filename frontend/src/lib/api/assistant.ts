import type { AnswerCitation, AnswerClaim, AskRequest, AskResponse } from '../../types/assistant'
import { apiRequest, invalidResponse } from './client'

type ObjectValue = Record<string, unknown>
const isObject = (value: unknown): value is ObjectValue => typeof value === 'object' && value !== null && !Array.isArray(value)
const isString = (value: unknown): value is string => typeof value === 'string'
const isNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const isNullableString = (value: unknown): value is string | null => value === null || isString(value)

function isHttpUrl(value: unknown): value is string {
  if (!isString(value)) return false
  try {
    const protocol = new URL(value).protocol
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}

function parseCitation(value: unknown): AnswerCitation {
  if (
    !isObject(value) ||
    !isString(value.evidence_id) ||
    !isString(value.document_id) ||
    !isString(value.chunk_id) ||
    !isString(value.title) ||
    !isHttpUrl(value.source_url) ||
    !isString(value.quote)
  ) invalidResponse('An answer citation does not match the expected API contract.')
  return value as unknown as AnswerCitation
}

function parseClaim(value: unknown): AnswerClaim {
  if (!isObject(value) || !isString(value.text) || !Array.isArray(value.citations) || value.citations.length === 0) {
    invalidResponse('An answer claim does not match the expected API contract.')
  }
  return { text: value.text, citations: value.citations.map(parseCitation) }
}

export function parseAskResponse(value: unknown): AskResponse {
  if (
    !isObject(value) ||
    !isString(value.question) ||
    (value.status !== 'answered' && value.status !== 'abstained') ||
    !isString(value.answer) ||
    !Array.isArray(value.claims) ||
    !Array.isArray(value.citations) ||
    !isNumber(value.retrieved_chunks) ||
    !isNullableString(value.model) ||
    !isNullableString(value.abstention_reason)
  ) invalidResponse('The assistant response does not match the expected API contract.')

  const claims = value.claims.map(parseClaim)
  const citations = value.citations.map(parseCitation)
  if (value.status === 'answered' && (claims.length === 0 || citations.length === 0 || value.abstention_reason !== null)) {
    invalidResponse('An answered response must contain verified claims and citations.')
  }
  if (value.status === 'abstained' && (claims.length > 0 || citations.length > 0 || !value.abstention_reason)) {
    invalidResponse('An abstained response must not contain claims or citations.')
  }
  return {
    question: value.question,
    status: value.status,
    answer: value.answer,
    claims,
    citations,
    retrieved_chunks: value.retrieved_chunks,
    model: value.model,
    abstention_reason: value.abstention_reason,
  }
}

export const assistantApi = {
  ask: async (request: AskRequest, signal?: AbortSignal, timeoutMs = 70_000) =>
    parseAskResponse(await apiRequest('/api/v1/ask', {
      method: 'POST',
      body: request,
      signal,
      timeoutMs,
    })),
}
