import { Routes, Route } from 'react-router-dom'
import SearchPage from '@/pages/SearchPage'
import CoursePage from '@/pages/CoursePage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SearchPage />} />
      <Route path="/courses/:courseId" element={<CoursePage />} />
    </Routes>
  )
}
