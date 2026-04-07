import { Fragment } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  to?: string
}

export default function Breadcrumbs() {
  const { pathname, state } = useLocation()

  const items = buildBreadcrumbs(pathname, state as { courseCode?: string } | null)

  if (!items) return null

  return (
    <nav aria-label="Breadcrumb" className="bg-muted/50 border-b border-border px-4 md:px-6 py-2">
      <ol className="flex items-center gap-1 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1

          return (
            <Fragment key={item.label}>
              {index > 0 && (
                <li aria-hidden="true">
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                </li>
              )}
              {isLast ? (
                <li aria-current="page" className="text-accent font-medium">
                  {item.label}
                </li>
              ) : (
                <li>
                  <Link
                    to={item.to!}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              )}
            </Fragment>
          )
        })}
      </ol>
    </nav>
  )
}

function buildBreadcrumbs(
  pathname: string,
  state: { courseCode?: string } | null
): BreadcrumbItem[] | null {
  if (pathname === '/') return null

  if (pathname === '/search') {
    return [
      { label: 'Home', to: '/' },
      { label: 'Search' },
    ]
  }

  const courseMatch = pathname.match(/^\/courses\/(.+)$/)
  if (courseMatch) {
    const courseLabel = state?.courseCode || 'Course Results'
    return [
      { label: 'Home', to: '/' },
      { label: 'Search', to: '/search' },
      { label: courseLabel },
    ]
  }

  return null
}
