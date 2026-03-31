# Testing Patterns

**Analysis Date:** 2026-03-30

## Test Framework

**Runner:**
- `pytest` 8.3–9.x
- Config: `pyproject.toml`

**Assertion Library:**
- `pytest` built-in assertions (no external library)

**Mocking:**
- `pytest-mock` 3.14–3.x (provides `mocker` fixture)

**Run Commands:**
```bash
pytest tests/                      # Run all tests
pytest tests/test_name_matcher.py  # Run specific test file
pytest -v                          # Verbose output
pytest -k "test_normalize"         # Run tests matching pattern
```

**Coverage:**
- No coverage tool explicitly configured in `pyproject.toml`
- No `.coveragerc` or coverage settings detected

## Test File Organization

**Location:**
- Separate directory: all tests in `tests/` directory parallel to source (`db/`, `etl/`, `scrapers/`, etc.)

**Naming:**
- Pattern: `test_*.py` (test file prefix)
- 21 test files total: `test_name_matcher.py`, `test_scoring.py`, `test_integration.py`, etc.

**File structure:**
```
tests/
├── conftest.py                    # Shared fixtures (db_session, engine)
├── test_active_professors.py      # Unit tests
├── test_batch_nlp.py
├── test_batch_scoring.py
├── test_db_connection.py
├── test_enhanced_matcher.py       # Large integration tests (152 lines)
├── test_integration.py            # End-to-end pipeline tests (64 lines)
├── test_name_matcher.py           # Pure function tests (43 lines)
├── test_scoring.py                # Pure function tests (51 lines)
└── ... (15 more test files)
```

## Test Structure

**Test organization: function-based with pytest conventions**

```python
# Pattern from test_name_matcher.py
from etl.name_matcher import normalize_nexus_name, normalize_rmp_name, match_names

def test_normalize_nexus_name():
    assert normalize_nexus_name("SMITH, JOHN") == "john smith"
    assert normalize_nexus_name("DE LA CRUZ, MARIA") == "maria de la cruz"

def test_normalize_rmp_name():
    assert normalize_rmp_name("John Smith") == "john smith"
    assert normalize_rmp_name("Dr. Maria De La Cruz") == "maria de la cruz"

def test_match_confidence_exact():
    score = match_confidence("john smith", "john smith")
    assert score == 100
```

**Naming convention:**
- Functions prefixed `test_` (required by pytest)
- Descriptive names: `test_normalize_nexus_name`, `test_match_confidence_exact`, `test_process_all_comments_fills_sentiment`
- One logical assertion group per test (sometimes multiple asserts if testing one behavior)

**Setup/teardown:**
- **Fixture-based**: Pytest fixtures for common setup
- **No explicit teardown**: Handled by fixture scope (session, function)
- **Database transactions**: SAVEPOINT pattern for test isolation

## Database Test Fixtures

**Core fixture: `db_session` (function-scoped)**

From `tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def engine():
    eng = get_engine()
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)

@pytest.fixture
def db_session(engine):
    """Create a transactional session that rolls back after each test.

    Uses the nested-transaction (SAVEPOINT) pattern so that even explicit
    session.commit() calls inside tests are contained and rolled back.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Start a SAVEPOINT
    nested = connection.begin_nested()

    # After every commit, re-open a new SAVEPOINT
    from sqlalchemy import event

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

**Key feature:** SAVEPOINT allows tests to call `session.commit()` (as production code does) while keeping all changes isolated and rolled back after each test. No cleanup code needed per test.

**Database URL:** Test database configured via environment variable
```python
os.environ.setdefault("DATABASE_URL", "postgresql://gco:gco@localhost:5432/gco_test")
```

## Test Types

### Unit Tests

**Scope:** Pure functions with no database or I/O

**Examples:**
- `test_name_matcher.py` — Normalization and matching logic (43 lines)
- `test_scoring.py` — Normalization and Bayesian adjustment (51 lines)
- `test_name_utils.py` — Parsing helpers (83 lines)

**Pattern:**
```python
def test_normalize_quality():
    assert normalize_quality(5.0) == 1.0
    assert normalize_quality(0.0) == 0.0
    assert normalize_quality(2.5) == 0.5

