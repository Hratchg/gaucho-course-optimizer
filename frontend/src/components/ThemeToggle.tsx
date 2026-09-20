import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? 'Switch to day mode' : 'Switch to night mode'}
      className="focusable btn-press inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/30 text-white hover:bg-white/10 transition-colors"
    >
      {isDark ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  )
}
