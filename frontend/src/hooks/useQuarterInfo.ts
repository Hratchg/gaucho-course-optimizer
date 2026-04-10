import { useQuery } from '@tanstack/react-query'
import { fetchQuarterInfo } from '@/lib/api'

export function useQuarterInfo() {
  return useQuery({
    queryKey: ['quarterInfo'],
    queryFn: fetchQuarterInfo,
    staleTime: 1000 * 60 * 30, // 30 minutes — quarter info changes rarely
    retry: 1,
  })
}
