import '@testing-library/jest-dom/vitest'
import { configure } from '@testing-library/dom'

configure({ asyncUtilTimeout: 3_000 })

class ResizeObserverMock implements ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(window, 'ResizeObserver', { writable: true, value: ResizeObserverMock })
Object.defineProperty(Element.prototype, 'scrollIntoView', { writable: true, value: vi.fn() })
Object.defineProperty(navigator, 'clipboard', {
  configurable: true,
  value: { writeText: vi.fn().mockResolvedValue(undefined) },
})

afterEach(() => {
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})
