import CourseSearch from '@/components/CourseSearch'

export default function SearchPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="mb-2 text-2xl font-semibold">Gaucho Course Optimizer</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Find the best professor for your UCSB courses
      </p>
      <CourseSearch />
    </div>
  )
}
