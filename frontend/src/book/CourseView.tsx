import { lazy, Suspense, useState } from 'react'
import { useLocation, useParams, useSearchParams } from 'react-router-dom'
import { canRender3D } from '@/lib/webgl'
import type { CourseResult } from '@/types/api'

const LibraryLanding = lazy(() => import('@/library/LibraryLanding'))
const CoursePage = lazy(() => import('@/pages/CoursePage'))

/**
 * /courses/:id — same shelf as home: the course is an open book with the
 * classic HUD. No WebGL / ?classic=1 keeps the standalone CoursePage.
 */
export default function CourseView() {
  const { courseId } = useParams<{ courseId: string }>()
  const [params] = useSearchParams()
  const location = useLocation()
  const [use3D] = useState(() => canRender3D())
  const classic = params.get('classic') === '1'

  const state = location.state as { courseCode?: string; courseTitle?: string | null } | null
  const initialCourse: CourseResult = {
    id: Number(courseId),
    code: state?.courseCode ?? '',
    title: state?.courseTitle ?? null,
    department: null,
  }

  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-4xl px-4 py-16 text-muted-foreground">Loading course…</div>
      }
    >
      {classic || !use3D ? (
        <CoursePage />
      ) : (
        <LibraryLanding initialCourse={initialCourse} startOpen />
      )}
    </Suspense>
  )
}
