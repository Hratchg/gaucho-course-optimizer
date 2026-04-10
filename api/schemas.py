from pydantic import BaseModel, ConfigDict


class CourseResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str | None = None
    department: str | None = None


class ProfessorTag(BaseModel):
    name: str
    count: int


class ProfessorRanking(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    department: str | None = None
    gaucho_score: float
    gpa_factor: float
    quality_factor: float
    difficulty_factor: float
    sentiment_factor: float
    rmp_quality: float | None = None
    rmp_difficulty: float | None = None
    rmp_would_take_again: float | None = None
    rmp_num_ratings: int | None = None
    mean_gpa: float | None = None
    std_gpa: float | None = None
    avg_sentiment: float | None = None
    match_confidence: float | None = None
    quarters_taught: int
    tags: list[ProfessorTag] = []
    is_active_teacher: bool = False
    recent_quarters: list[str] = []


class GradeQuarter(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    quarter: str
    avg_gpa: float | None = None
    a_plus: int = 0
    a: int = 0
    a_minus: int = 0
    b_plus: int = 0
    b: int = 0
    b_minus: int = 0
    c_plus: int = 0
    c: int = 0
    c_minus: int = 0
    d_plus: int = 0
    d: int = 0
    d_minus: int = 0
    f: int = 0


class CommentResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str | None = None
    sentiment_score: float | None = None
    keywords: list[str] | None = None
    created_at: str | None = None


class ScheduledSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    quarter_code: str
    quarter_name: str | None = None
    enroll_code: str
    instructor_name_raw: str | None = None
    days: str | None = None
    begin_time: str | None = None
    end_time: str | None = None
    building: str | None = None
    room: str | None = None
    enrolled: int | None = None
    max_enroll: int | None = None


class HealthResponse(BaseModel):
    status: str
