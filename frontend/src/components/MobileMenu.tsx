import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetClose,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { NavLink } from 'react-router-dom'
import { Menu } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Home', end: true },
  { to: '/search', label: 'Search', end: false },
]

export default function MobileMenu() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          aria-label="Open navigation menu"
          className="focusable p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-primary-foreground"
        >
          <Menu className="h-5 w-5" />
        </button>
      </SheetTrigger>
      <SheetContent side="right" aria-describedby={undefined}>
        <SheetHeader>
          <SheetTitle className="font-heading text-base font-bold">
            CoursePick
          </SheetTitle>
        </SheetHeader>
        <nav className="flex flex-col mt-4">
          {navItems.map((item) => (
            <SheetClose asChild key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `py-3 px-4 text-base font-sans min-h-[44px] flex items-center rounded-md transition-colors ${
                    isActive
                      ? 'font-bold text-primary border-l-4 border-primary bg-primary/5'
                      : 'text-foreground hover:text-primary hover:bg-primary/5'
                  }`
                }
              >
                {item.label}
              </NavLink>
            </SheetClose>
          ))}
        </nav>
      </SheetContent>
    </Sheet>
  )
}
