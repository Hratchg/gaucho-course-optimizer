import { Link, NavLink } from 'react-router-dom'
import MobileMenu from '@/components/MobileMenu'

export default function Navbar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `focusable rounded-sm font-sans ${isActive
      ? 'font-bold text-white'
      : 'text-primary-foreground/80 hover:text-white transition-colors'}`

  return (
    <header className="sticky top-0 z-50 h-14 bg-primary shadow-md">
      <nav className="flex items-center justify-between px-4 md:px-6 h-full max-w-7xl mx-auto">
        <Link to="/" className="focusable btn-press font-heading font-bold text-xl text-white">
          CoursePick
        </Link>

        <div className="flex items-center gap-4">
          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-4">
            <NavLink to="/" end className={linkClass}>
              Home
            </NavLink>
            <NavLink to="/search" className={linkClass}>
              Search
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
