# Gaucho Course Optimizer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production Streamlit dashboard that ranks UCSB professors by a configurable "Gaucho Value Score" combining grade distributions and RateMyProfessors sentiment.

**Architecture:** Monolith Python pipeline. Scrapers and ETL run on APScheduler. Streamlit reads directly from PostgreSQL via SQLAlchemy. Docker Compose orchestrates Postgres, dashboard, and scheduler as three services.

**Tech Stack:** Python 3.12+, Streamlit, PostgreSQL 16, SQLAlchemy + Alembic, curl_cffi, TheFuzz, VADER (nltk), scikit-learn, Plotly, APScheduler, Docker Compose

**Design doc:** `docs/plans/2026-02-25-gaucho-course-optimizer-design.md`
**PRD:** `docs/PRD.md`

---

## Task 1: Project Scaffolding & Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `scrapers/__init__.py`
- Create: `etl/__init__.py`
- Create: `db/__init__.py`
- Create: `dashboard/__init__.py`
- Create: `scheduler/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create `pyproject.toml`**

```toml
[project]
name = "gaucho-course-optimizer"
version = "0.1.0"
description = "UCSB course optimizer correlating grade distributions with RMP sentiment"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

**Step 2: Create `requirements.txt`**

```
sqlalchemy==2.0.*
alembic==1.13.*
psycopg2-binary==2.9.*
pandas==2.2.*
streamlit==1.41.*
plotly==5.24.*
curl_cffi==0.7.*
thefuzz[speedup]==0.22.*
nltk==3.9.*
scikit-learn==1.6.*
apscheduler==3.10.*
python-dotenv==1.0.*
pytest==8.3.*
pytest-mock==3.14.*
```

**Step 3: Create `.env.example`**

```env
DATABASE_URL=postgresql://gco:gco@localhost:5432/gco
RMP_AUTH_TOKEN=
```

**Step 4: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
*.egg-info/
dist/
.venv/
venv/
.pytest_cache/
```

**Step 5: Create all `__init__.py` files and `tests/conftest.py`**

All `__init__.py` files are empty.

`tests/conftest.py`:
```python
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco_test")

from db.models import Base
from db.connection import get_engine


@pytest.fixture(scope="session")
def engine():
    eng = get_engine()
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

**Step 6: Install dependencies**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && python -m pip install -r requirements.txt`

**Step 7: Commit**

```bash
git add pyproject.toml requirements.txt .env.example .gitignore \
  scrapers/__init__.py etl/__init__.py db/__init__.py \
  dashboard/__init__.py scheduler/__init__.py \
  tests/__init__.py tests/conftest.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

## Task 2: Database Connection Module

**Files:**
- Create: `db/connection.py`
- Create: `tests/test_db_connection.py`

**Step 1: Write the failing test**

`tests/test_db_connection.py`:
```python
from db.connection import get_engine, get_session


def test_get_engine_returns_engine():
    engine = get_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_get_session_returns_session():
    session = get_session()
    assert session is not None
    session.close()
```

**Step 2: Run test to verify it fails**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && python -m pytest tests/test_db_connection.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'db.connection'`

**Step 3: Write minimal implementation**

`db/connection.py`:
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db_connection.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add db/connection.py tests/test_db_connection.py
git commit -m "feat: add database connection module"
```

---

## Task 3: SQLAlchemy ORM Models

**Files:**
- Create: `db/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

`tests/test_models.py`:
```python
from db.models import Base, Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore


def test_all_tables_defined():
    table_names = {t.name for t in Base.metadata.sorted_tables}
    expected = {"professors", "courses", "grade_distributions", "rmp_ratings", "rmp_comments", "gaucho_scores"}
    assert expected == table_names


def test_professor_columns():
    cols = {c.name for c in Professor.__table__.columns}
    assert "name_nexus" in cols
    assert "name_rmp" in cols
    assert "rmp_id" in cols
    assert "department" in cols
    assert "match_confidence" in cols


def test_grade_distribution_has_letter_grades():
    cols = {c.name for c in GradeDistribution.__table__.columns}
    for grade in ["a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
                  "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f"]:
        assert grade in cols
    assert "avg_gpa" in cols
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`db/models.py`:
```python
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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add db/models.py tests/test_models.py
git commit -m "feat: add SQLAlchemy ORM models for all 6 tables"
```

---

## Task 4: Alembic Migration Setup

**Files:**
- Create: `alembic.ini`
- Create: `db/migrations/env.py`
- Create: `db/migrations/script.py.mako`
- Create: `db/migrations/versions/` (directory)

**Step 1: Initialize Alembic**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && python -m alembic init db/migrations`

**Step 2: Edit `alembic.ini`** — set `sqlalchemy.url` to use env var:

In `alembic.ini`, set:
```
sqlalchemy.url = postgresql://gco:gco@localhost:5432/gco
```

**Step 3: Edit `db/migrations/env.py`** — import models so Alembic sees them:

Add near top of `db/migrations/env.py`:
```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from db.models import Base
target_metadata = Base.metadata
```

Replace the existing `target_metadata = None` line with the import above.

**Step 4: Generate initial migration**

Run: `python -m alembic revision --autogenerate -m "initial schema"`
Expected: Creates a migration file in `db/migrations/versions/`

**Step 5: Apply migration (requires running Postgres)**

Run: `python -m alembic upgrade head`
Expected: All 6 tables created

**Step 6: Commit**

```bash
git add alembic.ini db/migrations/
git commit -m "chore: add Alembic migration setup with initial schema"
```

---

## Task 5: Docker Compose (Postgres)

**Files:**
- Create: `docker-compose.yml`

**Step 1: Create `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: gco
      POSTGRES_PASSWORD: gco
      POSTGRES_DB: gco
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gco"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

**Step 2: Start Postgres**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && docker compose up db -d`
Expected: Postgres container starts, healthy in ~10s

**Step 3: Apply Alembic migration**

Run: `python -m alembic upgrade head`
Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> <hash>, initial schema`

**Step 4: Verify tables exist**

Run: `docker compose exec db psql -U gco -c "\dt"`
Expected: Lists all 6 tables (professors, courses, grade_distributions, rmp_ratings, rmp_comments, gaucho_scores)

