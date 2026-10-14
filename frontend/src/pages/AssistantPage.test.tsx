import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'
import { assistantApi } from '../lib/api/assistant'
import { ApiError } from '../lib/api/client'
import { abstainedFixture, answeredFixture, unsafeEvidence } from '../test/assistantFixtures'

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
const healthResponse = () => Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
const answeredClaim = answeredFixture.claims[0]!
const answeredCitation = answeredFixture.citations[0]!

function renderAssistant() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/assistant']}><App /></MemoryRouter></QueryClientProvider>)
}

function successfulFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  void init
  return String(input).includes('/health/') ? healthResponse() : Promise.resolve(response(answeredFixture))
}

async function ask(question = answeredFixture.question) {
  const input = screen.getByRole('textbox', { name: 'Question' })
  await userEvent.type(input, `${question}{enter}`)
}

describe('AssistantPage', () => {
  it('validates empty submissions without calling the ask endpoint', async () => {
    const fetchMock = vi.fn(successfulFetch)
    vi.stubGlobal('fetch', fetchMock)
    renderAssistant()
    await userEvent.click(screen.getByRole('button', { name: 'Send question' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Enter a question before sending')
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/api/v1/ask'))).toHaveLength(0)
  })

  it('submits exact retrieval controls and renders grounded citations as safe text', async () => {
    const fetchMock = vi.fn(successfulFetch)
    vi.stubGlobal('fetch', fetchMock)
    const { container } = renderAssistant()
    await userEvent.selectOptions(screen.getByLabelText('Assistant retrieval mode'), 'semantic')
    await userEvent.selectOptions(screen.getByLabelText('Evidence count'), '6')
    await userEvent.selectOptions(screen.getByLabelText('Assistant document type'), 'article')
    await userEvent.type(screen.getByLabelText('Assistant source domain'), 'example.com')
    await ask()

    expect(await screen.findByText(answeredClaim.text)).toBeInTheDocument()
    const askCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/api/v1/ask'))
    expect(askCall?.[1]).toMatchObject({ method: 'POST' })
    expect(JSON.parse(String(askCall?.[1]?.body))).toEqual({
      question: answeredFixture.question,
      mode: 'semantic',
      top_k: 6,
      document_type: 'article',
      source_domain: 'example.com',
    })
    expect(screen.getByText('[E1]')).toBeInTheDocument()
    await userEvent.click(screen.getByText('Inspect'))
    expect(screen.getByText(unsafeEvidence)).toBeInTheDocument()
    expect(container.querySelector('img')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open document' })).toHaveAttribute('href', `/documents/${answeredCitation.document_id}`)
    expect(screen.getByRole('link', { name: 'Open source' })).toHaveAttribute('href', answeredCitation.source_url)
  })

  it('renders backend abstention as an intentional outcome', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).includes('/health/') ? healthResponse() : Promise.resolve(response(abstainedFixture))))
    renderAssistant()
    await ask(abstainedFixture.question)
    expect(await screen.findByText(abstainedFixture.answer)).toBeInTheDocument()
    expect(screen.getByText(`Reason: ${abstainedFixture.abstention_reason}`)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Search the corpus' })).toHaveAttribute('href', expect.stringContaining('/search?q='))
  })

  it('distinguishes provider errors and retries the exact question', async () => {
    let askCount = 0
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      void init
      if (String(input).includes('/health/')) return healthResponse()
      askCount += 1
      return Promise.resolve(askCount === 1 ? response({ detail: 'LLM provider is unavailable' }, 503) : response(answeredFixture))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderAssistant()
    await ask()
    expect(await screen.findByText('Language-model provider unavailable')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Retry question' }))
    expect(await screen.findByText(answeredClaim.text)).toBeInTheDocument()
    const bodies = fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/api/v1/ask')).map(([, init]) => JSON.parse(String(init?.body)))
    expect(bodies).toHaveLength(2)
    expect(bodies[1]).toEqual(bodies[0])
  })

  it('shows a specific timeout error', async () => {
    vi.stubGlobal('fetch', vi.fn(successfulFetch))
    vi.spyOn(assistantApi, 'ask').mockRejectedValueOnce(new ApiError('The request timed out after 70 seconds.', 'timeout'))
    renderAssistant()
    await ask()
    expect(await screen.findByText('Generation timed out')).toBeInTheDocument()
  })

  it('cancels an in-flight generation and allows retry', async () => {
    let requestSignal: AbortSignal | undefined
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes('/health/')) return healthResponse()
      requestSignal = init?.signal ?? undefined
      return new Promise<Response>((_resolve, reject) => requestSignal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true }))
    }))
    renderAssistant()
    await ask()
    await waitFor(() => expect(requestSignal).toBeDefined())
    await userEvent.click(screen.getByRole('button', { name: 'Cancel generation' }))
    await waitFor(() => expect(requestSignal?.aborted).toBe(true))
    expect(await screen.findByText('Request cancelled')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })

  it('copies an answer and clears the in-memory conversation', async () => {
    vi.stubGlobal('fetch', vi.fn(successfulFetch))
    renderAssistant()
    await ask()
    expect(await screen.findByText(answeredClaim.text)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Copy answer' }))
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(answeredFixture.answer)
    expect(screen.getByRole('button', { name: 'Copied' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Clear conversation' }))
    expect(screen.getByText('Ask the indexed corpus')).toBeInTheDocument()
    expect(screen.queryByText(answeredClaim.text)).not.toBeInTheDocument()
  })

  it('preserves Shift+Enter as a newline', async () => {
    vi.stubGlobal('fetch', vi.fn(successfulFetch))
    renderAssistant()
    const input = screen.getByRole('textbox', { name: 'Question' })
    await userEvent.type(input, 'first line{shift>}{enter}{/shift}second line')
    expect(input).toHaveValue('first line\nsecond line')
  })

  it('sends multiple visible questions independently without chat history', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes('/health/')) return healthResponse()
      const request = JSON.parse(String(init?.body)) as { question: string }
      const dynamic = { ...answeredFixture, question: request.question, answer: `Answer for ${request.question}`, claims: [{ ...answeredClaim, text: `Answer for ${request.question}` }] }
      return Promise.resolve(response(dynamic))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderAssistant()
    await ask('First independent question?')
    expect(await screen.findByText('Answer for First independent question?')).toBeInTheDocument()
    await ask('Second independent question?')
    expect(await screen.findByText('Answer for Second independent question?')).toBeInTheDocument()

    const bodies = fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/api/v1/ask')).map(([, init]) => JSON.parse(String(init?.body)))
    expect(bodies.map((body) => body.question)).toEqual(['First independent question?', 'Second independent question?'])
    expect(bodies.every((body) => !('history' in body) && !('messages' in body))).toBe(true)
  })
})
