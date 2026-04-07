import { Outlet } from 'react-router-dom'
import Navbar from '@/components/Navbar'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      {/* Breadcrumbs component will be added here in Plan 02 */}
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
