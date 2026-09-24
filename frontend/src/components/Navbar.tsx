import { Link, NavLink, useLocation } from 'react-router-dom'
import MobileMenu from '@/components/MobileMenu'
import BrandWordmark from '@/components/BrandWordmark'

export default function Navbar() {
  const onCourse = useLocation().pathname.startsWith('/courses/')
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `focusable rounded-sm text-sm transition-colors ${isActive
      ? 'text-foreground'
      : 'text-muted-foreground hover:text-foreground'}`

  return (
    <header className="sticky top-0 z-50 h-14 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <nav className="flex items-center justify-between px-4 md:px-6 h-full max-w-7xl mx-auto">
        <Link to="/" replace={onCourse} aria-label="CoursePick" className="focusable btn-press text-foreground">
          <BrandWordmark />
        </Link>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-4">
            <NavLink to="/" end replace={onCourse} className={linkClass}>
              Home
            </NavLink>
            <NavLink to="/methodology" className={linkClass}>
              Methodology
            </NavLink>
          </div>

          {/* Mobile hamburger menu */}
          <div className="flex md:hidden">
            <MobileMenu />
          </div>
        </div>
      </nav>
    </header>
  )
}
