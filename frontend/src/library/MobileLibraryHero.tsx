import { useNavigate } from 'react-router-dom'
import CourseSearchDock from './CourseSearchDock'
import HomeCopy from './HomeCopy'
import type { CourseResult } from '@/types/api'

const SPINES = [
  { h: 72, c: '#3d4a42' },
  { h: 88, c: '#8a4630' },
  { h: 64, c: '#2c3544' },
  { h: 96, c: '#6b4a32' },
  { h: 76, c: '#4a3d38' },
  { h: 84, c: '#5c4030' },
  { h: 68, c: '#3a2c28' },
]

/** Stone landing for small screens and reduced motion. Search is the whole page. */
export default function MobileLibraryHero() {
  const navigate = useNavigate()

  const pickCourse = (course: CourseResult) => {
    navigate(`/courses/${course.id}`, {
      state: { courseCode: course.code, courseTitle: course.title ?? null },
    })
  }

  return (
    <section className="relative min-h-[calc(100dvh-3.5rem)] overflow-hidden bg-[#efeae3] dark:bg-library-fog-night">
      <div className="flex h-[calc(100dvh-3.5rem)] flex-col justify-between pb-32 pt-8">
        <HomeCopy layout="stack" />
        <div className="flex items-end justify-center gap-2" aria-hidden>
          {SPINES.map((spine) => (
            <span
              key={`${spine.c}-${spine.h}`}
              className="w-4 rounded-sm"
              style={{ height: spine.h + 24, backgroundColor: spine.c }}
            />
          ))}
        </div>
        <div />
      </div>

      <CourseSearchDock onPick={pickCourse} />
    </section>
  )
}
