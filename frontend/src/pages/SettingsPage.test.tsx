import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'

function renderSettings() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/settings']}><App /></MemoryRouter></QueryClientProvider>)
}

const response = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))

describe('SettingsPage', () => {
  it('shows useful diagnostics without exposing backend identifiers or secrets', async () => {
    vi.stubGlobal('fetch', vi.fn(() => response({ status: 'ready', database: 'private_database_name' })))
    const { container } = renderSettings()
    expect(await screen.findByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('Same-origin /api proxy')).toBeInTheDocument()
    expect(screen.queryByText('private_database_name')).not.toBeInTheDocument()
    expect(container).not.toHaveTextContent('private_database_name')
    expect(container.innerHTML).not.toContain('private_database_name')
    expect(screen.getByText(/browser-visible shared API key is not secure/i)).toBeInTheDocument()
  })

  it('supports retrying a failed readiness check', async () => {
    let failing = true
    vi.stubGlobal('fetch', vi.fn(() => failing ? response({ detail: 'Unavailable' }, 503) : response({ status: 'ready', database: 'test' })))
    renderSettings()
    expect(await screen.findByRole('alert', undefined, { timeout: 3_000 })).toHaveTextContent('readiness endpoint is unavailable')
    failing = false
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('Ready')).toBeInTheDocument()
  })
})
