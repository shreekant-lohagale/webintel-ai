import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'
import { comparisonFixture, documentFixture, documentId, revisionsFixture, sourcesFixture, timelineFixture } from '../test/documentFixtures'

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

function successfulFetch(input: RequestInfo | URL): Promise<Response> {
  const url = String(input)
  if (url.includes('/health/')) return Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
  if (url.includes('/compare?')) return Promise.resolve(response(comparisonFixture))
  if (url.includes('/changes')) return Promise.resolve(response(timelineFixture))
  if (url.includes('/sources')) return Promise.resolve(response(sourcesFixture))
  if (url.includes('/revisions')) return Promise.resolve(response(revisionsFixture))
  return Promise.resolve(response(documentFixture))
}

function renderDetail(fetcher: typeof fetch = successfulFetch as typeof fetch) {
  vi.stubGlobal('fetch', vi.fn(fetcher))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[`/documents/${documentId}`]}><App /></MemoryRouter></QueryClientProvider>)
}

describe('DocumentDetailPage', () => {
  it('shows a loading state while document requests are pending', () => {
    renderDetail(((input: RequestInfo | URL) => String(input).includes('/health/')
      ? Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
      : new Promise<Response>(() => undefined)) as typeof fetch)
    expect(document.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('handles a missing document response', async () => {
    renderDetail((() => Promise.resolve(response({ detail: 'Document not found' }, 404))) as typeof fetch)
    expect(await screen.findByText('Document not found')).toBeInTheDocument()
    expect(screen.getByText('Return to Document Explorer')).toBeInTheDocument()
  })

  it('renders chronological revision history and backend change indicators', async () => {
    renderDetail()
    await userEvent.click(await screen.findByRole('tab', { name: /Revisions/ }))
    expect(await screen.findByText('2 immutable snapshots, displayed chronologically.')).toBeInTheDocument()
    expect(screen.getByText('Content changed')).toBeInTheDocument()
    expect(screen.getByText('Title changed')).toBeInTheDocument()
  })

  it('handles a single revision without requesting a comparison', async () => {
    const single = { ...revisionsFixture, total: 1, items: [revisionsFixture.items[0]!] }
    renderDetail(((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/revisions')) return Promise.resolve(response(single))
      return successfulFetch(input)
    }) as typeof fetch)
    await userEvent.click(await screen.findByRole('tab', { name: /Revisions/ }))
    expect(await screen.findByText('Comparison unavailable')).toBeInTheDocument()
  })

  it('renders backend-generated revision comparison excerpts', async () => {
    renderDetail()
    await userEvent.click(await screen.findByRole('tab', { name: /Revisions/ }))
    expect(await screen.findByText(comparisonFixture.change_summary)).toBeInTheDocument()
    expect(screen.getByText('Reliable public web')).toBeInTheDocument()
    expect(screen.getByText('Public web')).toBeInTheDocument()
  })

  it('renders provenance source, method, and observation timestamps', async () => {
    renderDetail()
    await userEvent.click(await screen.findByRole('tab', { name: /Provenance/ }))
    expect(await screen.findByText(documentFixture.source_url)).toBeInTheDocument()
    expect(screen.getByText('scrapy')).toBeInTheDocument()
    expect(screen.getByText('First observed')).toBeInTheDocument()
    expect(screen.getByText(/not guaranteed crawl-event times/)).toBeInTheDocument()
  })
})
