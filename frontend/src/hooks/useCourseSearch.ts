import { useQuery } from '@tanstack/react-query'
import { fetchCourses } from '@/lib/api'

export function useCourseSearch(query: string) {
  return useQuery({
    queryKey: ['courses', 'search', query],
    queryFn: () => fetchCourses(query),
    enabled: query.trim().length >= 2,
    staleTime: 5 * 60 * 1000,
    retry: 3,
  })
}
