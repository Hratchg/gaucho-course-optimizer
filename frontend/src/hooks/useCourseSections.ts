import { useQuery } from '@tanstack/react-query'
import { fetchCourseSections } from '@/lib/api'

export function useCourseSections(courseId: number) {
  return useQuery({
    queryKey: ['course-sections', courseId],
    queryFn: () => fetchCourseSections(courseId),
    enabled: courseId > 0,
  })
}