**Step 5: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add Docker Compose with Postgres 16"
```

---

## Task 6: Grade Ingestion — CSV Parser

**Files:**
- Create: `scrapers/grades_ingester.py`
- Create: `tests/test_grades_ingester.py`
- Create: `tests/fixtures/sample_grades.csv`

**Step 1: Create test fixture**

`tests/fixtures/sample_grades.csv` — a small representative sample. First, fetch the real CSV headers from the Daily Nexus repo to match the actual format:

Run: `curl -sL "https://raw.githubusercontent.com/dailynexusdata/grades-data/main/courseGrades.csv" | head -5`

Use the actual headers from the response. Create a fixture with ~10 rows mimicking the real format.

**Step 2: Write the failing test**

`tests/test_grades_ingester.py`:
```python
import os
import pandas as pd
from scrapers.grades_ingester import parse_grades_csv, compute_avg_gpa, normalize_course_code


def test_normalize_course_code():
    assert normalize_course_code("PSTAT 120A") == "PSTAT120A"
    assert normalize_course_code("CMPSC   8") == "CMPSC8"
    assert normalize_course_code("ECON 1") == "ECON1"


def test_compute_avg_gpa():
    # 10 students all got A (4.0)
    row = {"a_plus": 0, "a": 10, "a_minus": 0, "b_plus": 0, "b": 0,
           "b_minus": 0, "c_plus": 0, "c": 0, "c_minus": 0,
           "d_plus": 0, "d": 0, "d_minus": 0, "f": 0}
    assert compute_avg_gpa(row) == 4.0

    # 5 A, 5 F → avg 2.0
    row2 = {**row, "a": 5, "f": 5}
    assert compute_avg_gpa(row2) == 2.0


def test_parse_grades_csv():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_grades.csv")
    df = parse_grades_csv(fixture_path)
    assert len(df) > 0
    assert "course_code" in df.columns
    assert "avg_gpa" in df.columns
    assert "instructor" in df.columns
    # Course codes should have no spaces
    for code in df["course_code"]:
        assert " " not in code
```

**Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_grades_ingester.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write minimal implementation**

`scrapers/grades_ingester.py`:
```python
import pandas as pd

GPA_SCALE = {
    "a_plus": 4.0, "a": 4.0, "a_minus": 3.7,
    "b_plus": 3.3, "b": 3.0, "b_minus": 2.7,
    "c_plus": 2.3, "c": 2.0, "c_minus": 1.7,
    "d_plus": 1.3, "d": 1.0, "d_minus": 0.7,
    "f": 0.0,
}

GRADE_COLUMNS = list(GPA_SCALE.keys())


def normalize_course_code(code: str) -> str:
    return "".join(code.split())


def compute_avg_gpa(row: dict) -> float:
    total_points = 0.0
    total_students = 0
    for grade, points in GPA_SCALE.items():
        count = row.get(grade, 0)
        total_points += count * points
        total_students += count
    if total_students == 0:
        return 0.0
    return round(total_points / total_students, 2)


def parse_grades_csv(path: str) -> pd.DataFrame:
    """Parse the Daily Nexus courseGrades.csv.

    Adapts column names from the raw CSV to our internal schema.
    The actual CSV column names will be mapped after inspecting the real file.
    """
    df = pd.read_csv(path)

    # Normalize column names to lowercase with underscores
    df.columns = [c.strip().lower().replace(" ", "_").replace("+", "_plus").replace("-", "_minus") for c in df.columns]

    # Map columns — adapt these after inspecting real CSV headers
    # Expected raw columns: Quarter, Course, Instructor, A+, A, A-, B+, ... F
    rename_map = {}
    if "course" in df.columns:
        rename_map["course"] = "course_code_raw"
    if "instructor" not in df.columns and "professor" in df.columns:
        rename_map["professor"] = "instructor"

    df = df.rename(columns=rename_map)

    # Normalize course codes
    if "course_code_raw" in df.columns:
        df["course_code"] = df["course_code_raw"].apply(normalize_course_code)
    elif "course_code" not in df.columns:
        # Fallback: look for any column containing course info
        for col in df.columns:
            if "course" in col or "class" in col:
                df["course_code"] = df[col].apply(normalize_course_code)
                break

    # Compute avg GPA per row
    df["avg_gpa"] = df.apply(
        lambda r: compute_avg_gpa({g: r.get(g, 0) for g in GRADE_COLUMNS}), axis=1
    )

    return df


def fetch_grades_csv(url: str = None) -> pd.DataFrame:
    """Fetch courseGrades.csv from GitHub and parse it."""
    if url is None:
        url = "https://raw.githubusercontent.com/dailynexusdata/grades-data/main/courseGrades.csv"
    return parse_grades_csv(url)
```

> **Note to implementer:** After fetching the real CSV, inspect its actual column headers and adjust `parse_grades_csv` column mapping accordingly. The grade column names (A+, A, A-, etc.) may need different normalization depending on the actual CSV format.

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_grades_ingester.py -v`
Expected: PASS (3 tests). The fixture test may need the fixture CSV created first with matching column names.

**Step 6: Commit**

```bash
git add scrapers/grades_ingester.py tests/test_grades_ingester.py tests/fixtures/
git commit -m "feat: add grade CSV parser with GPA computation"
```

---

## Task 7: Grade Ingestion — Database Loader

**Files:**
- Create: `scrapers/grades_loader.py`
- Create: `tests/test_grades_loader.py`

**Step 1: Write the failing test**

`tests/test_grades_loader.py`:
```python
from db.models import Professor, Course, GradeDistribution
from scrapers.grades_loader import load_grades_to_db


def test_load_creates_professors_and_courses(db_session):
    rows = [
        {
            "instructor": "SMITH, JOHN",
            "course_code": "PSTAT120A",
            "quarter": "Fall",
            "year": 2023,
            "a_plus": 5, "a": 10, "a_minus": 8,
            "b_plus": 6, "b": 4, "b_minus": 2,
            "c_plus": 1, "c": 1, "c_minus": 0,
            "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
            "avg_gpa": 3.45,
            "department": "PSTAT",
        }
    ]
    load_grades_to_db(rows, db_session)

    profs = db_session.query(Professor).all()
    assert len(profs) == 1
    assert profs[0].name_nexus == "SMITH, JOHN"

    courses = db_session.query(Course).all()
    assert len(courses) == 1
    assert courses[0].code == "PSTAT120A"

    grades = db_session.query(GradeDistribution).all()
    assert len(grades) == 1
    assert grades[0].avg_gpa == 3.45


def test_load_is_idempotent(db_session):
    row = {
        "instructor": "DOE, JANE",
        "course_code": "CMPSC8",
        "quarter": "Winter",
        "year": 2024,
        "a_plus": 2, "a": 5, "a_minus": 3,
        "b_plus": 4, "b": 3, "b_minus": 1,
        "c_plus": 0, "c": 0, "c_minus": 0,
        "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
        "avg_gpa": 3.5,
        "department": "CMPSC",
    }
    load_grades_to_db([row], db_session)
    load_grades_to_db([row], db_session)

    grades = db_session.query(GradeDistribution).filter_by(
        quarter="Winter", year=2024
    ).all()
    # Should not duplicate
    assert len(grades) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_grades_loader.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`scrapers/grades_loader.py`:
```python
from db.models import Professor, Course, GradeDistribution

