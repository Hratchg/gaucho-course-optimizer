import { useQuery } from '@tanstack/react-query'
import { fetchGrades } from '@/lib/api'

export function useProfessorGrades(professorId: number, courseId: number) {
  return useQuery({
    queryKey: ['grades', professorId, courseId],
    queryFn: () => fetchGrades(professorId, courseId),
    enabled: professorId > 0 && courseId > 0,
  })
}
