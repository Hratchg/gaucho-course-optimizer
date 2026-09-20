import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from '@/layouts/Layout'
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import MethodologyPage from '@/pages/MethodologyPage'

const CoursePage = lazy(() => import('@/pages/CoursePage'))

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route
          path="/courses/:courseId"
          element={
            <Suspense fallback={<div className="mx-auto max-w-4xl px-4 py-16 text-muted-foreground">Loading course…</div>}>
              <CoursePage />
            </Suspense>
          }
        />
        <Route path="/methodology" element={<MethodologyPage />} />
      </Route>
    </Routes>
  )
}
