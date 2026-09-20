export interface CourseResult {
  id: number
  code: string
  title: string | null
  department: string | null
}

export interface ProfessorTag {
  name: string
  count: number
}

export interface ScheduledSection {
  quarter_code: string
  quarter_name: string | null
  enroll_code: string
  instructor_name_raw: string | null
  days: string | null
  begin_time: string | null
  end_time: string | null
  building: string | null
  room: string | null
  enrolled: number | null
  max_enroll: number | null
}

export interface QuarterInfo {
  quarter_code: string
  quarter_name: string
  next_quarter_code: string
  next_quarter_name: string
  pass1_begin: string | null
  pass2_begin: string | null
  pass3_begin: string | null
  first_day_of_classes: string | null
  last_day_of_classes: string | null
}

export interface ProfessorRanking {
  id: number
  name: string
  department: string | null
  gaucho_score: number
  gpa_factor: number | null
  quality_factor: number | null
  difficulty_factor: number | null
  sentiment_factor: number | null
  has_rmp: boolean
  rmp_quality: number | null
  rmp_difficulty: number | null
  rmp_would_take_again: number | null
  rmp_num_ratings: number | null
  mean_gpa: number | null
  std_gpa: number | null
  avg_sentiment: number | null
  match_confidence: number | null
  quarters_taught: number
  tags: ProfessorTag[]
  is_active_teacher: boolean
  recent_quarters: string[]
  teaching_next_quarter: boolean
  scheduled_sections: ScheduledSection[]
}

export interface DataFreshness {
  latest_grade_year: number | null
  latest_grade_quarter: string | null
  schedule_fetched_at: string | null
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
