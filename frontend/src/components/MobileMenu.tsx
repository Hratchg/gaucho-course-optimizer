import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetClose,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { NavLink, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Home', end: true },
  { to: '/methodology', label: 'Methodology', end: false },
]

export default function MobileMenu() {
  const onCourse = useLocation().pathname.startsWith('/courses/')

  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          aria-label="Open navigation menu"
          className="focusable p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-foreground"
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
                replace={item.to === '/' && onCourse}
                className={({ isActive }) =>
                  `py-3 px-4 text-base min-h-[44px] flex items-center rounded-lg transition-colors ${
                    isActive
                      ? 'bg-muted text-foreground'
                      : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'
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
