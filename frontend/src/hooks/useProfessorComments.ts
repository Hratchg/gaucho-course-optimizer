import { useQuery } from '@tanstack/react-query'
import { fetchComments } from '@/lib/api'

export function useProfessorComments(professorId: number, limit: number = 5) {
  return useQuery({
    queryKey: ['comments', professorId],
    queryFn: () => fetchComments(professorId, limit),
    enabled: professorId > 0,
    staleTime: 5 * 60 * 1000,
    retry: 3,
  })
}