GRADE_FIELDS = [
    "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
]


def _get_or_create_professor(session, name_nexus: str, department: str) -> Professor:
    prof = session.query(Professor).filter_by(name_nexus=name_nexus).first()
    if prof is None:
        prof = Professor(name_nexus=name_nexus, department=department)
        session.add(prof)
        session.flush()
    return prof


def _get_or_create_course(session, code: str, department: str) -> Course:
    course = session.query(Course).filter_by(code=code).first()
    if course is None:
        course = Course(code=code, department=department)
        session.add(course)
        session.flush()
    return course


def load_grades_to_db(rows: list[dict], session) -> int:
    """Load parsed grade rows into the database. Returns count of new rows inserted."""
    inserted = 0
    for row in rows:
        prof = _get_or_create_professor(session, row["instructor"], row.get("department", ""))
        course = _get_or_create_course(session, row["course_code"], row.get("department", ""))

        # Check for existing record (idempotent)
        existing = session.query(GradeDistribution).filter_by(
            professor_id=prof.id,
            course_id=course.id,
            quarter=row["quarter"],
            year=row["year"],
        ).first()
        if existing:
            continue

        grade = GradeDistribution(
            professor_id=prof.id,
            course_id=course.id,
            quarter=row["quarter"],
            year=row["year"],
            avg_gpa=row.get("avg_gpa", 0.0),
            **{f: row.get(f, 0) for f in GRADE_FIELDS},
        )
        session.add(grade)
        inserted += 1

    session.commit()
    return inserted
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_grades_loader.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add scrapers/grades_loader.py tests/test_grades_loader.py
git commit -m "feat: add grade DB loader with idempotent upserts"
```

---

## Task 8: RMP Scraper — GraphQL Client

**Files:**
- Create: `scrapers/rmp_scraper.py`
- Create: `tests/test_rmp_scraper.py`
- Create: `tests/fixtures/rmp_graphql_response.json`

**Step 1: Create mock GraphQL response fixture**

`tests/fixtures/rmp_graphql_response.json`:
```json
{
  "data": {
    "search": {
      "teachers": {
        "edges": [
          {
            "node": {
              "id": "VGVhY2hlci0xMjM0",
              "legacyId": 1234,
              "firstName": "John",
              "lastName": "Smith",
              "department": "Statistics",
              "avgRating": 4.2,
              "avgDifficulty": 3.1,
              "wouldTakeAgainPercent": 85.0,
              "numRatings": 42,
              "ratings": {
                "edges": [
                  {
                    "node": {
                      "comment": "Great professor, clear lectures and fair exams.",
                      "date": "2024-01-15"
                    }
                  },
                  {
                    "node": {
                      "comment": "Tough grader but you learn a lot.",
                      "date": "2024-03-20"
                    }
                  }
                ]
              }
            }
          }
        ],
        "pageInfo": {
          "hasNextPage": false,
          "endCursor": "abc123"
        }
      }
    }
  }
}
```

**Step 2: Write the failing test**

`tests/test_rmp_scraper.py`:
```python
import json
import os
from unittest.mock import MagicMock, patch
from scrapers.rmp_scraper import parse_teacher_node, RmpScraper


def _load_fixture():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "rmp_graphql_response.json")
    with open(path) as f:
        return json.load(f)


def test_parse_teacher_node():
    fixture = _load_fixture()
    node = fixture["data"]["search"]["teachers"]["edges"][0]["node"]
    result = parse_teacher_node(node)

    assert result["legacy_id"] == 1234
    assert result["first_name"] == "John"
    assert result["last_name"] == "Smith"
    assert result["department"] == "Statistics"
    assert result["avg_rating"] == 4.2
    assert result["avg_difficulty"] == 3.1
    assert result["would_take_again_pct"] == 85.0
    assert result["num_ratings"] == 42
    assert len(result["comments"]) == 2
    assert "clear lectures" in result["comments"][0]["text"]


def test_scraper_uses_school_id():
    scraper = RmpScraper(school_id=1077)
    assert scraper.school_id == 1077
```

**Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_rmp_scraper.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write minimal implementation**

`scrapers/rmp_scraper.py`:
```python
import json
import random
import time
from typing import Optional


GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"

