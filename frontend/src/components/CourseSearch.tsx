import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCourseSearch } from '@/hooks/useCourseSearch'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandLoading,
} from '@/components/ui/command'

export default function CourseSearch() {
  const [query, setQuery] = useState('')
  const { data: courses, isLoading } = useCourseSearch(query)
  const navigate = useNavigate()

  return (
    <Command className="rounded-lg border shadow-md" shouldFilter={false}>
      <CommandInput
        placeholder="Search courses by name or code (e.g., CS 16, Physics)"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {query.trim().length >= 2 && (
          <>
            {isLoading && <CommandLoading>Searching...</CommandLoading>}
            <CommandEmpty>
              <div className="py-6 text-center">
                <p className="text-sm font-semibold">No courses found</p>
                <p className="text-xs text-muted-foreground">
                  Try a different course name or code. Example: 'CS 16' or 'Physics 1'
                </p>
              </div>
            </CommandEmpty>
            <CommandGroup heading="Courses">
              {courses?.map((course) => (
                <CommandItem
                  key={course.id}
                  value={`${course.code} ${course.title ?? ''}`}
                  onSelect={() => navigate(`/courses/${course.id}`, { state: { courseCode: course.code } })}
                >
                  <span className="font-semibold">{course.code}</span>
                  {course.title && (
                    <span className="ml-2 text-muted-foreground">{course.title}</span>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          </>
        )}
      </CommandList>
    </Command>
  )
}
