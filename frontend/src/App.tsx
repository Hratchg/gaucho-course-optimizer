import { Routes, Route } from 'react-router-dom'
import Layout from '@/layouts/Layout'
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import MethodologyPage from '@/pages/MethodologyPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route element={<HomePage />}>
          <Route path="/" element={<></>} />
          <Route path="/courses/:courseId" element={<></>} />
        </Route>
        <Route path="/search" element={<SearchPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
      </Route>
    </Routes>
  )
}
