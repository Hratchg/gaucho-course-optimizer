import { useFreshness } from '@/hooks/useFreshness'

function useGradeLine() {
  const { data } = useFreshness()
  if (!data?.latest_grade_year) return 'Official UCSB grades'
  const term = `${data.latest_grade_quarter ?? ''} ${data.latest_grade_year}`.trim()
  return `Grades through ${term}`
}

/**
 * The words around the sphere. Hidden once a course is open so the book
 * and the panel have the stage.
 */
export default function HomeCopy({ layout }: { layout: 'stage' | 'stack' }) {
  const gradeLine = useGradeLine()
  const facts = [gradeLine, 'Matched RateMyProfessors reviews', 'This quarter and the next']

  if (layout === 'stack') {
    return (
      <div className="px-6">
        <h1 className="font-heading text-3xl font-semibold tracking-tight text-foreground">
          Search UCSB courses
        </h1>
        <p className="mt-3 max-w-[28ch] text-sm leading-relaxed text-muted-foreground">
          Choose a course. You get the professors ranked for that class.
        </p>
        <ul className="mt-8 space-y-2 text-sm text-muted-foreground">
          {facts.map((fact) => (
            <li key={fact}>{fact}</li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="pointer-events-none absolute inset-0 z-10">
      <div className="absolute left-8 top-10 w-[min(16rem,24vw)] md:left-12">
        <h1 className="font-heading text-4xl font-semibold tracking-tight text-foreground">
          Search UCSB courses
        </h1>
        <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
          Choose a course. A book leaves the sphere, and the professors are ranked for that class.
        </p>
      </div>
      <ul className="absolute right-8 top-10 hidden w-[min(16rem,22vw)] space-y-3 text-right text-sm leading-relaxed text-muted-foreground xl:block md:right-12">
        {facts.map((fact) => (
          <li key={fact}>{fact}</li>
        ))}
      </ul>
    </div>
  )
}
