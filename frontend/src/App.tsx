import { Routes, Route } from 'react-router-dom'
import Layout from '@/layouts/Layout'
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import MethodologyPage from '@/pages/MethodologyPage'
import CourseView from '@/book/CourseView'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/courses/:courseId" element={<CourseView />} />
        <Route path="/methodology" element={<MethodologyPage />} />
      </Route>
    </Routes>
  )
}
