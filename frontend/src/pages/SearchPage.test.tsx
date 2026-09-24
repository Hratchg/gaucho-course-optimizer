import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SearchPage from './SearchPage'

describe('SearchPage', () => {
  it('redirects to home', () => {
    render(
      <MemoryRouter initialEntries={['/search']}>
        <Routes>
          <Route path="/search" element={<SearchPage />} />
          <Route path="/" element={<div>home shelf</div>} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText('home shelf')).toBeInTheDocument()
  })
})
