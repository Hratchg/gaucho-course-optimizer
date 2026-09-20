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
  const { data: courses, isLoading, isError, refetch } = useCourseSearch(query)
  const navigate = useNavigate()
  const hasResults = (courses?.length ?? 0) > 0

  return (
    <Command className="rounded-lg border border-primary/20 shadow-md ring-primary" shouldFilter={false} label="Search courses">
      <CommandInput
        placeholder="Search courses by name or code (e.g., CS 16, Physics)"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {query.trim().length >= 2 && (
          <>
            {isLoading && <CommandLoading>Searching...</CommandLoading>}
            {isError ? (
              /* Search failures must not masquerade as "no results" — during an
                 outage that tells students the course doesn't exist. */
              <div className="py-6 text-center" role="alert">
                <p className="text-sm font-semibold">Search is unavailable</p>
                <p className="text-xs text-muted-foreground">
                  Something went wrong on our end, not with your search.
                </p>
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="mt-3 min-h-[44px] rounded-md border border-primary/30 px-4 text-sm font-medium hover:bg-primary/10"
                >
                  Try again
                </button>
              </div>
            ) : (
              <CommandEmpty>
                <div className="py-6 text-center">
                  <p className="text-sm font-semibold">No courses found</p>
                  <p className="text-xs text-muted-foreground">
                    Try a different course name or code. Example: 'CS 16' or 'Physics 1'
                  </p>
                </div>
              </CommandEmpty>
            )}
            {/* Only render the group when it has children, otherwise an empty
                "Courses" heading dangles under the empty state. */}
            {hasResults && (
              <CommandGroup heading="Courses">
                {courses?.map((course) => (
                  <CommandItem
                    key={course.id}
                    value={`${course.code} ${course.title ?? ''}`}
                    onSelect={() => navigate(`/courses/${course.id}`, { state: { courseCode: course.code } })}
                    className="hover:bg-primary/10"
                  >
                    <span className="font-semibold">{course.code}</span>
                    {course.title && (
                      <span className="ml-2 text-muted-foreground">{course.title}</span>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </>
        )}
      </CommandList>
    </Command>
  )
}
