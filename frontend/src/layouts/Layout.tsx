import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '@/components/Navbar'
import Breadcrumbs from '@/components/Breadcrumbs'
import { RegistrationBanner } from '@/components/RegistrationBanner'
import { Footer } from '@/components/Footer'

export default function Layout() {
  const location = useLocation()
  const shelfMode =
    location.pathname === '/' || /^\/courses\/[^/]+$/.test(location.pathname)
  const pageKey = shelfMode ? 'shelf' : location.pathname

  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main-content"
        className="skip-to-content"
      >
        Skip to content
      </a>
      <Navbar />
      <RegistrationBanner />
      {!shelfMode && <Breadcrumbs />}
      <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
        <div key={pageKey} className="page-enter">
          <Outlet />
        </div>
      </main>
      {!shelfMode && <Footer />}
    </div>
  )
}
