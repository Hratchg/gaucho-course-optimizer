from pydantic import BaseModel, ConfigDict


class CourseResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str | None = None
    department: str | None = None


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
    keywords: list[str] = []


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


class HealthResponse(BaseModel):
    status: str