TEACHER_SEARCH_QUERY = """
query TeacherSearchPaginationQuery($schoolID: ID!, $cursor: String) {
  search {
    teachers(query: {schoolID: $schoolID}, first: 20, after: $cursor) {
      edges {
        node {
          id
          legacyId
          firstName
          lastName
          department
          avgRating
          avgDifficulty
          wouldTakeAgainPercent
          numRatings
          ratings(first: 20) {
            edges {
              node {
                comment
                date
              }
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""


def parse_teacher_node(node: dict) -> dict:
    """Parse a single teacher node from the GraphQL response."""
    comments = []
    for edge in node.get("ratings", {}).get("edges", []):
        comment_node = edge["node"]
        comments.append({
            "text": comment_node.get("comment", ""),
            "date": comment_node.get("date"),
        })

    return {
        "legacy_id": node["legacyId"],
        "first_name": node["firstName"],
        "last_name": node["lastName"],
        "department": node.get("department", ""),
        "avg_rating": node.get("avgRating"),
        "avg_difficulty": node.get("avgDifficulty"),
        "would_take_again_pct": node.get("wouldTakeAgainPercent"),
        "num_ratings": node.get("numRatings", 0),
        "comments": comments,
    }


class RmpScraper:
    """Scrape RateMyProfessors via their internal GraphQL endpoint."""

    def __init__(self, school_id: int = 1077, auth_token: str = ""):
        self.school_id = school_id
        self.auth_token = auth_token

    def _request(self, query: str, variables: dict) -> dict:
        """Make a GraphQL request to RMP. Uses curl_cffi for TLS fingerprint mimicry."""
        from curl_cffi import requests as cffi_requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth_token}" if self.auth_token else "",
            "Referer": "https://www.ratemyprofessors.com/",
        }
        payload = json.dumps({"query": query, "variables": variables})
        resp = cffi_requests.post(GRAPHQL_URL, data=payload, headers=headers, impersonate="chrome")
        resp.raise_for_status()
        return resp.json()

    def fetch_all_teachers(self) -> list[dict]:
        """Fetch all teachers for the configured school. Returns list of parsed teacher dicts."""
        teachers = []
        cursor: Optional[str] = None

        while True:
            variables = {"schoolID": str(self.school_id)}
            if cursor:
                variables["cursor"] = cursor

            data = self._request(TEACHER_SEARCH_QUERY, variables)
            edges = data["data"]["search"]["teachers"]["edges"]

            for edge in edges:
                teachers.append(parse_teacher_node(edge["node"]))

            page_info = data["data"]["search"]["teachers"]["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]

            # Human-like delay
            time.sleep(random.uniform(3, 7))

        return teachers
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_rmp_scraper.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add scrapers/rmp_scraper.py tests/test_rmp_scraper.py tests/fixtures/rmp_graphql_response.json
git commit -m "feat: add RMP GraphQL scraper with curl_cffi"
```

---

## Task 9: RMP Data — Database Loader

**Files:**
- Create: `scrapers/rmp_loader.py`
- Create: `tests/test_rmp_loader.py`

**Step 1: Write the failing test**

`tests/test_rmp_loader.py`:
```python
from db.models import Professor, RmpRating, RmpComment
from scrapers.rmp_loader import load_rmp_teacher_to_db


def test_load_rmp_teacher(db_session):
    teacher = {
        "legacy_id": 9999,
        "first_name": "Alice",
        "last_name": "Wong",
        "department": "Computer Science",
        "avg_rating": 4.5,
        "avg_difficulty": 2.8,
        "would_take_again_pct": 92.0,
        "num_ratings": 30,
        "comments": [
            {"text": "Best professor ever!", "date": "2024-06-01"},
            {"text": "Really helpful in office hours.", "date": "2024-05-15"},
        ],
    }
    load_rmp_teacher_to_db(teacher, db_session)

    prof = db_session.query(Professor).filter_by(rmp_id=9999).first()
    assert prof is not None
    assert prof.name_rmp == "Alice Wong"

    rating = db_session.query(RmpRating).filter_by(professor_id=prof.id).first()
    assert rating.overall_quality == 4.5
    assert rating.num_ratings == 30

    comments = db_session.query(RmpComment).filter_by(rmp_rating_id=rating.id).all()
    assert len(comments) == 2
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_rmp_loader.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

`scrapers/rmp_loader.py`:
```python
from datetime import datetime
from db.models import Professor, RmpRating, RmpComment


def load_rmp_teacher_to_db(teacher: dict, session) -> Professor:
    """Load a parsed RMP teacher dict into the database."""
    rmp_id = teacher["legacy_id"]
    name_rmp = f"{teacher['first_name']} {teacher['last_name']}"

    # Get or create professor by rmp_id
    prof = session.query(Professor).filter_by(rmp_id=rmp_id).first()
    if prof is None:
        prof = Professor(
            name_rmp=name_rmp,
            rmp_id=rmp_id,
            department=teacher.get("department", ""),
        )
        session.add(prof)
        session.flush()
    else:
        prof.name_rmp = name_rmp
        prof.department = teacher.get("department", prof.department)

    # Upsert rating
    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=teacher.get("avg_rating"),
        difficulty=teacher.get("avg_difficulty"),
        would_take_again_pct=teacher.get("would_take_again_pct"),
        num_ratings=teacher.get("num_ratings", 0),
        fetched_at=datetime.utcnow(),
    )
    session.add(rating)
    session.flush()

    # Add comments
    for comment in teacher.get("comments", []):
        if not comment.get("text"):
            continue
        rmp_comment = RmpComment(
            rmp_rating_id=rating.id,
            comment_text=comment["text"],
            created_at=datetime.fromisoformat(comment["date"]) if comment.get("date") else None,
        )
        session.add(rmp_comment)

    session.commit()
    return prof
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_rmp_loader.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scrapers/rmp_loader.py tests/test_rmp_loader.py
git commit -m "feat: add RMP data loader to database"
```

---

## Task 10: Name Matching (TheFuzz)

**Files:**
- Create: `etl/name_matcher.py`
- Create: `tests/test_name_matcher.py`

**Step 1: Write the failing test**

`tests/test_name_matcher.py`:
```python
from etl.name_matcher import normalize_nexus_name, normalize_rmp_name, match_names, match_confidence


def test_normalize_nexus_name():
    assert normalize_nexus_name("SMITH, JOHN") == "john smith"
    assert normalize_nexus_name("DE LA CRUZ, MARIA") == "maria de la cruz"
    assert normalize_nexus_name("O'BRIEN, PATRICK") == "patrick o'brien"


def test_normalize_rmp_name():
    assert normalize_rmp_name("John Smith") == "john smith"
    assert normalize_rmp_name("Dr. Maria De La Cruz") == "maria de la cruz"


def test_match_confidence_exact():
    score = match_confidence("john smith", "john smith")
    assert score == 100


def test_match_confidence_reordered():
    score = match_confidence("john smith", "smith john")
    assert score >= 85


def test_match_confidence_partial():
    score = match_confidence("john smith", "j smith")
    assert 50 < score < 100


def test_match_names_auto_links():
    nexus_names = ["SMITH, JOHN", "DOE, JANE"]
    rmp_names = ["John Smith", "Jane Doe"]
    matches = match_names(nexus_names, rmp_names)
    assert matches["SMITH, JOHN"]["rmp_name"] == "John Smith"
    assert matches["SMITH, JOHN"]["confidence"] >= 85
    assert matches["DOE, JANE"]["rmp_name"] == "Jane Doe"


def test_match_names_no_match():
    nexus_names = ["ZHANG, WEI"]
    rmp_names = ["Robert Johnson"]
    matches = match_names(nexus_names, rmp_names)
    assert "ZHANG, WEI" not in matches or matches["ZHANG, WEI"]["confidence"] < 70
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_name_matcher.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

`etl/name_matcher.py`:
```python
import re
from thefuzz import fuzz

TITLE_PATTERNS = re.compile(r"\b(dr|prof|professor|mr|ms|mrs|phd|md)\b\.?", re.IGNORECASE)


def normalize_nexus_name(name: str) -> str:
    """Convert 'LAST, FIRST' to normalized 'first last'."""
    parts = name.split(",", 1)
    if len(parts) == 2:
        last, first = parts[0].strip(), parts[1].strip()
        name = f"{first} {last}"
    name = TITLE_PATTERNS.sub("", name)
    return " ".join(name.lower().split())


def normalize_rmp_name(name: str) -> str:
    """Convert 'First Last' to normalized 'first last'."""
    name = TITLE_PATTERNS.sub("", name)
    return " ".join(name.lower().split())


def match_confidence(name_a: str, name_b: str) -> int:
    """Return fuzzy match confidence (0–100) using token_sort_ratio."""
    return fuzz.token_sort_ratio(name_a, name_b)


def match_names(
    nexus_names: list[str],
    rmp_names: list[str],
    auto_threshold: int = 85,
    review_threshold: int = 70,
) -> dict:
    """Match Nexus names to RMP names.

    Returns dict: {nexus_name: {"rmp_name": str, "confidence": int, "status": str}}
    status is "auto" (>=85), "review" (70-84), or absent if <70.
    """
    matches = {}
    normalized_rmp = [(name, normalize_rmp_name(name)) for name in rmp_names]

    for nexus_name in nexus_names:
        norm_nexus = normalize_nexus_name(nexus_name)
        best_score = 0
        best_rmp = None
        best_rmp_raw = None

        for rmp_raw, norm_rmp in normalized_rmp:
            score = match_confidence(norm_nexus, norm_rmp)
            if score > best_score:
                best_score = score
                best_rmp = norm_rmp
                best_rmp_raw = rmp_raw

        if best_score >= auto_threshold:
            matches[nexus_name] = {
                "rmp_name": best_rmp_raw,
                "confidence": best_score,
                "status": "auto",
            }
        elif best_score >= review_threshold:
            matches[nexus_name] = {
                "rmp_name": best_rmp_raw,
                "confidence": best_score,
                "status": "review",
            }

    return matches
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_name_matcher.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add etl/name_matcher.py tests/test_name_matcher.py
git commit -m "feat: add TheFuzz name matching for Nexus↔RMP reconciliation"
```

---

## Task 11: NLP Processor (VADER + TF-IDF)

**Files:**
- Create: `etl/nlp_processor.py`
- Create: `tests/test_nlp_processor.py`

**Step 1: Download VADER lexicon**

Run: `python -c "import nltk; nltk.download('vader_lexicon')"`

**Step 2: Write the failing test**

`tests/test_nlp_processor.py`:
```python
from etl.nlp_processor import analyze_sentiment, extract_keywords


def test_analyze_sentiment_positive():
    score = analyze_sentiment("Great professor, very clear and helpful!")
    assert score > 0.0


def test_analyze_sentiment_negative():
    score = analyze_sentiment("Terrible class, confusing and unfair grading.")
    assert score < 0.0


def test_analyze_sentiment_empty():
    score = analyze_sentiment("")
    assert score == 0.0


def test_extract_keywords():
    comments = [
        "The exams are really hard but fair",
        "Hard exams, but the lectures are clear",
        "Clear lectures, difficult exams, helpful office hours",
        "Office hours are great, exams are tough",
    ]
    keywords = extract_keywords(comments, top_n=5)
    assert isinstance(keywords, list)
    assert len(keywords) <= 5
    # "exams" should be a top keyword given it appears in every comment
    keyword_texts = [k.lower() for k in keywords]
    assert any("exam" in k for k in keyword_texts)
```

**Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_nlp_processor.py -v`
Expected: FAIL

**Step 4: Write minimal implementation**

`etl/nlp_processor.py`:
```python
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

_sia = None


def _get_sia():
    global _sia
    if _sia is None:
        _sia = SentimentIntensityAnalyzer()
    return _sia


def analyze_sentiment(text: str) -> float:
    """Return VADER compound sentiment score (-1 to +1). Returns 0.0 for empty text."""
    if not text or not text.strip():
        return 0.0
    return _get_sia().polarity_scores(text)["compound"]


def extract_keywords(comments: list[str], top_n: int = 8) -> list[str]:
    """Extract top-N distinctive keywords from a list of comments using TF-IDF."""
    if not comments:
        return []

    non_empty = [c for c in comments if c and c.strip()]
    if not non_empty:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=200,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform(non_empty)
    feature_names = vectorizer.get_feature_names_out()

    # Average TF-IDF across all comments
    avg_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
    top_indices = avg_scores.argsort()[-top_n:][::-1]

    return [feature_names[i] for i in top_indices]
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_nlp_processor.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add etl/nlp_processor.py tests/test_nlp_processor.py
git commit -m "feat: add NLP processor with VADER sentiment and TF-IDF keywords"
```

---

## Task 12: Gaucho Value Score Engine

**Files:**
- Create: `etl/scoring.py`
- Create: `tests/test_scoring.py`

**Step 1: Write the failing test**

`tests/test_scoring.py`:
```python
from etl.scoring import compute_gaucho_score, normalize_gpa, normalize_quality, normalize_difficulty, bayesian_adjust


def test_normalize_gpa():
    # 4.0 GPA in a dept with median 3.0 → high score
    assert normalize_gpa(4.0, dept_median=3.0, dept_max=4.0) > 0.8
    # 2.0 GPA → low score
    assert normalize_gpa(2.0, dept_median=3.0, dept_max=4.0) < 0.3


def test_normalize_quality():
    assert normalize_quality(5.0) == 1.0
    assert normalize_quality(0.0) == 0.0
    assert normalize_quality(2.5) == 0.5


def test_normalize_difficulty():
    # Low difficulty → high score (inverted)
    assert normalize_difficulty(1.0) > 0.7
    # High difficulty → low score
    assert normalize_difficulty(5.0) == 0.0


def test_bayesian_adjust():
    # Professor with many ratings → stays close to their value
    adjusted = bayesian_adjust(value=4.5, count=50, prior=3.0, min_count=5)
    assert abs(adjusted - 4.5) < 0.3

    # Professor with 1 rating → pulled heavily toward prior
    adjusted = bayesian_adjust(value=5.0, count=1, prior=3.0, min_count=5)
    assert adjusted < 4.0


def test_compute_gaucho_score_equal_weights():
    score = compute_gaucho_score(
        gpa_factor=0.8, quality_factor=0.9,
        difficulty_factor=0.7, sentiment_factor=0.6,
        weights={"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25},
    )
    expected = (0.8 * 0.25 + 0.9 * 0.25 + 0.7 * 0.25 + 0.6 * 0.25) * 100
    assert abs(score - expected) < 0.01


def test_compute_gaucho_score_custom_weights():
    # All weight on GPA
    score = compute_gaucho_score(
        gpa_factor=1.0, quality_factor=0.0,
        difficulty_factor=0.0, sentiment_factor=0.0,
        weights={"gpa": 1.0, "quality": 0.0, "difficulty": 0.0, "sentiment": 0.0},
    )
    assert score == 100.0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scoring.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

`etl/scoring.py`:
```python
def normalize_gpa(gpa: float, dept_median: float = 3.0, dept_max: float = 4.0) -> float:
    """Normalize GPA to 0–1 relative to department stats."""
    if dept_max == 0:
        return 0.0
    return max(0.0, min(1.0, gpa / dept_max))


def normalize_quality(quality: float) -> float:
    """Normalize RMP quality (0–5) to 0–1."""
    return max(0.0, min(1.0, quality / 5.0))


def normalize_difficulty(difficulty: float) -> float:
    """Normalize RMP difficulty (0–5) to 0–1, inverted (lower difficulty = higher score)."""
    return max(0.0, min(1.0, (5.0 - difficulty) / 5.0))


def bayesian_adjust(value: float, count: int, prior: float, min_count: int = 5) -> float:
    """Bayesian adjustment: pull toward prior when sample size is small."""
    return (count * value + min_count * prior) / (count + min_count)


def compute_gaucho_score(
    gpa_factor: float,
    quality_factor: float,
    difficulty_factor: float,
    sentiment_factor: float,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute Gaucho Value Score (0–100) from normalized factors and weights."""
    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}

    raw = (
        gpa_factor * weights.get("gpa", 0.25)
        + quality_factor * weights.get("quality", 0.25)
        + difficulty_factor * weights.get("difficulty", 0.25)
        + sentiment_factor * weights.get("sentiment", 0.25)
    )
    return round(max(0.0, min(100.0, raw * 100)), 2)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_scoring.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add etl/scoring.py tests/test_scoring.py
