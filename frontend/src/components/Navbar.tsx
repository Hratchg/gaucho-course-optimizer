import { Link, NavLink } from 'react-router-dom'
import MobileMenu from '@/components/MobileMenu'
import ThemeToggle from '@/components/ThemeToggle'
import BrandWordmark from '@/components/BrandWordmark'

export default function Navbar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `focusable rounded-sm font-sans ${isActive
      ? 'font-bold text-white'
      : 'text-white/80 hover:text-white transition-colors'}`

  return (
    <header className="sticky top-0 z-50 h-14 border-b-2 border-brand-gold bg-brand-ink shadow-md">
      <nav className="flex items-center justify-between px-4 md:px-6 h-full max-w-7xl mx-auto">
        <Link to="/" aria-label="CoursePick" className="focusable btn-press text-white">
          <BrandWordmark />
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
            <NavLink to="/methodology" className={linkClass}>
              Methodology
            </NavLink>
          </div>

          <ThemeToggle />

          {/* Mobile hamburger menu */}
          <div className="flex md:hidden">
            <MobileMenu />
          </div>
        </div>
      </nav>
    </header>
  )
}
