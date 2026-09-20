import { useEffect } from 'react'
import CourseSearch from '@/components/CourseSearch'

export default function SearchPage() {
  useEffect(() => {
    document.title = 'Search | CoursePick'
  }, [])

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <p className="font-script text-2xl text-brand-violet">what are you taking?</p>
      <h1 className="mb-2 mt-1 text-3xl font-heading font-extrabold text-foreground">
        Search courses
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Type a course code or name and pick from the list — we&rsquo;ll rank every
        professor who has taught it.
      </p>
      <CourseSearch />
    </div>
  )
}