git commit -m "feat: add Gaucho Value Score engine with Bayesian weighting"
```

---

## Task 13: Streamlit Dashboard — Core Layout

**Files:**
- Create: `dashboard/app.py`
- Create: `dashboard/queries.py`

**Step 1: Create database query helpers**

`dashboard/queries.py`:
```python
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore


def search_courses(session: Session, query: str) -> list[dict]:
    """Search courses by code prefix."""
    courses = (
        session.query(Course)
        .filter(Course.code.ilike(f"%{query}%"))
        .order_by(Course.code)
        .limit(20)
        .all()
    )
    return [{"id": c.id, "code": c.code, "title": c.title, "department": c.department} for c in courses]


def get_professors_for_course(session: Session, course_id: int) -> list[dict]:
    """Get all professors who have taught a course, with their stats."""
    results = (
        session.query(
            Professor,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
            func.stddev(GradeDistribution.avg_gpa).label("std_gpa"),
            func.count(GradeDistribution.id).label("quarters_taught"),
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.course_id == course_id)
        .group_by(Professor.id)
        .all()
    )

    professors = []
    for prof, mean_gpa, std_gpa, quarters_taught in results:
        # Get latest RMP rating
        rmp = (
            session.query(RmpRating)
            .filter_by(professor_id=prof.id)
            .order_by(RmpRating.fetched_at.desc())
            .first()
        )

        # Get sentiment stats
        avg_sentiment = None
        keywords = []
        if rmp:
            sentiment_result = (
                session.query(func.avg(RmpComment.sentiment_score))
                .filter(RmpComment.rmp_rating_id == rmp.id)
                .scalar()
            )
            avg_sentiment = float(sentiment_result) if sentiment_result else None

            keyword_rows = (
                session.query(RmpComment.keywords)
                .filter(RmpComment.rmp_rating_id == rmp.id, RmpComment.keywords.isnot(None))
                .all()
            )
            for (kw,) in keyword_rows:
                if isinstance(kw, list):
                    keywords.extend(kw)

        professors.append({
            "id": prof.id,
            "name": prof.name_rmp or prof.name_nexus or "Unknown",
            "department": prof.department,
            "mean_gpa": round(float(mean_gpa), 2) if mean_gpa else None,
            "std_gpa": round(float(std_gpa), 2) if std_gpa else None,
            "quarters_taught": quarters_taught,
            "rmp_quality": rmp.overall_quality if rmp else None,
            "rmp_difficulty": rmp.difficulty if rmp else None,
            "rmp_would_take_again": rmp.would_take_again_pct if rmp else None,
            "rmp_num_ratings": rmp.num_ratings if rmp else None,
            "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
            "keywords": list(set(keywords))[:8],
            "match_confidence": prof.match_confidence,
        })

    return professors


