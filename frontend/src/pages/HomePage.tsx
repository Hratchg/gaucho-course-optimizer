import { useEffect, useState } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
import LibraryLanding from '@/library/LibraryLanding'
import MobileLibraryHero from '@/library/MobileLibraryHero'
import CoursePage from '@/pages/CoursePage'
import { canRender3D } from '@/lib/webgl'
import { courseIdFromPath } from '@/library/courseRoute'

/**
 * Stays mounted for `/` and `/courses/:id` so the shelf does not remount
 * when a book opens. Classic and no-WebGL course links stay a plain page.
 */
export default function HomePage() {
  const location = useLocation()
  const [params] = useSearchParams()
  const [show3D] = useState(() => canRender3D())
  const courseId = courseIdFromPath(location.pathname)
  const classic = params.get('classic') === '1'

  useEffect(() => {
    if (!courseId) document.title = 'Home | CoursePick'
  }, [courseId])

  if (courseId && (classic || !show3D)) return <CoursePage />
  if (!show3D) return <MobileLibraryHero />
  return <LibraryLanding />
}
