export interface CourseResult {
  id: number
  code: string
  title: string | null
  department: string | null
}

export interface ProfessorRanking {
  id: number
  name: string
  department: string | null
  gaucho_score: number
  gpa_factor: number
  quality_factor: number
  difficulty_factor: number
  sentiment_factor: number
  rmp_quality: number | null
  rmp_difficulty: number | null
  rmp_would_take_again: number | null
  rmp_num_ratings: number | null
  mean_gpa: number | null
  std_gpa: number | null
  avg_sentiment: number | null
  match_confidence: number | null
  quarters_taught: number
  keywords: string[]
}

export interface GradeQuarter {
  quarter: string
  avg_gpa: number | null
  a_plus: number; a: number; a_minus: number
  b_plus: number; b: number; b_minus: number
  c_plus: number; c: number; c_minus: number
  d_plus: number; d: number; d_minus: number
  f: number
}

export interface CommentResult {
  text: string | null
  sentiment_score: number | null
  keywords: string[] | null
  created_at: string | null
}
