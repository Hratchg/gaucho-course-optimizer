interface BrandWordmarkProps {
  /** Tailwind text size class, defaults to text-xl */
  className?: string
}

/** CoursePick wordmark: open-book mark + two-tone name. */
export default function BrandWordmark({ className = 'text-xl' }: BrandWordmarkProps) {
  return (
    <span className={`inline-flex items-center gap-2 font-heading font-semibold tracking-tight ${className}`}>
      <svg
        width="1.2em"
        height="1.2em"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <path d="M12 7v14" stroke="var(--brand-coral)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <path
          d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        Course<span className="text-brand-coral">Pick</span>
      </span>
    </span>
  )
}
