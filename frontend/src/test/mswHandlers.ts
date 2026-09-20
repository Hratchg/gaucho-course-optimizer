import { http, HttpResponse } from 'msw'
import type { CourseResult, ProfessorRanking, GradeQuarter, CommentResult, QuarterInfo } from '@/types/api'

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
    tags: [
      { name: 'Clear Explanations', count: 12 },
      { name: 'Helpful', count: 8 },
      { name: 'Engaging', count: 5 },
    ],
    is_active_teacher: true,
    recent_quarters: ['Fall 2024', 'Winter 2024', 'Spring 2024'],
    teaching_next_quarter: true,
    scheduled_sections: [
      {
        quarter_code: '20262',
        quarter_name: 'Spring 2026',
        enroll_code: '12345',
        instructor_name_raw: 'SMITH A',
        days: 'MWF',
        begin_time: '10:00',
        end_time: '10:50',
        building: 'Phelps',
        room: '1260',
        enrolled: 42,
        max_enroll: 120,
      },
    ],
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
    tags: [
      { name: 'Fair Tests', count: 4 },
    ],
    is_active_teacher: false,
    recent_quarters: ['Winter 2023'],
    teaching_next_quarter: false,
    scheduled_sections: [],
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

const mockQuarterInfo: QuarterInfo = {
  quarter_code: '20262',
  quarter_name: 'Spring 2026',
  next_quarter_code: '20263',
  next_quarter_name: 'Summer 2026',
  pass1_begin: '2026-05-01T09:00:00',
  pass2_begin: '2026-05-08T09:00:00',
  pass3_begin: '2026-05-15T09:00:00',
  first_day_of_classes: '2026-06-22',
  last_day_of_classes: '2026-07-31',
}

export const handlers = [
  http.get('http://localhost:8001/courses/search', () => {
    return HttpResponse.json(mockCourses)
  }),

  http.get('http://localhost:8001/courses/:id/professors', () => {
    return HttpResponse.json(mockProfessors)
  }),

  http.get('http://localhost:8001/professors/:id/grades', () => {
    return HttpResponse.json(mockGrades)
  }),

  http.get('http://localhost:8001/professors/:id/comments', () => {
    return HttpResponse.json(mockComments)
  }),

  http.get('http://localhost:8001/courses/:id/sections', () => {
    return HttpResponse.json(mockProfessors[0].scheduled_sections)
  }),

  http.get('http://localhost:8001/quarters/current', () => {
    return HttpResponse.json(mockQuarterInfo)
  }),
]
