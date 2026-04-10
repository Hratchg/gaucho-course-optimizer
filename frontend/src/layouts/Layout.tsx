import { Outlet } from 'react-router-dom'
import Navbar from '@/components/Navbar'
import Breadcrumbs from '@/components/Breadcrumbs'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main-content"
        className="skip-to-content"
      >
        Skip to content
      </a>
      <Navbar />
      <Breadcrumbs />
      <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
        <Outlet />
      </main>
    </div>
  )
}
