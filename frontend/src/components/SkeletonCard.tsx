import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export function SkeletonCard() {
  return (
    <Card className="mb-6 border-l-4 border-l-gray-200">
      <CardContent className="p-4">
        {/* Row 1: Name + Score */}
        <div className="flex items-start justify-between">
          <Skeleton className="shimmer h-6 w-40" />
          <Skeleton className="shimmer h-8 w-12" />
        </div>
        {/* Row 2: GPA */}
        <Skeleton className="shimmer mt-2 h-4 w-32" />
        {/* Row 3: RMP stats */}
        <div className="mt-2 flex gap-4">
          <Skeleton className="shimmer h-4 w-24" />
          <Skeleton className="shimmer h-4 w-24" />
          <Skeleton className="shimmer h-4 w-28" />
        </div>
        {/* Row 4: Tags */}
        <div className="mt-3 flex gap-1">
          <Skeleton className="shimmer h-5 w-16 rounded-full" />
          <Skeleton className="shimmer h-5 w-20 rounded-full" />
          <Skeleton className="shimmer h-5 w-14 rounded-full" />
        </div>
      </CardContent>
    </Card>
  )
}
