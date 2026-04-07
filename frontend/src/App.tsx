import { Routes, Route } from 'react-router-dom'
import Layout from '@/layouts/Layout'
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import CoursePage from '@/pages/CoursePage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/courses/:courseId" element={<CoursePage />} />
      </Route>
    </Routes>
  )
}
