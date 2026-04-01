import { useQuery } from '@tanstack/react-query'
import { fetchProfessors } from '@/lib/api'

export function useProfessors(courseId: number) {
  return useQuery({
    queryKey: ['professors', courseId],
    queryFn: () => fetchProfessors(courseId),
    enabled: courseId > 0,
  })
}
