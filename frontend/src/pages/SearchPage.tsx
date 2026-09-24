import { Navigate } from 'react-router-dom'

/** Search lives on home. Keep this path so old links still land on the shelf. */
export default function SearchPage() {
  return <Navigate to="/" replace />
}
