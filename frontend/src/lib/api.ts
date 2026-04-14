import type { CourseResult, ProfessorRanking, GradeQuarter, CommentResult, QuarterInfo, ScheduledSection } from '@/types/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function fetchCourses(query: string): Promise<CourseResult[]> {
  const res = await fetch(`${API_URL}/courses/search?q=${encodeURIComponent(query)}`)
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function fetchProfessors(courseId: number): Promise<ProfessorRanking[]> {
  const res = await fetch(`${API_URL}/courses/${courseId}/professors`)
  if (!res.ok) throw new Error(`Professors fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchGrades(professorId: number, courseId: number): Promise<GradeQuarter[]> {
  const res = await fetch(`${API_URL}/professors/${professorId}/grades?course_id=${courseId}`)
  if (!res.ok) throw new Error(`Grades fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchComments(professorId: number, limit: number = 5): Promise<CommentResult[]> {
  const res = await fetch(`${API_URL}/professors/${professorId}/comments?limit=${limit}`)
  if (!res.ok) throw new Error(`Comments fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchCourseSections(courseId: number): Promise<ScheduledSection[]> {
  const res = await fetch(`${API_URL}/courses/${courseId}/sections`)
  if (!res.ok) throw new Error(`Sections fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchQuarterInfo(): Promise<QuarterInfo> {
  const res = await fetch(`${API_URL}/quarters/current`)
  if (!res.ok) throw new Error(`Quarter info fetch failed: ${res.status}`)
  return res.json()
}
