import { lazy, Suspense, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { canRender3D } from '@/lib/webgl'

const BookCourseView = lazy(() => import('./BookCourseView'))
const CoursePage = lazy(() => import('@/pages/CoursePage'))

/**
 * Gate for /courses/:id — the 3D open book when WebGL is available and the
 * user hasn't asked for the classic layout (?classic=1); the existing 2D
 * CoursePage otherwise. The book is its own lazy chunk, so the classic page
 * loads nothing extra.
 */
export default function CourseView() {
  const [params] = useSearchParams()
  const classic = params.get('classic') === '1'
  const use3D = useMemo(() => !classic && canRender3D(), [classic])

  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-4xl px-4 py-16 text-muted-foreground">Loading course…</div>
      }
    >
      {use3D ? <BookCourseView /> : <CoursePage />}
    </Suspense>
  )
}
