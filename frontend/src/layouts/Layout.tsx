import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '@/components/Navbar'
import Breadcrumbs from '@/components/Breadcrumbs'
import { RegistrationBanner } from '@/components/RegistrationBanner'

export default function Layout() {
  const location = useLocation()

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
      <Breadcrumbs />
      <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
        <div key={location.pathname} className="page-enter">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
