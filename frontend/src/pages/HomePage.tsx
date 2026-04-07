import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  useEffect(() => {
    document.title = 'Home | Gaucho Course Optimizer'
  }, [])

  return (
    <div className="flex flex-col items-center text-center py-16 px-4 max-w-xl mx-auto">
      <h1 className="font-heading font-bold text-[28px] leading-tight mb-4">
        Find the Best Professor for Any UCSB Course
      </h1>
      <p className="text-base text-muted-foreground mb-8">
        Compare professors by GPA, teaching quality, difficulty, and student sentiment.
      </p>
      <Link to="/search">
        <Button className="bg-accent hover:bg-accent/90 text-accent-foreground">
          Start Searching
        </Button>
      </Link>
    </div>
  )
}
