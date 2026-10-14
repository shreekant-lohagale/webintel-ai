import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'
import { documentFixture, documentListFixture } from '../test/documentFixtures'

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

function renderPage(entry = '/documents') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}><App /></MemoryRouter></QueryClientProvider>)
}

describe('DocumentsPage', () => {
  it('renders backend document rows and pagination', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).includes('/health/')
      ? Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
      : Promise.resolve(response(documentListFixture))))
    renderPage()
    expect(await screen.findAllByText(documentFixture.title)).not.toHaveLength(0)
    expect(screen.getByText('21')).toBeInTheDocument()
    expect(screen.getByText(/Page/)).toHaveTextContent('Page 1 of 2')
  })

  it('debounces search and sends supported filters to the backend', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => String(input).includes('/health/')
      ? Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
      : Promise.resolve(response(documentListFixture)))
    vi.stubGlobal('fetch', fetchMock)
    renderPage()
    fireEvent.change(screen.getByPlaceholderText('Search title or content…'), { target: { value: 'provenance' } })
    await userEvent.selectOptions(screen.getByLabelText('Document type'), 'article')
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => {
      const value = String(url)
      return value.includes('q=provenance') && value.includes('document_type=article')
    })).toBe(true), { timeout: 1500 })
  })

  it('updates server pagination from the next-page control', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => String(input).includes('/health/')
      ? Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
      : Promise.resolve(response(documentListFixture)))
    vi.stubGlobal('fetch', fetchMock)
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Next/ }))
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes('page=2'))).toBe(true))
    await userEvent.selectOptions(screen.getByLabelText('Rows per page'), '50')
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes('page_size=50'))).toBe(true))
  })

  it('offers retry after a list error', async () => {
    let failed = true
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      if (String(input).includes('/health/')) return Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))
      if (failed) { failed = false; return Promise.resolve(response({ detail: 'Database unavailable' }, 503)) }
      return Promise.resolve(response(documentListFixture))
    }))
    renderPage()
    expect(await screen.findByText('This widget could not load')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findAllByText(documentFixture.title)).not.toHaveLength(0)
  })
})
