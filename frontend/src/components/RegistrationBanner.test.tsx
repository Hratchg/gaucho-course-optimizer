import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mswServer'
import { RegistrationBanner } from './RegistrationBanner'

const store = new Map<string, string>()
vi.stubGlobal('localStorage', {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => {
    store.set(key, value)
  },
  removeItem: (key: string) => {
    store.delete(key)
  },
})

function daysFromNow(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString()
}

function renderBanner() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <RegistrationBanner />
    </QueryClientProvider>
  )
}

function stubQuarter(nextCode: string) {
  server.use(
    http.get('http://localhost:8001/quarters/current', () =>
      HttpResponse.json({
        quarter_code: '20264',
        quarter_name: 'Fall 2026',
        next_quarter_code: nextCode,
        next_quarter_name: 'Winter 2027',
        pass1_begin: daysFromNow(3),
        pass2_begin: daysFromNow(10),
        pass3_begin: daysFromNow(17),
        first_day_of_classes: daysFromNow(40),
        last_day_of_classes: daysFromNow(120),
      })
    )
  )
}

describe('RegistrationBanner', () => {
  beforeEach(() => {
    store.clear()
  })

  it('shows the countdown when a pass is within a week', async () => {
    stubQuarter('20271')
    renderBanner()
    expect(await screen.findByRole('status', { name: /registration countdown/i })).toBeInTheDocument()
    expect(screen.getByText(/pass 1 opens in 3 days/i)).toBeInTheDocument()
  })

  it('re-shows after dismiss when the quarter code changes', async () => {
    stubQuarter('20271')
    const user = userEvent.setup()
    const { unmount } = renderBanner()
    expect(await screen.findByText(/pass 1 opens in 3 days/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /dismiss registration banner/i }))
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(localStorage.getItem('registration-banner-dismissed-20271')).toBe('1')
    unmount()

    stubQuarter('20272')
    renderBanner()
    expect(await screen.findByRole('status', { name: /registration countdown/i })).toBeInTheDocument()
  })
})