def test_bayesian_adjust():
    adjusted = bayesian_adjust(value=4.5, count=50, prior=3.0, min_count=5)
    assert abs(adjusted - 4.5) < 0.3
```

### Integration Tests

**Scope:** Functions that interact with database; batch operations

**Examples:**
- `test_batch_scoring.py` — `compute_all_scores()` with fixtures (56 lines)
- `test_batch_nlp.py` — `process_all_comments()` with sentiment + keywords (71 lines)
- `test_rmp_loader.py` — Database loading functions (75 lines)
- `test_enhanced_matcher.py` — Multi-pass professor matching (152 lines)

**Pattern:**
```python
def test_compute_all_scores_creates_gaucho_scores(db_session):
    """compute_all_scores creates GauchoScore for matched professors."""
    prof = Professor(name_nexus="SCORE, TEST", rmp_id=1234, match_confidence=95, department="CS")
    db_session.add(prof)
    db_session.flush()

    course = Course(code="CS300", department="CS")
    db_session.add(course)
    db_session.flush()

    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.7,
    ))

    db_session.add(RmpRating(
        professor_id=prof.id,
        overall_quality=4.2, difficulty=3.0,
        would_take_again_pct=85.0, num_ratings=40,
    ))
    db_session.commit()

    stats = compute_all_scores(db_session)

    scores = db_session.query(GauchoScore).filter_by(professor_id=prof.id).all()
    assert len(scores) == 1
    assert 0 <= scores[0].score <= 100
    assert stats["computed"] >= 1
```

### End-to-End Tests

**Scope:** Full pipeline from CSV load through NLP to scoring

**File:** `test_integration.py` (64 lines)

**Pattern:**
```python
def test_full_pipeline(db_session):
    # 1. Load grades
    grade_rows = [...]
    load_grades_to_db(grade_rows, db_session)

    # 2. Load RMP data
    teacher = {...}
    load_rmp_teacher_to_db(teacher, db_session)

    # 3. Name matching
    matches = match_names(nexus_names, rmp_names)
    assert matches["SMITH, JOHN"]["confidence"] >= 85

    # 4. NLP sentiment
    sentiment = analyze_sentiment("Great professor!")
    assert sentiment > 0

    # 5. Scoring
    score = compute_gaucho_score(...)
    assert 0 <= score <= 100
    assert score > 50
```

**Test count by type (approximate):**

| Type | Location | Count |
|------|----------|-------|
| Unit | `test_name_matcher.py`, `test_scoring.py`, `test_name_utils.py`, `test_department_mapper.py` | 80+ |
| Integration | `test_batch_scoring.py`, `test_batch_nlp.py`, `test_rmp_loader.py`, `test_enhanced_matcher.py`, `test_grades_loader.py`, `test_dashboard_queries.py` | 30+ |
| E2E | `test_integration.py` | 1 main test |

Total across 21 test files: ~1200 lines of test code

## Test Data

**Fixtures approach:** Direct object instantiation within test functions

```python
# From test_batch_nlp.py
prof = Professor(name_nexus="NLP, TEST", department="CS")
db_session.add(prof)
db_session.flush()

rating = RmpRating(
    professor_id=prof.id,
    overall_quality=4.0, difficulty=3.0,
    num_ratings=10,
)
db_session.add(rating)

comments = [
    RmpComment(rmp_rating_id=rating.id, comment_text="Amazing professor!"),
    RmpComment(rmp_rating_id=rating.id, comment_text="Terrible class."),
]
db_session.add_all(comments)
db_session.commit()
```

**No separate factory classes or fixture builders** — Tests create minimal data inline

## Assertion Patterns

**Standard pytest assertions:**

```python
# Equality
assert normalize_nexus_name("SMITH, JOHN") == "john smith"

# Comparison
assert score >= 85
assert 0 <= score <= 100

# Boolean
assert prof is not None
assert len(scores) == 1

# Truth/falsy
assert sentiment > 0
assert sentiment < 0

