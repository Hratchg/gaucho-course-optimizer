import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'

const CASES: { label: string; x: number; spines: { w: number; h: number; fill: string }[] }[] = [
  {
    label: 'MATH',
    x: 8,
    spines: [
      { w: 7, h: 26, fill: '#E85A4F' },
      { w: 5, h: 22, fill: '#7B4DB8' },
      { w: 8, h: 28, fill: '#F5C84C' },
      { w: 6, h: 20, fill: '#3DB8A8' },
      { w: 5, h: 24, fill: '#5BA3D9' },
      { w: 7, h: 27, fill: '#E85A4F' },
    ],
  },
  {
    label: 'CHEM',
    x: 96,
    spines: [
      { w: 6, h: 24, fill: '#7B4DB8' },
      { w: 8, h: 28, fill: '#3DB8A8' },
      { w: 5, h: 21, fill: '#F5C84C' },
      { w: 7, h: 26, fill: '#E85A4F' },
      { w: 5, h: 23, fill: '#5BA3D9' },
      { w: 6, h: 25, fill: '#7B4DB8' },
    ],
  },
  {
    label: 'PHYS',
    x: 184,
    spines: [
      { w: 7, h: 27, fill: '#5BA3D9' },
      { w: 5, h: 20, fill: '#E85A4F' },
      { w: 8, h: 29, fill: '#7B4DB8' },
      { w: 6, h: 23, fill: '#F5C84C' },
      { w: 5, h: 25, fill: '#3DB8A8' },
      { w: 7, h: 22, fill: '#E85A4F' },
    ],
  },
  {
    label: 'CMPSC',
    x: 272,
    spines: [
      { w: 6, h: 25, fill: '#F5C84C' },
      { w: 8, h: 28, fill: '#E85A4F' },
      { w: 5, h: 21, fill: '#5BA3D9' },
      { w: 7, h: 26, fill: '#7B4DB8' },
      { w: 5, h: 24, fill: '#3DB8A8' },
      { w: 6, h: 27, fill: '#F5C84C' },
    ],
  },
]

function ShelfUnit({ label, x, spines }: (typeof CASES)[number]) {
  const shelfYs = [52, 86, 120]
  return (
    <g transform={`translate(${x} 0)`}>
      <rect x="0" y="18" width="80" height="118" rx="3" fill="#4A3F63" />
      <rect x="5" y="23" width="70" height="108" fill="#2B2438" />
      {shelfYs.map((y) => {
        let left = 9
        return (
          <g key={y}>
            <rect x="5" y={y} width="70" height="5" fill="#6B5A3E" />
            {spines.map((s, i) => {
              const xPos = left
              left += s.w + 2
              return (
                <rect
                  key={`${y}-${i}`}
                  x={xPos}
                  y={y - s.h}
                  width={s.w}
                  height={s.h}
                  fill={s.fill}
                />
              )
            })}
          </g>
        )
      })}
      <rect x="16" y="6" width="48" height="14" rx="2" fill="#C4A35A" />
      <text
        x="40"
        y="16.5"
        textAnchor="middle"
        fill="#1C1408"
        fontSize="8"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="800"
      >
        {label}
      </text>
    </g>
  )
}

/**
 * Static 2D stand-in for the 3D stacks on small viewports / reduced motion.
 * CSS + inline SVG only — no extra image assets.
 */
export default function MobileLibraryHero() {
  return (
    <section className="relative overflow-hidden bg-brand-ink text-white">
      <div className="relative z-10 mx-auto max-w-lg px-4 pb-4 pt-10 text-center">
        <p className="font-script text-2xl text-brand-sun">welcome to the stacks</p>
        <h1 className="mt-1 font-heading text-3xl font-extrabold leading-tight">
          Every UCSB course.
          <br />
          One library.
        </h1>
        <p className="mt-3 text-sm text-white/70">
          Search any course and compare professors by Gaucho Score.
        </p>
        <Link
          to="/search"
          className="focusable btn-press mt-6 flex items-center gap-3 rounded-2xl bg-white px-4 py-4 text-left shadow-2xl ring-1 ring-black/10 dark:bg-white/10 dark:ring-white/15"
          aria-label="Search courses"
        >
          <Search className="h-5 w-5 shrink-0 text-brand-violet dark:text-brand-sun" aria-hidden />
          <span className="font-sans text-base text-brand-ink/55 dark:text-white/60">
            Find a course — try &ldquo;CMPSC 130A&rdquo;
          </span>
        </Link>
      </div>

      <svg
        className="pointer-events-none relative mt-6 block h-40 w-full"
        viewBox="0 0 360 160"
        preserveAspectRatio="xMidYMax meet"
        aria-hidden
      >
        <rect x="0" y="144" width="360" height="16" fill="#1A1528" />
        {CASES.map((c) => (
          <ShelfUnit key={c.label} {...c} />
        ))}
      </svg>
    </section>
  )
}
