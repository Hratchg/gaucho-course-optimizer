import { useQuery } from '@tanstack/react-query'
import { fetchFreshness } from '@/lib/api'

export function useFreshness() {
  return useQuery({
    queryKey: ['freshness'],
    queryFn: fetchFreshness,
    staleTime: 1000 * 60 * 30,
    retry: 1,
  })
}
