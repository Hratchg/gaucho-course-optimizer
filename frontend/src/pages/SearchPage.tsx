import { useEffect } from 'react'
import CourseSearch from '@/components/CourseSearch'

export default function SearchPage() {
  useEffect(() => {
    document.title = 'Search | CoursePick'
  }, [])

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="mb-6 text-xl font-heading font-semibold">Search Courses</h1>
      <CourseSearch />
    </div>
  )
}
