import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { courseIdFromPath } from './courseRoute'
import ClassicBookHud from './ClassicBookHud'
import CourseSearchDock from './CourseSearchDock'
import HomeCopy from './HomeCopy'
import { FLIGHT_MS, RETURN_MS } from './flight'
import type { SphereFlight } from './LibraryScene'
import type { CourseResult } from '@/types/api'

const LibraryScene = lazy(() => import('./LibraryScene'))

const CLOSE_MS = 200

interface LibraryLandingProps {
  initialCourse?: CourseResult | null
  /** Deep link: skip the pull and show the open book. */
  startOpen?: boolean
}

function courseFromLocation(pathname: string, state: unknown): CourseResult | null {
  const id = courseIdFromPath(pathname)
  if (id == null) return null
  const nav = state as { courseCode?: string; courseTitle?: string | null } | null
  return {
    id,
    code: nav?.courseCode ?? '',
    title: nav?.courseTitle ?? null,
    department: null,
  }
}

/**
 * A rotating sphere of books. Search pulls one book to the right and docks
 * the sphere on the left; the open book is the classic course HUD.
 */
export default function LibraryLanding({ initialCourse = null, startOpen = false }: LibraryLandingProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const routed = courseFromLocation(location.pathname, location.state)
  const [picked, setPicked] = useState<CourseResult | null>(initialCourse ?? routed)
  const [hudOpen, setHudOpen] = useState(Boolean((initialCourse && startOpen) || routed))
  const [closing, setClosing] = useState(false)
  const [flight, setFlight] = useState<SphereFlight | null>(null)
  const [holdBook, setHoldBook] = useState(false)
  const openTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const heldRef = useRef(false)
  const flightGen = useRef(0)
  const routeId = courseIdFromPath(location.pathname)
  const routeIdRef = useRef(routeId)
  const pathnameRef = useRef(location.pathname)
  pathnameRef.current = location.pathname

  const docked = Boolean(picked) && !closing

  useEffect(() => {
    return () => {
      if (openTimer.current) clearTimeout(openTimer.current)
      if (closeTimer.current) clearTimeout(closeTimer.current)
    }
  }, [])

  useEffect(() => {
    const previous = routeIdRef.current
    routeIdRef.current = routeId
    if (previous != null && routeId == null) {
      if (openTimer.current) clearTimeout(openTimer.current)
      if (closeTimer.current) clearTimeout(closeTimer.current)
      setClosing(false)
      setHudOpen(false)
      setPicked(null)
      setFlight(null)
      setHoldBook(false)
      heldRef.current = false
      return
    }
    if (routeId != null && previous !== routeId) {
      const fromUrl = courseFromLocation(location.pathname, location.state)
      setPicked((current) => (current?.id === routeId && current.code ? current : fromUrl))
      setClosing(false)
      setHudOpen(true)
    }
  }, [routeId, location.pathname, location.state])

  useEffect(() => {
    if (hudOpen && picked) {
      const label = picked.code?.trim() || `Course ${picked.id}`
      document.title = `${label} | CoursePick`
    } else if (!hudOpen) {
      document.title = 'Home | CoursePick'
    }
  }, [hudOpen, picked])

  const closeBook = useCallback(() => {
    if (!hudOpen || closing) return
    setClosing(true)
    setFlight(null)
    setHoldBook(false)
    heldRef.current = false
    flightGen.current += 1
    if (closeTimer.current) clearTimeout(closeTimer.current)
    closeTimer.current = setTimeout(() => {
      setClosing(false)
      setHudOpen(false)
      setPicked(null)
      if (courseIdFromPath(pathnameRef.current) != null) {
        navigate('/', { replace: true })
      }
    }, CLOSE_MS)
  }, [hudOpen, closing, navigate])

  useEffect(() => {
    if (!hudOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape' || event.defaultPrevented) return
      closeBook()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [hudOpen, closeBook])

  const beginOut = (c: CourseResult, token: number) => {
    heldRef.current = true
    setHoldBook(true)
    setClosing(false)
    setHudOpen(false)
    setPicked(c)
    setFlight({ direction: 'out', claimKey: token })
    const replace = courseIdFromPath(pathnameRef.current) != null
    openTimer.current = setTimeout(() => {
      if (flightGen.current !== token) return
      setFlight(null)
      setHudOpen(true)
      navigate(`/courses/${c.id}`, {
        replace,
        state: { courseCode: c.code, courseTitle: c.title ?? null },
      })
    }, FLIGHT_MS)
  }

  const pickCourse = (c: CourseResult) => {
    if (openTimer.current) clearTimeout(openTimer.current)
    if (closeTimer.current) clearTimeout(closeTimer.current)
    const token = ++flightGen.current
    if (heldRef.current && hudOpen) {
      setClosing(false)
      setHudOpen(false)
      setFlight({ direction: 'back', claimKey: token })
      openTimer.current = setTimeout(() => {
        if (flightGen.current !== token) return
        beginOut(c, token)
      }, RETURN_MS)
      return
    }
    beginOut(c, token)
  }

  const showHud = Boolean(picked && (hudOpen || closing))

  return (
    <section className="library-wall relative h-[calc(100dvh-3.5rem)] min-h-[480px] w-full overflow-hidden">
      <div className="absolute inset-0">
        <Suspense fallback={<div className="library-wall h-full w-full" aria-hidden />}>
          <LibraryScene
            docked={docked || flight != null}
            flight={flight}
            holdBook={holdBook}
            night
            onSphereClick={showHud ? closeBook : undefined}
          />
        </Suspense>
      </div>

      {!picked && <HomeCopy layout="stage" />}

      {showHud && picked && (
        <div className="pointer-events-none absolute inset-0 z-20">
          <div className="pointer-events-auto absolute bottom-24 right-3 top-3 w-[calc(66.666vw-0.75rem)]">
            <ClassicBookHud
              courseId={picked.id}
              code={picked.code}
              title={picked.title}
              closing={closing}
              onClose={closeBook}
            />
          </div>
        </div>
      )}

      <CourseSearchDock
        onPick={pickCourse}
        placeholder={picked ? 'Search another course' : 'Search a course'}
        caption={picked ? undefined : 'Find the right professor for any UCSB course'}
      />
    </section>
  )
}
