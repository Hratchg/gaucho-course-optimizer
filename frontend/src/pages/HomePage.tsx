import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card'
import {
  GraduationCap,
  Star,
  TrendingDown,
  MessageCircle,
  Search,
  BarChart2,
  SlidersHorizontal,
} from 'lucide-react'

const factors = [
  {
    name: 'GPA',
    icon: GraduationCap,
    definition:
      "Average grade students earn in this professor\u2019s sections \u2014 higher means easier grading",
    example: 'Example: 3.45 / 4.00',
  },
  {
    name: 'Quality',
    icon: Star,
    definition:
      "How highly students rate this professor\u2019s teaching on RateMyProfessors",
    example: 'Example: 4.2 / 5.0',
  },
  {
    name: 'Difficulty',
    icon: TrendingDown,
    definition:
      'How hard students find the workload \u2014 lower difficulty means a more manageable course',
    example: 'Example: 2.8 / 5.0',
  },
  {
    name: 'Sentiment',
    icon: MessageCircle,
    definition:
      'Percentage of recent student comments that express a positive experience',
    example: 'Example: 72% positive',
  },
]

const steps = [
  {
    number: 1,
    icon: Search,
    title: 'Search a Course',
    body: 'Type any UCSB course name or code \u2014 like "CMPSC 130A" or "Introduction to Algorithms"',
  },
  {
    number: 2,
    icon: BarChart2,
    title: 'Compare Professors',
    body: 'See every professor ranked by Prof Score with GPA, ratings, and student comments side by side',
  },
  {
    number: 3,
    icon: SlidersHorizontal,
    title: 'Adjust Your Priorities',
    body: 'Toggle what matters most to you \u2014 grades, teaching, difficulty, or reviews \u2014 and rankings update instantly',
  },
]

export default function HomePage() {
  useEffect(() => {
    document.title = 'Home | CoursePick'
  }, [])

  return (
    <div>
      {/* Content container */}
      <div className="max-w-4xl mx-auto px-4">
        {/* Section 1: Hero */}
        <section className="py-16 text-center">
          <h1 className="font-heading font-bold text-[28px] leading-tight mb-4">
            Find the Best Professor for Any UCSB Course
          </h1>
          <p className="text-base text-muted-foreground max-w-2xl mx-auto">
            Search any UCSB course and instantly see which professor will give
            you the best outcome &mdash; ranked by GPA, teaching quality,
            difficulty, and student sentiment.
          </p>
        </section>

        {/* Section 2: Score Breakdown */}
        <section className="py-16">
          <h2 className="font-heading font-bold text-[20px] text-center mb-8">
            How Prof Score Works
          </h2>
          <p className="text-sm text-muted-foreground text-center mb-6">
            Each score is a 0&ndash;100 composite of four equally weighted
            factors. Weights are adjustable on the results page.
          </p>

          {/* Score bar */}
          <div
            role="img"
            aria-label="Prof Score breakdown: four equally weighted factors"
            className="flex w-full h-10 rounded-lg overflow-hidden ring-1 ring-foreground/10"
          >
            <div
              className="flex-1 bg-primary"
              aria-label="GPA: 25%"
            />
            <div
              className="flex-1 bg-secondary"
              aria-label="Quality: 25%"
            />
            <div
              className="flex-1 bg-[oklch(0.75_0.10_180)]"
              aria-label="Difficulty: 25%"
            />
            <div
              className="flex-1 bg-[oklch(0.8549_0.1251_181.07)]"
              aria-label="Sentiment: 25%"
            />
          </div>

          {/* Labels row */}
          <div className="flex justify-between mt-2">
            <span className="text-[14px] text-muted-foreground text-center flex-1">
              GPA &middot; 25%
            </span>
            <span className="text-[14px] text-muted-foreground text-center flex-1">
              Quality &middot; 25%
            </span>
            <span className="text-[14px] text-muted-foreground text-center flex-1">
              Difficulty &middot; 25%
            </span>
            <span className="text-[14px] text-muted-foreground text-center flex-1">
              Sentiment &middot; 25%
            </span>
          </div>

          {/* Score badge example */}
          <p className="text-sm font-medium text-foreground text-center mt-4">
            Example: a score of 78/100
          </p>
        </section>

        {/* Section 3: Factor Cards */}
        <section className="py-16">
          <h2 className="font-heading font-bold text-[20px] text-center mb-8">
            What Each Factor Means
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {factors.map((factor) => {
              const Icon = factor.icon
              return (
                <Card key={factor.name}>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Icon size={24} className="text-primary" />
                      <CardTitle>
                        <h3 className="font-heading font-bold text-base">
                          {factor.name}
                        </h3>
                      </CardTitle>
                    </div>
                    <CardDescription>{factor.definition}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium text-foreground">
                      {factor.example}
                    </p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </section>

        {/* Section 4: Usage Guide */}
        <section className="py-16">
          <h2 className="font-heading font-bold text-[20px] text-center mb-8">
            How to Use CoursePick
          </h2>
          <ol className="flex flex-col md:flex-row items-start justify-between gap-8 list-none p-0">
            {steps.map((step, index) => {
              const Icon = step.icon
              return (
                <li
                  key={step.number}
                  className="flex flex-col items-center text-center flex-1 w-full"
                >
                  {/* Connector line (desktop only, before steps 2 and 3) */}
                  {index > 0 && (
                    <div className="hidden md:block w-full h-px bg-border -mt-5 mb-5" />
                  )}
                  <div
                    className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-heading font-bold text-base"
                    aria-hidden="true"
                  >
                    {step.number}
                  </div>
                  <Icon size={20} className="text-primary mt-2" />
                  <p className="font-heading font-medium text-base mt-3">
                    {step.title}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {step.body}
                  </p>
                </li>
              )
            })}
          </ol>
        </section>
      </div>

      {/* Section 5: Final CTA Banner (full-bleed) */}
      <section className="bg-primary">
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <h2 className="font-heading font-bold text-[28px] text-primary-foreground mb-4">
            Ready to Find Your Professor?
          </h2>
          <p className="text-base text-primary-foreground/80 mb-8">
            Search any UCSB course and see ranked results in seconds.
          </p>
          <Link to="/search">
            <Button
              size="lg"
              className="bg-accent hover:bg-accent/90 text-accent-foreground min-h-[44px] px-6"
            >
              Start Searching
            </Button>
          </Link>
        </div>
      </section>
    </div>
  )
}