def get_grade_history(session: Session, professor_id: int, course_id: int) -> list[dict]:
    """Get quarter-by-quarter grade history for a professor+course."""
    grades = (
        session.query(GradeDistribution)
        .filter_by(professor_id=professor_id, course_id=course_id)
        .order_by(GradeDistribution.year, GradeDistribution.quarter)
        .all()
    )
    return [
        {
            "quarter": f"{g.quarter} {g.year}",
            "avg_gpa": g.avg_gpa,
            "a_plus": g.a_plus, "a": g.a, "a_minus": g.a_minus,
            "b_plus": g.b_plus, "b": g.b, "b_minus": g.b_minus,
            "c_plus": g.c_plus, "c": g.c, "c_minus": g.c_minus,
            "d_plus": g.d_plus, "d": g.d, "d_minus": g.d_minus,
            "f": g.f,
        }
        for g in grades
    ]
```

**Step 2: Create the Streamlit app**

`dashboard/app.py`:
```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from db.connection import get_engine
from sqlalchemy.orm import sessionmaker
from dashboard.queries import search_courses, get_professors_for_course, get_grade_history
from etl.scoring import (
    compute_gaucho_score, normalize_gpa, normalize_quality,
    normalize_difficulty, bayesian_adjust,
)

st.set_page_config(page_title="Gaucho Course Optimizer", page_icon="🎓", layout="wide")
st.title("Gaucho Course Optimizer")
st.caption("Find the best professor for your UCSB courses")

# --- Sidebar: Weight Sliders ---
st.sidebar.header("Score Weights")
w_gpa = st.sidebar.slider("GPA Weight", 0.0, 1.0, 0.25, 0.05)
w_quality = st.sidebar.slider("Quality Weight", 0.0, 1.0, 0.25, 0.05)
w_difficulty = st.sidebar.slider("Difficulty Weight", 0.0, 1.0, 0.25, 0.05)
w_sentiment = st.sidebar.slider("Sentiment Weight", 0.0, 1.0, 0.25, 0.05)

weights = {"gpa": w_gpa, "quality": w_quality, "difficulty": w_difficulty, "sentiment": w_sentiment}

# Normalize weights to sum to 1
total_w = sum(weights.values())
if total_w > 0:
    weights = {k: v / total_w for k, v in weights.items()}

st.sidebar.markdown("---")
st.sidebar.header("Filters")
min_year = st.sidebar.number_input("Minimum Year", value=2015, min_value=2009, max_value=2025)

# --- Session ---
engine = get_engine()
Session = sessionmaker(bind=engine)


