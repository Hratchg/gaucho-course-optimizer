import { useEffect, useMemo, useState } from 'react'
import { X, ExternalLink, CalendarClock } from 'lucide-react'
import { useQuarterInfo } from '@/hooks/useQuarterInfo'

const GOLD_URL = 'https://my.sa.ucsb.edu/gold/'
const DISMISS_KEY_PREFIX = 'registration-banner-dismissed-'
const SHOW_WITHIN_DAYS = 7

function dismissKey(quarterCode: string): string {
  return `${DISMISS_KEY_PREFIX}${quarterCode}`
}

function getDaysUntil(dateStr: string): number {
  const target = new Date(dateStr)
  const now = new Date()
  const diffMs = target.getTime() - now.getTime()
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24))
}

interface PassInfo {
  label: string
  daysUntil: number
}

export function RegistrationBanner() {
  const { data: quarterInfo, isLoading } = useQuarterInfo()

  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (!quarterInfo?.next_quarter_code) return
    try {
      setDismissed(localStorage.getItem(dismissKey(quarterInfo.next_quarter_code)) === '1')
    } catch {
      setDismissed(false)
    }
  }, [quarterInfo?.next_quarter_code])

  const nextPass = useMemo<PassInfo | null>(() => {
    if (!quarterInfo) return null

    const passes = [
      { label: 'Pass 1', date: quarterInfo.pass1_begin },
      { label: 'Pass 2', date: quarterInfo.pass2_begin },
      { label: 'Pass 3', date: quarterInfo.pass3_begin },
    ]

    let closest: PassInfo | null = null

    for (const p of passes) {
      if (!p.date) continue
      const days = getDaysUntil(p.date)
      if (days >= 0 && days <= SHOW_WITHIN_DAYS) {
        if (!closest || days < closest.daysUntil) {
          closest = { label: p.label, daysUntil: days }
        }
      }
    }

    return closest
  }, [quarterInfo])

  function handleDismiss() {
    setDismissed(true)
    const code = quarterInfo?.next_quarter_code
    if (!code) return
    try {
      localStorage.setItem(dismissKey(code), '1')
    } catch {
      // localStorage may be unavailable
    }
  }

  if (isLoading || dismissed || !quarterInfo || !nextPass) return null

  const countdownText =
    nextPass.daysUntil === 0
      ? `${nextPass.label} opens today!`
      : nextPass.daysUntil === 1
        ? `${nextPass.label} opens tomorrow!`
        : `${nextPass.label} opens in ${nextPass.daysUntil} days`

  return (
    <div
      className="border-b border-primary/20 bg-primary/5 px-4 py-2.5"
      role="status"
      aria-label="Registration countdown"
    >
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm">
          <CalendarClock className="h-4 w-4 text-primary shrink-0" aria-hidden="true" />
          <span className="text-foreground">
            <strong className="text-primary">{countdownText}</strong>
            {quarterInfo.next_quarter_name && (
              <span className="text-muted-foreground"> for {quarterInfo.next_quarter_name}</span>
            )}
          </span>
          <a
            href={GOLD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="focusable inline-flex items-center gap-1 rounded-sm text-primary font-medium hover:text-primary/80 transition-colors underline underline-offset-2"
          >
            Register on GOLD
            <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </div>
        <button
          onClick={handleDismiss}
          className="focusable rounded-sm p-1 text-muted-foreground hover:text-foreground transition-colors min-h-[32px] min-w-[32px] flex items-center justify-center"
          aria-label="Dismiss registration banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
