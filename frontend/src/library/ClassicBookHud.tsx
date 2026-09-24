import { Link } from 'react-router-dom'
import { X } from 'lucide-react'
import CoursePage from '@/pages/CoursePage'

/**
 * Open-book frame that hosts the classic course HUD. The 3D shelf stays
 * behind; this is the readable surface after a book is pulled.
 */
export default function ClassicBookHud({
  courseId,
  code,
  title,
  closing = false,
  onClose,
}: {
  courseId: number
  code?: string
  title?: string | null
  closing?: boolean
  onClose: () => void
}) {
  const heading = code?.trim() || `Course ${courseId}`

  return (
    <div
      data-testid="classic-book-hud"
      className={`pointer-events-auto flex h-full w-full overflow-hidden rounded-xl bg-card text-card-foreground shadow-[0_18px_50px_-28px_oklch(0.22_0.02_50_/_0.4)] ring-1 ring-border ${
        closing ? 'book-close' : 'book-open'
      }`}
    >
      <div className="w-1 shrink-0 bg-primary" aria-hidden />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-border/70 px-5 py-3">
          <div className="min-w-0">
            <p className="truncate font-heading text-lg font-semibold tracking-tight">{heading}</p>
            {title && <p className="truncate text-sm text-muted-foreground">{title}</p>}
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              A 0–100 score from UCSB grades and RateMyProfessors.{' '}
              <Link to="/methodology" className="text-foreground underline-offset-2 hover:underline">
                How scoring works
              </Link>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="focusable btn-press inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          <CoursePage key={courseId} courseId={courseId} compact />
        </div>
      </div>
    </div>
  )
}
