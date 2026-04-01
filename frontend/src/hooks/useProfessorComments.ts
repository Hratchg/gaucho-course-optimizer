import { useQuery } from '@tanstack/react-query'
import { fetchComments } from '@/lib/api'

export function useProfessorComments(professorId: number, limit: number = 5) {
  return useQuery({
    queryKey: ['comments', professorId, limit],
    queryFn: () => fetchComments(professorId, limit),
    enabled: professorId > 0,
  })
}
