from datetime import datetime
from sqlalchemy import Column, Integer, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True)
    name_nexus = Column(Text)
    name_rmp = Column(Text)
    rmp_id = Column(Integer, unique=True, nullable=True)
    department = Column(Text)
    match_confidence = Column(Float, nullable=True)

    grades = relationship("GradeDistribution", back_populates="professor")
    rmp_ratings = relationship("RmpRating", back_populates="professor")
    scores = relationship("GauchoScore", back_populates="professor")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=True)
    department = Column(Text)

    grades = relationship("GradeDistribution", back_populates="course")
    scores = relationship("GauchoScore", back_populates="course")


class GradeDistribution(Base):
    __tablename__ = "grade_distributions"

    id = Column(Integer, primary_key=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    quarter = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    a_plus = Column(Integer, default=0)
    a = Column(Integer, default=0)
    a_minus = Column(Integer, default=0)
    b_plus = Column(Integer, default=0)
    b = Column(Integer, default=0)
    b_minus = Column(Integer, default=0)
    c_plus = Column(Integer, default=0)
    c = Column(Integer, default=0)
    c_minus = Column(Integer, default=0)
    d_plus = Column(Integer, default=0)
    d = Column(Integer, default=0)
    d_minus = Column(Integer, default=0)
    f = Column(Integer, default=0)
    avg_gpa = Column(Float)

    professor = relationship("Professor", back_populates="grades")
    course = relationship("Course", back_populates="grades")


class RmpRating(Base):
    __tablename__ = "rmp_ratings"

    id = Column(Integer, primary_key=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    overall_quality = Column(Float)
    difficulty = Column(Float)
    would_take_again_pct = Column(Float, nullable=True)
    num_ratings = Column(Integer)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    professor = relationship("Professor", back_populates="rmp_ratings")
    comments = relationship("RmpComment", back_populates="rating")


class RmpComment(Base):
    __tablename__ = "rmp_comments"

    id = Column(Integer, primary_key=True)
    rmp_rating_id = Column(Integer, ForeignKey("rmp_ratings.id"), nullable=False)
    comment_text = Column(Text)
    sentiment_score = Column(Float, nullable=True)
    keywords = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)

    rating = relationship("RmpRating", back_populates="comments")


class GauchoScore(Base):
    __tablename__ = "gaucho_scores"

    id = Column(Integer, primary_key=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    score = Column(Float)
    weights_used = Column(JSON)
    computed_at = Column(DateTime, default=datetime.utcnow)

    professor = relationship("Professor", back_populates="scores")
    course = relationship("Course", back_populates="scores")