# Exceptions
with pytest.raises(ValueError, match="already linked"):
    load_rmp_teacher_to_db(...)

# Containment
assert "john smith" in matches
```

## Mocking

**Framework:** `pytest-mock` (provides `mocker` fixture)

**Not heavily used in this codebase** — Most tests use real database (with SAVEPOINT isolation)

**Where mocking could apply (but doesn't):**
- Scraper tests (`test_rmp_scraper.py`) test real HTTP calls or use fixture responses
- Database tests use real in-memory/test PostgreSQL, not mocked

## Common Testing Patterns

### Database state verification

```python
def test_load_rmp_teacher(db_session):
    teacher = {...}
    load_rmp_teacher_to_db(teacher, db_session)

    prof = db_session.query(Professor).filter_by(rmp_id=9999).first()
    assert prof is not None
    assert prof.name_rmp == "Alice Wong"

    rating = db_session.query(RmpRating).filter_by(professor_id=prof.id).first()
    assert rating.overall_quality == 4.5
```

### Batch operation stats

```python
def test_process_all_comments_fills_sentiment(db_session):
    # Setup: create comments without sentiment
    stats = process_all_comments(db_session)

    # Verify results
    assert stats["processed"] == 2
    db_session.refresh(c1)
    assert c1.sentiment_score is not None
    assert c1.sentiment_score > 0  # positive
```

### Negative case testing

```python
def test_compute_all_scores_skips_unmatched(db_session):
    prof = Professor(name_nexus="NORP, MATCH", department="MATH")
    # ... create grade data but NO RMP data ...

    stats = compute_all_scores(db_session)

    scores = db_session.query(GauchoScore).filter_by(professor_id=prof.id).all()
    assert len(scores) == 0  # Should skip
```

### Precondition validation

```python
def test_load_rmp_teacher_links_nexus_professor(db_session):
    # Setup: create Nexus professor
    load_grades_to_db([...], db_session)
    nexus_prof = db_session.query(Professor).filter_by(name_nexus="CONRAD, PHILL").first()

    # Link RMP data to existing professor
    teacher = {...}
    load_rmp_teacher_to_db(teacher, db_session, nexus_professor_id=nexus_prof.id, match_confidence=95)

    # Verify: updated existing professor, didn't create duplicate
    db_session.refresh(nexus_prof)
    assert nexus_prof.rmp_id == 7777
    assert nexus_prof.match_confidence == 95
```

## Test Environment

**Database:**
- Test database: `gco_test` PostgreSQL instance
- Configured via `DATABASE_URL` env var in `conftest.py`
- **Pre-test setup:** `Base.metadata.create_all(engine)` creates schema
- **Post-test cleanup:** `Base.metadata.drop_all(engine)` destroys schema

**Test requirements:** `requirements-dev.txt` includes test dependencies
```
-r requirements.txt
pytest>=8.3,<10
pytest-mock>=3.14,<4
```

## Notable Patterns

### SAVEPOINT Pattern for Clean Rollback

The `db_session` fixture uses PostgreSQL SAVEPOINT (nested transactions) to enable:
- Tests can call `session.commit()` (as production code does)
- Changes are isolated within a SAVEPOINT
- After test, outer transaction rolled back (no manual cleanup needed)

This avoids the common problem of mocking commits or using `session.rollback()` between tests.

### Minimal Fixtures, Maximum Clarity

Tests build data inline rather than using factory classes:
```python
# Inline (preferred in this codebase)
prof = Professor(name_nexus="TEST", department="CS")
db_session.add(prof)

# Not used: factory pattern with Factory Boy
```

Benefits: Test code is self-documenting; dependencies explicit

### One Assertion Per Scenario

Tests group related assertions but avoid "test everything in one test":
```python
# Good: Separate test per behavior
def test_normalize_quality():
    assert normalize_quality(5.0) == 1.0

def test_compute_gaucho_score_equal_weights():
    assert abs(score - expected) < 0.01

# Bad: Lumped together
def test_all_scoring():
    assert normalize_quality(5.0) == 1.0
    # ... 30 more assertions ...
```

---

*Testing analysis: 2026-03-30*
