const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim()
const baseUrl = configuredBaseUrl.replace(/\/$/, '')

export type ApiErrorKind = 'http' | 'network' | 'timeout' | 'invalid-response'

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status?: number
  readonly details?: unknown

  constructor(message: string, kind: ApiErrorKind, options?: { status?: number; details?: unknown }) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = options?.status
    this.details = options?.details
  }
}

function errorDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) return null
  const detail = payload.detail
  return typeof detail === 'string' ? detail : null
}

export async function apiRequest(
  path: string,
  options: { signal?: AbortSignal; timeoutMs?: number } = {},
): Promise<unknown> {
  const controller = new AbortController()
  const timeoutMs = options.timeoutMs ?? 10_000
  let timedOut = false
  const timeout = window.setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)
  const abortFromCaller = () => controller.abort()
  options.signal?.addEventListener('abort', abortFromCaller, { once: true })

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    let payload: unknown
    try {
      payload = await response.json()
    } catch {
      throw new ApiError('The server returned an unreadable response.', 'invalid-response', {
        status: response.status,
      })
    }

    if (!response.ok) {
      throw new ApiError(errorDetail(payload) ?? `Request failed with status ${response.status}.`, 'http', {
        status: response.status,
        details: payload,
      })
    }
    return payload
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      if (timedOut) throw new ApiError(`The request timed out after ${timeoutMs / 1000} seconds.`, 'timeout')
      throw error
    }
    throw new ApiError('Unable to reach the WebIntel API.', 'network', { details: error })
  } finally {
    window.clearTimeout(timeout)
    options.signal?.removeEventListener('abort', abortFromCaller)
  }
}

export function invalidResponse(message: string): never {
  throw new ApiError(message, 'invalid-response')
}