@st.cache_data(ttl=3600)
def _search_courses(query: str):
    with Session() as session:
        return search_courses(session, query)


@st.cache_data(ttl=3600)
def _get_professors(course_id: int):
    with Session() as session:
        return get_professors_for_course(session, course_id)


@st.cache_data(ttl=3600)
def _get_grade_history(prof_id: int, course_id: int):
    with Session() as session:
        return get_grade_history(session, prof_id, course_id)


# --- Search ---
search_query = st.text_input("Search for a course (e.g., PSTAT120A, CMPSC8)", "")

if search_query:
    courses = _search_courses(search_query.replace(" ", ""))

    if not courses:
        st.warning("No courses found. Try a different search term.")
    elif len(courses) == 1:
        selected_course = courses[0]
    else:
        options = {f"{c['code']} — {c['title'] or 'N/A'}": c for c in courses}
        selected_label = st.selectbox("Select a course:", list(options.keys()))
        selected_course = options[selected_label]

    if "selected_course" in dir() and selected_course:
        st.header(f"Professors for {selected_course['code']}")

        professors = _get_professors(selected_course["id"])

        if not professors:
            st.info("No professor data found for this course.")
        else:
            # Compute scores with current weights
            dept_gpas = [p["mean_gpa"] for p in professors if p["mean_gpa"]]
            dept_median = sorted(dept_gpas)[len(dept_gpas) // 2] if dept_gpas else 3.0

            for prof in professors:
                gpa_f = normalize_gpa(prof["mean_gpa"], dept_median) if prof["mean_gpa"] else 0.5
                qual_f = normalize_quality(prof["rmp_quality"]) if prof["rmp_quality"] else 0.5
                diff_f = normalize_difficulty(prof["rmp_difficulty"]) if prof["rmp_difficulty"] else 0.5
                sent_f = (prof["avg_sentiment"] + 1) / 2 if prof["avg_sentiment"] is not None else 0.5

                # Bayesian adjust quality if few ratings
                if prof["rmp_num_ratings"] and prof["rmp_quality"]:
                    adj_qual = bayesian_adjust(prof["rmp_quality"], prof["rmp_num_ratings"], 3.0)
                    qual_f = normalize_quality(adj_qual)

                prof["gaucho_score"] = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f, weights)

            # Sort by score descending
            professors.sort(key=lambda p: p.get("gaucho_score", 0), reverse=True)

            # Render professor cards
            for i, prof in enumerate(professors):
                score = prof.get("gaucho_score", 0)
                color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"

                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 2])

                    with col1:
                        st.metric("Gaucho Score", f"{score:.0f}/100")
                        st.caption(f"{color} {prof['name']}")
                        if prof.get("match_confidence"):
                            st.caption(f"Match: {prof['match_confidence']:.0f}%")

                    with col2:
                        st.markdown("**Grade Stats**")
                        if prof["mean_gpa"]:
                            st.write(f"Avg GPA: **{prof['mean_gpa']:.2f}** (±{prof['std_gpa'] or 0:.2f})")
                        st.write(f"Quarters taught: {prof['quarters_taught']}")

                    with col3:
                        st.markdown("**RMP Ratings**")
                        if prof["rmp_quality"]:
                            st.write(f"Quality: **{prof['rmp_quality']:.1f}**/5")
                            st.write(f"Difficulty: {prof['rmp_difficulty']:.1f}/5")
                            if prof["rmp_would_take_again"]:
                                st.write(f"Would take again: {prof['rmp_would_take_again']:.0f}%")
                        else:
                            st.write("No RMP data")

                    # Keywords
                    if prof.get("keywords"):
                        st.markdown(" ".join(f"`{kw}`" for kw in prof["keywords"][:6]))

                    # Expandable: GPA trend
                    with st.expander(f"📈 Grade history for {prof['name']}"):
                        history = _get_grade_history(prof["id"], selected_course["id"])
                        if history:
                            fig = px.line(
                                x=[h["quarter"] for h in history],
                                y=[h["avg_gpa"] for h in history],
                                labels={"x": "Quarter", "y": "Avg GPA"},
                                title=f"GPA Trend — {prof['name']}",
                            )
                            fig.update_layout(yaxis_range=[0, 4.0])
                            st.plotly_chart(fig, use_container_width=True)

                    st.divider()
```

**Step 3: Test manually**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && streamlit run dashboard/app.py`
Expected: App loads at http://localhost:8501, shows search bar and sidebar sliders. (No data yet — will populate after running scrapers.)

**Step 4: Commit**

```bash
git add dashboard/app.py dashboard/queries.py
git commit -m "feat: add Streamlit dashboard with course search and professor cards"
```

---

## Task 14: Scheduler (APScheduler)

**Files:**
- Create: `scheduler/jobs.py`
- Create: `tests/test_scheduler.py`

**Step 1: Write the failing test**

`tests/test_scheduler.py`:
```python
from scheduler.jobs import create_scheduler, NIGHTLY_JOB_ID, QUARTERLY_JOB_ID


def test_create_scheduler_has_jobs():
    sched = create_scheduler(start=False)
    job_ids = [j.id for j in sched.get_jobs()]
    assert NIGHTLY_JOB_ID in job_ids
    assert QUARTERLY_JOB_ID in job_ids
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scheduler.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

`scheduler/jobs.py`:
```python
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

NIGHTLY_JOB_ID = "nightly_rmp_refresh"
QUARTERLY_JOB_ID = "quarterly_grade_update"


def nightly_rmp_refresh():
    """Nightly job: scrape RMP → NLP → recompute scores."""
    logger.info("Starting nightly RMP refresh...")
    from scrapers.rmp_scraper import RmpScraper
    from scrapers.rmp_loader import load_rmp_teacher_to_db
    from etl.nlp_processor import analyze_sentiment, extract_keywords
    from etl.name_matcher import match_names
    from db.connection import get_session

    session = get_session()
    try:
        scraper = RmpScraper()
        teachers = scraper.fetch_all_teachers()
        for teacher in teachers:
            load_rmp_teacher_to_db(teacher, session)
        logger.info(f"Loaded {len(teachers)} teachers from RMP")
    except Exception as e:
        logger.error(f"Nightly RMP refresh failed: {e}")
    finally:
        session.close()


def quarterly_grade_update():
    """Quarterly job: fetch grades CSV → load → match names → recompute scores."""
    logger.info("Starting quarterly grade update...")
    from scrapers.grades_ingester import fetch_grades_csv
    from scrapers.grades_loader import load_grades_to_db
    from db.connection import get_session

    session = get_session()
    try:
        df = fetch_grades_csv()
        rows = df.to_dict("records")
        inserted = load_grades_to_db(rows, session)
        logger.info(f"Loaded {inserted} new grade records")
    except Exception as e:
        logger.error(f"Quarterly grade update failed: {e}")
    finally:
        session.close()


