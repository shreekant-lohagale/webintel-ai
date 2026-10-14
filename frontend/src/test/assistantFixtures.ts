import type { AskRequest, AskResponse } from '../types/assistant'

export const unsafeEvidence = '<img src=x onerror=alert(1)> Source text remains plain text.'

export const askRequestFixture: AskRequest = {
  question: 'What makes intelligence pipelines reliable?',
  mode: 'hybrid',
  top_k: 4,
}

export const answeredFixture: AskResponse = {
  question: askRequestFixture.question,
  status: 'answered',
  answer: 'Reliable pipelines validate evidence before publishing an answer.',
  claims: [
    {
      text: 'Reliable pipelines validate evidence before publishing an answer.',
      citations: [
        {
          evidence_id: 'E1',
          document_id: '11111111-1111-4111-8111-111111111111',
          chunk_id: 'chunk-1',
          title: 'Reliable Intelligence Pipelines',
          source_url: 'https://example.com/reliable-pipelines',
          quote: unsafeEvidence,
        },
      ],
    },
  ],
  citations: [
    {
      evidence_id: 'E1',
      document_id: '11111111-1111-4111-8111-111111111111',
      chunk_id: 'chunk-1',
      title: 'Reliable Intelligence Pipelines',
      source_url: 'https://example.com/reliable-pipelines',
      quote: unsafeEvidence,
    },
  ],
  retrieved_chunks: 1,
  model: 'test-grounded-model',
  abstention_reason: null,
}

export const abstainedFixture: AskResponse = {
  question: 'What is not covered?',
  status: 'abstained',
  answer: 'I could not answer from the available indexed evidence.',
  claims: [],
  citations: [],
  retrieved_chunks: 0,
  model: null,
  abstention_reason: 'insufficient_retrieval_evidence',
}
