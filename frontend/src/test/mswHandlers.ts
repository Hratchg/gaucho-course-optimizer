import { http, HttpResponse } from 'msw'
import type { CourseResult, ProfessorRanking, GradeQuarter, CommentResult } from '@/types/api'

const mockCourses: CourseResult[] = [
  { id: 1, code: 'CMPSC 8', title: 'Intro to CS', department: 'CMPSC' },
]

const mockProfessors: ProfessorRanking[] = [
  {
    id: 101,
    name: 'Alice Smith',
    department: 'CMPSC',
    gaucho_score: 82,
    gpa_factor: 0.85,
    quality_factor: 0.80,
    difficulty_factor: 0.65,
    sentiment_factor: 0.75,
    rmp_quality: 4.1,
    rmp_difficulty: 3.2,
    rmp_would_take_again: 0.78,
    rmp_num_ratings: 120,
    mean_gpa: 3.4,
    std_gpa: 0.45,
    avg_sentiment: 0.6,
    match_confidence: 0.95,
    quarters_taught: 8,
    keywords: ['clear', 'helpful', 'challenging'],
  },
  {
    id: 102,
    name: 'Bob Jones',
    department: 'CMPSC',
    gaucho_score: 71,
    gpa_factor: 0.72,
    quality_factor: 0.68,
    difficulty_factor: 0.55,
    sentiment_factor: 0.60,
    rmp_quality: 3.5,
    rmp_difficulty: 2.8,
    rmp_would_take_again: 0.62,
    rmp_num_ratings: 55,
    mean_gpa: 3.1,
    std_gpa: 0.50,
    avg_sentiment: 0.3,
    match_confidence: 0.88,
    quarters_taught: 5,
    keywords: ['straightforward', 'fair'],
  },
]

const mockGrades: GradeQuarter[] = [
  {
    quarter: 'F22',
    avg_gpa: 3.2,
    a_plus: 5, a: 20, a_minus: 10,
    b_plus: 8, b: 15, b_minus: 6,
    c_plus: 3, c: 4, c_minus: 2,
    d_plus: 1, d: 1, d_minus: 0,
    f: 1,
  },
  {
    quarter: 'W23',
    avg_gpa: 3.4,
    a_plus: 8, a: 25, a_minus: 12,
    b_plus: 6, b: 10, b_minus: 4,
    c_plus: 2, c: 2, c_minus: 1,
    d_plus: 0, d: 0, d_minus: 0,
    f: 0,
  },
]

const mockComments: CommentResult[] = [
  {
    text: 'Great professor, explains concepts clearly and is always available for office hours.',
    sentiment_score: 0.8,
    keywords: ['clear', 'available', 'helpful'],
    created_at: '2023-03-15T10:00:00Z',
  },
  {
    text: 'Very difficult grader. Exams are tricky and the curve is minimal.',
    sentiment_score: -0.5,
    keywords: ['difficult', 'tricky', 'strict'],
    created_at: '2023-06-20T14:30:00Z',
  },
]

export const handlers = [
  http.get('http://localhost:8000/courses/search', () => {
    return HttpResponse.json(mockCourses)
  }),

  http.get('http://localhost:8000/courses/:id/professors', () => {
    return HttpResponse.json(mockProfessors)
  }),

  http.get('http://localhost:8000/professors/:id/grades', () => {
    return HttpResponse.json(mockGrades)
  }),

  http.get('http://localhost:8000/professors/:id/comments', () => {
    return HttpResponse.json(mockComments)
  }),
]