def create_scheduler(start: bool = True) -> BlockingScheduler:
    """Create and optionally start the APScheduler."""
    scheduler = BlockingScheduler()

    scheduler.add_job(
        nightly_rmp_refresh,
        trigger=CronTrigger(hour=2, minute=0),
        id=NIGHTLY_JOB_ID,
        replace_existing=True,
    )

    scheduler.add_job(
        quarterly_grade_update,
        trigger=CronTrigger(month="1,4,7,10", day=15, hour=3),
        id=QUARTERLY_JOB_ID,
        replace_existing=True,
    )

    if start:
        logger.info("Scheduler started.")
        scheduler.start()

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_scheduler()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scheduler/jobs.py tests/test_scheduler.py
git commit -m "feat: add APScheduler with nightly RMP and quarterly grade jobs"
```

---

## Task 15: Docker Compose — Full Stack

**Files:**
- Modify: `docker-compose.yml`
- Create: `Dockerfile`

**Step 1: Create Dockerfile**

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('vader_lexicon')"

COPY . .
```

**Step 2: Update `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: gco
      POSTGRES_PASSWORD: gco
      POSTGRES_DB: gco
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gco"]
      interval: 5s
      timeout: 5s
      retries: 5

  dashboard:
    build: .
    command: streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0
    ports:
      - "8501:8501"
    environment:
      DATABASE_URL: postgresql://gco:gco@db:5432/gco
    depends_on:
      db:
        condition: service_healthy

  scheduler:
    build: .
    command: python -m scheduler.jobs
    environment:
      DATABASE_URL: postgresql://gco:gco@db:5432/gco
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```

**Step 3: Test full stack**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && docker compose up --build`
Expected: All 3 services start. Dashboard accessible at http://localhost:8501.

**Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add full-stack Docker Compose with dashboard and scheduler"
```

---

## Task 16: Integration Test — End-to-End Pipeline

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

`tests/test_integration.py`:
```python
"""End-to-end integration test: CSV → DB → name match → NLP → score."""
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore
from scrapers.grades_loader import load_grades_to_db
from scrapers.rmp_loader import load_rmp_teacher_to_db
from etl.name_matcher import match_names
from etl.nlp_processor import analyze_sentiment, extract_keywords
from etl.scoring import compute_gaucho_score, normalize_gpa, normalize_quality, normalize_difficulty


def test_full_pipeline(db_session):
    # 1. Load grades
    grade_rows = [
        {
            "instructor": "SMITH, JOHN",
            "course_code": "PSTAT120A",
            "quarter": "Fall", "year": 2023,
            "a_plus": 3, "a": 12, "a_minus": 8,
            "b_plus": 5, "b": 4, "b_minus": 2,
            "c_plus": 1, "c": 0, "c_minus": 0,
            "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
            "avg_gpa": 3.52, "department": "PSTAT",
        },
    ]
    load_grades_to_db(grade_rows, db_session)

    # 2. Load RMP data
    teacher = {
        "legacy_id": 5555,
        "first_name": "John",
        "last_name": "Smith",
        "department": "Statistics",
        "avg_rating": 4.2,
        "avg_difficulty": 3.1,
        "would_take_again_pct": 85.0,
        "num_ratings": 42,
        "comments": [
            {"text": "Great professor, clear lectures!", "date": "2024-01-15"},
            {"text": "Tough grader but you learn a lot.", "date": "2024-03-20"},
        ],
    }
    load_rmp_teacher_to_db(teacher, db_session)

    # 3. Name matching
    nexus_names = ["SMITH, JOHN"]
    rmp_names = ["John Smith"]
    matches = match_names(nexus_names, rmp_names)
    assert "SMITH, JOHN" in matches
    assert matches["SMITH, JOHN"]["confidence"] >= 85

    # 4. NLP
    sentiment_1 = analyze_sentiment("Great professor, clear lectures!")
    assert sentiment_1 > 0
    keywords = extract_keywords(["Great professor, clear lectures!", "Tough grader but you learn a lot."])
    assert len(keywords) > 0

    # 5. Scoring
    score = compute_gaucho_score(
        gpa_factor=normalize_gpa(3.52),
        quality_factor=normalize_quality(4.2),
        difficulty_factor=normalize_difficulty(3.1),
        sentiment_factor=(sentiment_1 + 1) / 2,
    )
    assert 0 <= score <= 100
    assert score > 50  # Should be a decent professor
```

**Step 2: Run integration test**

Run: `python -m pytest tests/test_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test for full pipeline"
```

---

## Task 17: Update README and PRD

**Files:**
- Modify: `README.md` — add setup instructions for running locally without Docker
- Modify: `docs/PRD.md` — update status to reflect implementation progress

**Step 1: Add local dev instructions to README**

Add a "Local Development" section:
```markdown
## Local Development

```bash
# Install dependencies
python -m pip install -r requirements.txt
python -c "import nltk; nltk.download('vader_lexicon')"

# Start Postgres (via Docker)
docker compose up db -d

# Run migrations
python -m alembic upgrade head

# Ingest grade data
python -c "from scrapers.grades_ingester import fetch_grades_csv; from scrapers.grades_loader import load_grades_to_db; from db.connection import get_session; s = get_session(); df = fetch_grades_csv(); load_grades_to_db(df.to_dict('records'), s)"

# Launch dashboard
streamlit run dashboard/app.py

# Run tests
python -m pytest tests/ -v
```
```

**Step 2: Commit**

```bash
git add README.md docs/PRD.md
git commit -m "docs: update README with local dev instructions"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Project scaffolding | conftest.py |
| 2 | DB connection | 2 tests |
| 3 | ORM models | 3 tests |
| 4 | Alembic migrations | — |
| 5 | Docker Compose (Postgres) | — |
| 6 | Grade CSV parser | 3 tests |
| 7 | Grade DB loader | 2 tests |
| 8 | RMP GraphQL scraper | 2 tests |
| 9 | RMP DB loader | 1 test |
| 10 | Name matching | 6 tests |
| 11 | NLP processor | 4 tests |
| 12 | Scoring engine | 6 tests |
| 13 | Streamlit dashboard | manual |
| 14 | APScheduler | 1 test |
| 15 | Full Docker Compose | manual |
| 16 | Integration test | 1 test |
| 17 | Docs update | — |

**Total: 17 tasks, ~31 automated tests, 17 commits**
