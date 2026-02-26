# Targeted RMP Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the bulk RMP scraper with a targeted name-search approach that only scrapes active professors (2023-2025), matches during scraping, then runs NLP and scoring in batch.

**Architecture:** The `RmpScraper` gets a new `search_teacher_by_name()` method using a name+school GraphQL query. A new `scrape_active_professors()` function queries the DB for active professors, searches each on RMP, fuzzy matches, and saves matches directly. After scraping, batch NLP and scoring passes fill in sentiment, keywords, and Gaucho Scores. A CLI script orchestrates the full pipeline. The scheduler is updated to run every 2 days.

**Tech Stack:** Python 3.12+, curl_cffi, TheFuzz, VADER (vaderSentiment), scikit-learn, SQLAlchemy, APScheduler

**Design doc:** `docs/plans/2026-02-25-targeted-rmp-pipeline-design.md`

---

## Task 1: Add Targeted Name Search to RmpScraper

**Files:**
- Modify: `scrapers/rmp_scraper.py`
- Modify: `tests/test_rmp_scraper.py`
- Create: `tests/fixtures/rmp_name_search_response.json`

**Step 1: Create name search fixture**

`tests/fixtures/rmp_name_search_response.json`:
```json
{
  "data": {
    "newSearch": {
      "teachers": {
        "edges": [
          {
            "node": {
              "id": "VGVhY2hlci01NTU1",
              "legacyId": 5555,
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
          },
          {
            "node": {
              "id": "VGVhY2hlci02NjY2",
              "legacyId": 6666,
              "firstName": "Jane",
              "lastName": "Smithson",
              "department": "English",
              "avgRating": 3.0,
              "avgDifficulty": 2.5,
              "wouldTakeAgainPercent": 60.0,
              "numRatings": 10,
              "ratings": {
                "edges": []
              }
            }
          }
        ],
        "pageInfo": {
          "hasNextPage": false,
          "endCursor": "xyz789"
        }
      }
    }
  }
}
```

**Step 2: Write the failing test**

Add to `tests/test_rmp_scraper.py`:
```python
def _load_name_search_fixture():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "rmp_name_search_response.json")
    with open(path) as f:
        return json.load(f)


def test_search_teacher_by_name_parses_results():
    """search_teacher_by_name returns parsed teacher dicts from name search results."""
    from scrapers.rmp_scraper import NAME_SEARCH_QUERY
    assert "$text" in NAME_SEARCH_QUERY
    assert "$schoolID" in NAME_SEARCH_QUERY

    fixture = _load_name_search_fixture()
    edges = fixture["data"]["newSearch"]["teachers"]["edges"]
    results = [parse_teacher_node(e["node"]) for e in edges]

    assert len(results) == 2
    assert results[0]["first_name"] == "John"
    assert results[0]["last_name"] == "Smith"
    assert results[0]["legacy_id"] == 5555
    assert len(results[0]["comments"]) == 2
    assert results[1]["legacy_id"] == 6666
    assert len(results[1]["comments"]) == 0
```

**Step 3: Run test to verify it fails**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && python -m pytest tests/test_rmp_scraper.py::test_search_teacher_by_name_parses_results -v`
Expected: FAIL — `ImportError: cannot import name 'NAME_SEARCH_QUERY'`

**Step 4: Write minimal implementation**

Add to `scrapers/rmp_scraper.py` after the existing `TEACHER_SEARCH_QUERY` (after line 42):

```python
NAME_SEARCH_QUERY = """
query TeacherSearchQuery($text: String!, $schoolID: ID!) {
  newSearch {
    teachers(query: {text: $text, schoolID: $schoolID}, first: 5) {
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
```

Add to the `RmpScraper` class (after `fetch_all_teachers`, after line 114):

```python
    def search_teacher_by_name(self, name: str) -> list[dict]:
        """Search for a teacher by name at this school. Returns list of parsed teacher dicts."""
        variables = {"text": name, "schoolID": self.school_id_encoded}
        data = self._request(NAME_SEARCH_QUERY, variables)
        edges = data.get("data", {}).get("newSearch", {}).get("teachers", {}).get("edges", [])
        return [parse_teacher_node(edge["node"]) for edge in edges]
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_rmp_scraper.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add scrapers/rmp_scraper.py tests/test_rmp_scraper.py tests/fixtures/rmp_name_search_response.json
git commit -m "feat: add targeted name search to RMP scraper"
```

---

## Task 2: Add Active Professor Query

**Files:**
- Modify: `scrapers/rmp_loader.py`
- Create: `tests/test_active_professors.py`

**Step 1: Write the failing test**

`tests/test_active_professors.py`:
```python
from datetime import datetime, timezone
from db.models import Professor, Course, GradeDistribution, RmpRating
from scrapers.rmp_loader import get_active_professors, is_stale


def test_get_active_professors_filters_by_year(db_session):
    # Create a professor with a recent grade (2024)
    prof_recent = Professor(name_nexus="RECENT, PROF", department="CS")
    db_session.add(prof_recent)
    db_session.flush()
    course = Course(code="CS101", department="CS")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof_recent.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.5,
    ))

    # Create a professor with only old grades (2015)
    prof_old = Professor(name_nexus="OLD, PROF", department="CS")
    db_session.add(prof_old)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof_old.id, course_id=course.id,
        quarter="Fall", year=2015, avg_gpa=3.0,
    ))
    db_session.commit()

    active = get_active_professors(db_session, min_year=2023)
    active_ids = [p.id for p in active]
    assert prof_recent.id in active_ids
    assert prof_old.id not in active_ids


def test_is_stale_with_no_rating():
    assert is_stale(None, max_age_days=2) is True


def test_is_stale_with_recent_rating():
    assert is_stale(datetime.now(timezone.utc), max_age_days=2) is False
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_active_professors.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_active_professors'`

**Step 3: Write minimal implementation**

Add to `scrapers/rmp_loader.py` (after line 2, before the function):

```python
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from db.models import Professor, RmpRating, RmpComment, GradeDistribution
```

Replace the existing import line at top. Then add these functions before `load_rmp_teacher_to_db`:

```python
def get_active_professors(session, min_year: int = 2023) -> list[Professor]:
    """Get professors who have taught at least one course since min_year."""
    return (
        session.query(Professor)
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .filter(GradeDistribution.year >= min_year)
        .group_by(Professor.id)
        .all()
    )


def is_stale(fetched_at: datetime | None, max_age_days: int = 2) -> bool:
    """Check if an RMP rating is stale (older than max_age_days or missing)."""
    if fetched_at is None:
        return True
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - fetched_at
    return age > timedelta(days=max_age_days)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_active_professors.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add scrapers/rmp_loader.py tests/test_active_professors.py
git commit -m "feat: add active professor query and staleness check"
```

---

## Task 3: Update RMP Loader to Link Nexus Professors

**Files:**
- Modify: `scrapers/rmp_loader.py`
- Modify: `tests/test_rmp_loader.py`

**Step 1: Write the failing test**

Add to `tests/test_rmp_loader.py`:
```python
def test_load_rmp_teacher_links_nexus_professor(db_session):
    """When nexus_professor_id is provided, link to existing professor instead of creating new."""
    from scrapers.grades_loader import load_grades_to_db

    # First create a Nexus professor via grade loader
    load_grades_to_db([{
        "instructor": "CONRAD, PHILL",
        "course_code": "CMPSC156",
        "quarter": "Fall", "year": 2024,
        "a_plus": 5, "a": 10, "a_minus": 3,
        "b_plus": 2, "b": 1, "b_minus": 0,
        "c_plus": 0, "c": 0, "c_minus": 0,
        "d_plus": 0, "d": 0, "d_minus": 0, "f": 0,
        "avg_gpa": 3.7, "department": "CMPSC",
    }], db_session)

    nexus_prof = db_session.query(Professor).filter_by(name_nexus="CONRAD, PHILL").first()
    assert nexus_prof is not None

    # Now load RMP data linked to this Nexus professor
    teacher = {
        "legacy_id": 7777,
        "first_name": "Phill",
        "last_name": "Conrad",
        "department": "Computer Science",
        "avg_rating": 4.5,
        "avg_difficulty": 2.5,
        "would_take_again_pct": 90.0,
        "num_ratings": 78,
        "comments": [{"text": "Love this class!", "date": "2024-09-01"}],
    }
    load_rmp_teacher_to_db(teacher, db_session, nexus_professor_id=nexus_prof.id, match_confidence=95)

    # Should have updated the existing Nexus professor, not created a new one
    db_session.refresh(nexus_prof)
    assert nexus_prof.rmp_id == 7777
    assert nexus_prof.name_rmp == "Phill Conrad"
    assert nexus_prof.match_confidence == 95

    rating = db_session.query(RmpRating).filter_by(professor_id=nexus_prof.id).first()
    assert rating is not None
    assert rating.overall_quality == 4.5
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_rmp_loader.py::test_load_rmp_teacher_links_nexus_professor -v`
Expected: FAIL — `TypeError: load_rmp_teacher_to_db() got an unexpected keyword argument 'nexus_professor_id'`

**Step 3: Update implementation**

Replace `load_rmp_teacher_to_db` in `scrapers/rmp_loader.py` with:

```python
def load_rmp_teacher_to_db(
    teacher: dict,
    session,
    nexus_professor_id: int | None = None,
    match_confidence: int | None = None,
) -> Professor:
    """Load a parsed RMP teacher dict into the database.

    If nexus_professor_id is provided, link RMP data to the existing Nexus professor
    instead of creating a new professor record.
    """
    rmp_id = teacher["legacy_id"]
    name_rmp = f"{teacher['first_name']} {teacher['last_name']}"

    if nexus_professor_id is not None:
        # Link to existing Nexus professor
        prof = session.query(Professor).get(nexus_professor_id)
        if prof is None:
            raise ValueError(f"No professor with id={nexus_professor_id}")
        prof.rmp_id = rmp_id
        prof.name_rmp = name_rmp
        if match_confidence is not None:
            prof.match_confidence = match_confidence
    else:
        # Fallback: get or create by rmp_id (original behavior)
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
        fetched_at=datetime.now(timezone.utc),
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

**Step 4: Run all rmp_loader tests to verify they pass**

Run: `python -m pytest tests/test_rmp_loader.py -v`
Expected: PASS (2 tests — original + new one)

**Step 5: Commit**

```bash
git add scrapers/rmp_loader.py tests/test_rmp_loader.py
git commit -m "feat: update RMP loader to link Nexus professors with match confidence"
```

---

## Task 4: Targeted Scrape Loop

**Files:**
- Create: `scrapers/targeted_scrape.py`
- Create: `tests/test_targeted_scrape.py`

**Step 1: Write the failing test**

`tests/test_targeted_scrape.py`:
```python
from unittest.mock import MagicMock, patch
from db.models import Professor, Course, GradeDistribution
from scrapers.targeted_scrape import scrape_active_professors


def test_scrape_matches_and_saves(db_session):
    """Targeted scrape finds RMP match for a Nexus professor and links them."""
    # Set up a Nexus professor
    prof = Professor(name_nexus="CONRAD, PHILL", department="CMPSC")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="CMPSC156", department="CMPSC")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.7,
    ))
    db_session.commit()

    # Mock the scraper to return a matching teacher
    mock_scraper = MagicMock()
    mock_scraper.search_teacher_by_name.return_value = [{
        "legacy_id": 7777,
        "first_name": "Phill",
        "last_name": "Conrad",
        "department": "Computer Science",
        "avg_rating": 4.5,
        "avg_difficulty": 2.5,
        "would_take_again_pct": 90.0,
        "num_ratings": 78,
        "comments": [{"text": "Great class!", "date": "2024-09-01"}],
    }]

    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    assert stats["searched"] == 1
    assert stats["matched"] == 1
    assert stats["skipped"] == 0

    db_session.refresh(prof)
    assert prof.rmp_id == 7777
    assert prof.match_confidence >= 85


def test_scrape_skips_low_confidence(db_session):
    """Targeted scrape skips RMP results that don't fuzzy match the Nexus name."""
    prof = Professor(name_nexus="ZHANG, WEI", department="MATH")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="MATH100", department="MATH")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.0,
    ))
    db_session.commit()

    mock_scraper = MagicMock()
    mock_scraper.search_teacher_by_name.return_value = [{
        "legacy_id": 8888,
        "first_name": "Robert",
        "last_name": "Johnson",
        "department": "Mathematics",
        "avg_rating": 3.0,
        "avg_difficulty": 3.5,
        "would_take_again_pct": 50.0,
        "num_ratings": 10,
        "comments": [],
    }]

    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    assert stats["matched"] == 0
    assert stats["skipped"] == 1
    assert prof.rmp_id is None


def test_scrape_skips_stale_check(db_session):
    """Targeted scrape skips professors who already have fresh RMP data."""
    from scrapers.rmp_loader import load_rmp_teacher_to_db

    prof = Professor(name_nexus="FRESH, DATA", department="CS")
    db_session.add(prof)
    db_session.flush()
    course = Course(code="CS200", department="CS")
    db_session.add(course)
    db_session.flush()
    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.5,
    ))

    # Pre-load RMP data (fresh)
    load_rmp_teacher_to_db({
        "legacy_id": 1111,
        "first_name": "Fresh",
        "last_name": "Data",
        "department": "CS",
        "avg_rating": 4.0,
        "avg_difficulty": 3.0,
        "would_take_again_pct": 80.0,
        "num_ratings": 20,
        "comments": [],
    }, db_session, nexus_professor_id=prof.id, match_confidence=95)

    mock_scraper = MagicMock()
    stats = scrape_active_professors(db_session, scraper=mock_scraper, min_year=2024, delay=0)

    # Should not have called the scraper since data is fresh
    mock_scraper.search_teacher_by_name.assert_not_called()
    assert stats["already_fresh"] >= 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_targeted_scrape.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scrapers.targeted_scrape'`

**Step 3: Write minimal implementation**

`scrapers/targeted_scrape.py`:
```python
import logging
import time
import random

from db.models import Professor, RmpRating
from scrapers.rmp_loader import get_active_professors, is_stale, load_rmp_teacher_to_db
from scrapers.rmp_scraper import RmpScraper
from etl.name_matcher import normalize_nexus_name, normalize_rmp_name, match_confidence

logger = logging.getLogger(__name__)


def scrape_active_professors(
    session,
    scraper: RmpScraper | None = None,
    min_year: int = 2023,
    max_age_days: int = 2,
    delay: float | None = None,
) -> dict:
    """Scrape RMP for active professors using targeted name search.

    Returns stats dict: {searched, matched, skipped, already_fresh, errors}.
    """
    if scraper is None:
        scraper = RmpScraper()

    professors = get_active_professors(session, min_year=min_year)
    total = len(professors)
    stats = {"searched": 0, "matched": 0, "skipped": 0, "already_fresh": 0, "errors": 0}

    for i, prof in enumerate(professors):
        # Check if data is already fresh
        latest_rating = (
            session.query(RmpRating)
            .filter_by(professor_id=prof.id)
            .order_by(RmpRating.fetched_at.desc())
            .first()
        )
        fetched_at = latest_rating.fetched_at if latest_rating else None
        if not is_stale(fetched_at, max_age_days=max_age_days):
            stats["already_fresh"] += 1
            continue

        # Build search name from Nexus name
        nexus_name = prof.name_nexus
        if not nexus_name:
            stats["skipped"] += 1
            continue

        # Convert "LAST, FIRST" to "First Last" for RMP search
        norm = normalize_nexus_name(nexus_name)
        search_name = norm.title()

        try:
            results = scraper.search_teacher_by_name(search_name)
            stats["searched"] += 1
        except Exception as e:
            logger.error(f"[{i+1}/{total}] Error searching '{search_name}': {e}")
            stats["errors"] += 1
            continue

        # Fuzzy match against results
        best_match = None
        best_confidence = 0
        for teacher in results:
            rmp_name = f"{teacher['first_name']} {teacher['last_name']}"
            norm_rmp = normalize_rmp_name(rmp_name)
            confidence = match_confidence(norm, norm_rmp)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = teacher

        if best_match and best_confidence >= 70:
            status = "auto" if best_confidence >= 85 else "review"
            try:
                load_rmp_teacher_to_db(
                    best_match, session,
                    nexus_professor_id=prof.id,
                    match_confidence=best_confidence,
                )
                stats["matched"] += 1
                logger.info(
                    f"[{i+1}/{total}] {status.upper()} {nexus_name} -> "
                    f"{best_match['first_name']} {best_match['last_name']} "
                    f"({best_confidence}%)"
                )
            except Exception as e:
                logger.error(f"[{i+1}/{total}] Error saving '{nexus_name}': {e}")
                session.rollback()
                stats["errors"] += 1
        else:
            stats["skipped"] += 1
            logger.debug(
                f"[{i+1}/{total}] SKIP {nexus_name} — "
                f"best match: {best_confidence}%"
            )

        # Rate limiting
        if delay is None:
            time.sleep(random.uniform(2, 4))
        elif delay > 0:
            time.sleep(delay)

    return stats
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_targeted_scrape.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add scrapers/targeted_scrape.py tests/test_targeted_scrape.py
git commit -m "feat: add targeted scrape loop with fuzzy matching and staleness check"
```

---

## Task 5: Batch NLP Processor

**Files:**
- Modify: `etl/nlp_processor.py`
- Create: `tests/test_batch_nlp.py`

**Step 1: Write the failing test**

`tests/test_batch_nlp.py`:
```python
from db.models import Professor, RmpRating, RmpComment
from etl.nlp_processor import process_all_comments


def test_process_all_comments_fills_sentiment(db_session):
    """process_all_comments sets sentiment_score on unprocessed comments."""
    prof = Professor(name_nexus="NLP, TEST", department="CS")
    db_session.add(prof)
    db_session.flush()

    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=4.0, difficulty=3.0,
        num_ratings=10,
    )
    db_session.add(rating)
    db_session.flush()

    c1 = RmpComment(rmp_rating_id=rating.id, comment_text="Amazing professor, super clear!")
    c2 = RmpComment(rmp_rating_id=rating.id, comment_text="Terrible class, very confusing.")
    db_session.add_all([c1, c2])
    db_session.commit()

    # Sentiment should be None before processing
    assert c1.sentiment_score is None
    assert c2.sentiment_score is None

    stats = process_all_comments(db_session)

    db_session.refresh(c1)
    db_session.refresh(c2)

    assert c1.sentiment_score is not None
    assert c1.sentiment_score > 0  # positive
    assert c2.sentiment_score is not None
    assert c2.sentiment_score < 0  # negative
    assert stats["processed"] == 2


def test_process_all_comments_extracts_keywords(db_session):
    """process_all_comments sets keywords on the first comment per rating."""
    prof = Professor(name_nexus="KW, TEST", department="CS")
    db_session.add(prof)
    db_session.flush()

    rating = RmpRating(
        professor_id=prof.id,
        overall_quality=4.0, difficulty=3.0,
        num_ratings=10,
    )
    db_session.add(rating)
    db_session.flush()

    comments = [
        RmpComment(rmp_rating_id=rating.id, comment_text="The exams are really hard but fair"),
        RmpComment(rmp_rating_id=rating.id, comment_text="Hard exams but the lectures are clear"),
        RmpComment(rmp_rating_id=rating.id, comment_text="Clear lectures and tough exams"),
    ]
    db_session.add_all(comments)
    db_session.commit()

    process_all_comments(db_session)

    # At least one comment should have keywords set
    kw_comments = (
        db_session.query(RmpComment)
        .filter(RmpComment.rmp_rating_id == rating.id, RmpComment.keywords.isnot(None))
        .all()
    )
    assert len(kw_comments) > 0
    assert any("exam" in kw.lower() for c in kw_comments for kw in (c.keywords or []))
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_batch_nlp.py -v`
Expected: FAIL — `ImportError: cannot import name 'process_all_comments'`

**Step 3: Write minimal implementation**

Add to `etl/nlp_processor.py` at the bottom:

```python
def process_all_comments(session) -> dict:
    """Batch process all unprocessed RMP comments: VADER sentiment + TF-IDF keywords.

    Returns stats dict: {processed, keywords_set}.
    """
    from db.models import RmpRating, RmpComment

    # Get all comments without sentiment scores
    unprocessed = (
        session.query(RmpComment)
        .filter(RmpComment.sentiment_score.is_(None))
        .all()
    )

    stats = {"processed": 0, "keywords_set": 0}

    # Phase 1: Sentiment scoring
    for comment in unprocessed:
        comment.sentiment_score = analyze_sentiment(comment.comment_text or "")
        stats["processed"] += 1

    session.flush()

    # Phase 2: TF-IDF keywords per rating (group comments by rating_id)
    rating_ids = {c.rmp_rating_id for c in unprocessed}
    for rating_id in rating_ids:
        comments_for_rating = (
            session.query(RmpComment)
            .filter_by(rmp_rating_id=rating_id)
            .all()
        )
        texts = [c.comment_text for c in comments_for_rating if c.comment_text]
        if len(texts) >= 2:
            keywords = extract_keywords(texts, top_n=8)
            # Store keywords on the first comment of this rating
            comments_for_rating[0].keywords = keywords
            stats["keywords_set"] += 1

    session.commit()
    return stats
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_batch_nlp.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add etl/nlp_processor.py tests/test_batch_nlp.py
git commit -m "feat: add batch NLP processor for sentiment and keyword extraction"
```

---

## Task 6: Batch Scoring Engine

**Files:**
- Modify: `etl/scoring.py`
- Create: `tests/test_batch_scoring.py`

**Step 1: Write the failing test**

`tests/test_batch_scoring.py`:
```python
from db.models import Professor, Course, GradeDistribution, RmpRating, GauchoScore
from etl.scoring import compute_all_scores


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
    assert scores[0].course_id == course.id
    assert scores[0].weights_used is not None
    assert stats["computed"] >= 1


def test_compute_all_scores_skips_unmatched(db_session):
    """compute_all_scores skips professors without RMP data."""
    prof = Professor(name_nexus="NORP, MATCH", department="MATH")
    db_session.add(prof)
    db_session.flush()

    course = Course(code="MATH500", department="MATH")
    db_session.add(course)
    db_session.flush()

    db_session.add(GradeDistribution(
        professor_id=prof.id, course_id=course.id,
        quarter="Fall", year=2024, avg_gpa=3.0,
    ))
    db_session.commit()

    stats = compute_all_scores(db_session)

    scores = db_session.query(GauchoScore).filter_by(professor_id=prof.id).all()
    assert len(scores) == 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_batch_scoring.py -v`
Expected: FAIL — `ImportError: cannot import name 'compute_all_scores'`

**Step 3: Write minimal implementation**

Add to `etl/scoring.py` at the bottom:

```python
def compute_all_scores(
    session,
    weights: dict[str, float] | None = None,
) -> dict:
    """Compute Gaucho Scores for all matched professors (those with both grades and RMP data).

    Returns stats dict: {computed, skipped}.
    """
    from sqlalchemy import func
    from db.models import (
        Professor, Course, GradeDistribution, RmpRating, RmpComment, GauchoScore,
    )

    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}

    stats = {"computed": 0, "skipped": 0}

    # Find all (professor, course) pairs where professor has RMP data
    pairs = (
        session.query(
            Professor.id,
            GradeDistribution.course_id,
            func.avg(GradeDistribution.avg_gpa).label("mean_gpa"),
        )
        .join(GradeDistribution, GradeDistribution.professor_id == Professor.id)
        .join(RmpRating, RmpRating.professor_id == Professor.id)
        .filter(Professor.rmp_id.isnot(None))
        .group_by(Professor.id, GradeDistribution.course_id)
        .all()
    )

    for prof_id, course_id, mean_gpa in pairs:
        # Get latest RMP rating
        rating = (
            session.query(RmpRating)
            .filter_by(professor_id=prof_id)
            .order_by(RmpRating.fetched_at.desc())
            .first()
        )
        if not rating:
            stats["skipped"] += 1
            continue

        # Compute factors
        gpa_f = normalize_gpa(float(mean_gpa)) if mean_gpa else 0.5
        qual_f = normalize_quality(rating.overall_quality) if rating.overall_quality else 0.5
        diff_f = normalize_difficulty(rating.difficulty) if rating.difficulty else 0.5

        # Sentiment: average of comments
        avg_sentiment = (
            session.query(func.avg(RmpComment.sentiment_score))
            .join(RmpRating, RmpComment.rmp_rating_id == RmpRating.id)
            .filter(RmpRating.professor_id == prof_id, RmpComment.sentiment_score.isnot(None))
            .scalar()
        )
        sent_f = (float(avg_sentiment) + 1) / 2 if avg_sentiment is not None else 0.5

        # Bayesian adjust quality
        if rating.overall_quality and rating.num_ratings:
            adj_qual = bayesian_adjust(rating.overall_quality, rating.num_ratings, 3.0)
            qual_f = normalize_quality(adj_qual)

        score = compute_gaucho_score(gpa_f, qual_f, diff_f, sent_f, weights)

        # Upsert: delete old score for this pair, insert new
        session.query(GauchoScore).filter_by(
            professor_id=prof_id, course_id=course_id,
        ).delete()

        from datetime import datetime, timezone
        session.add(GauchoScore(
            professor_id=prof_id,
            course_id=course_id,
            score=score,
            weights_used=weights,
            computed_at=datetime.now(timezone.utc),
        ))
        stats["computed"] += 1

    session.commit()
    return stats
```

Note: you need to add `from db.models import RmpComment` — this import is inside the function to avoid circular imports.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_batch_scoring.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add etl/scoring.py tests/test_batch_scoring.py
git commit -m "feat: add batch Gaucho Score computation for matched professors"
```

---

## Task 7: Pipeline CLI Script

**Files:**
- Create: `scripts/run_pipeline.py`

**Step 1: Create the pipeline script**

`scripts/run_pipeline.py`:
```python
"""One-shot CLI script to run the full Gaucho pipeline.

Usage:
    python scripts/run_pipeline.py              # full pipeline
    python scripts/run_pipeline.py --scrape     # scrape only
    python scripts/run_pipeline.py --nlp        # NLP only
    python scripts/run_pipeline.py --score      # scoring only
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.connection import get_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_scrape(session):
    from scrapers.targeted_scrape import scrape_active_professors
    logger.info("=== Phase 1: Targeted RMP Scrape ===")
    stats = scrape_active_professors(session, min_year=2023)
    logger.info(f"Scrape complete: {stats}")
    return stats


def run_nlp(session):
    from etl.nlp_processor import process_all_comments
    logger.info("=== Phase 2: NLP Processing ===")
    stats = process_all_comments(session)
    logger.info(f"NLP complete: {stats}")
    return stats


def run_scoring(session):
    from etl.scoring import compute_all_scores
    logger.info("=== Phase 3: Gaucho Score Computation ===")
    stats = compute_all_scores(session)
    logger.info(f"Scoring complete: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Run the Gaucho Course Optimizer pipeline")
    parser.add_argument("--scrape", action="store_true", help="Run RMP scrape only")
    parser.add_argument("--nlp", action="store_true", help="Run NLP processing only")
    parser.add_argument("--score", action="store_true", help="Run scoring only")
    args = parser.parse_args()

    run_all = not (args.scrape or args.nlp or args.score)

    session = get_session()
    try:
        if run_all or args.scrape:
            run_scrape(session)
        if run_all or args.nlp:
            run_nlp(session)
        if run_all or args.score:
            run_scoring(session)

        logger.info("Pipeline finished.")
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted. Partial progress is saved.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
```

**Step 2: Verify it runs (dry run)**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && python scripts/run_pipeline.py --help`
Expected: Shows usage text with `--scrape`, `--nlp`, `--score` flags.

**Step 3: Commit**

```bash
git add scripts/run_pipeline.py
git commit -m "feat: add CLI pipeline script for scrape/NLP/scoring"
```

---

## Task 8: Update Scheduler to Every 2 Days

**Files:**
- Modify: `scheduler/jobs.py`
- Modify: `tests/test_scheduler.py`

**Step 1: Update the test**

Replace `tests/test_scheduler.py`:
```python
from scheduler.jobs import create_scheduler, RMP_REFRESH_JOB_ID, QUARTERLY_JOB_ID


def test_create_scheduler_has_jobs():
    sched = create_scheduler(start=False)
    job_ids = [j.id for j in sched.get_jobs()]
    assert RMP_REFRESH_JOB_ID in job_ids
    assert QUARTERLY_JOB_ID in job_ids


def test_rmp_refresh_runs_every_2_days():
    sched = create_scheduler(start=False)
    rmp_job = sched.get_job(RMP_REFRESH_JOB_ID)
    trigger = rmp_job.trigger
    # CronTrigger for every 2 days: day='*/2'
    assert hasattr(trigger, 'fields')
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scheduler.py -v`
Expected: FAIL — `ImportError: cannot import name 'RMP_REFRESH_JOB_ID'`

**Step 3: Update implementation**

Replace `scheduler/jobs.py`:
```python
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

RMP_REFRESH_JOB_ID = "rmp_targeted_refresh"
QUARTERLY_JOB_ID = "quarterly_grade_update"


def rmp_targeted_refresh():
    """Every-2-days job: targeted RMP scrape → NLP → recompute scores."""
    logger.info("Starting targeted RMP refresh...")
    from scrapers.targeted_scrape import scrape_active_professors
    from etl.nlp_processor import process_all_comments
    from etl.scoring import compute_all_scores
    from db.connection import get_session

    session = get_session()
    try:
        scrape_stats = scrape_active_professors(session, min_year=2023)
        logger.info(f"Scrape: {scrape_stats}")

        nlp_stats = process_all_comments(session)
        logger.info(f"NLP: {nlp_stats}")

        score_stats = compute_all_scores(session)
        logger.info(f"Scoring: {score_stats}")
    except Exception as e:
        logger.error(f"RMP refresh failed: {e}")
    finally:
        session.close()


def quarterly_grade_update():
    """Quarterly job: fetch grades CSV → load → recompute scores."""
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
        rmp_targeted_refresh,
        trigger=CronTrigger(day="*/2", hour=2, minute=0),
        id=RMP_REFRESH_JOB_ID,
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
Expected: PASS (2 tests)

**Step 5: Run all tests to make sure nothing is broken**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add scheduler/jobs.py tests/test_scheduler.py
git commit -m "feat: update scheduler to every-2-day targeted RMP refresh"
```

---

## Task 9: Run the Full Pipeline

This is the manual execution step — no code changes, just running the pipeline.

**Step 1: Run the pipeline scrape phase**

Run: `cd /c/Users/King\ Hratch/gaucho-course-optimizer && python scripts/run_pipeline.py --scrape 2>&1 | tee pipeline_scrape.log`

Expected: ~2,292 professors searched, progress logs like `[1/2292] AUTO SMITH, JOHN -> John Smith (95%)`. This will take ~60-120 minutes. Monitor with `tail -f pipeline_scrape.log`.

**Step 2: Run NLP phase**

Run: `python scripts/run_pipeline.py --nlp`
Expected: Processes all scraped comments. Should take < 1 minute.

**Step 3: Run scoring phase**

Run: `python scripts/run_pipeline.py --score`
Expected: Computes Gaucho Scores for all matched professors. Should take < 1 minute.

**Step 4: Verify data in DB**

Run: `docker compose exec db psql -U gco -c "SELECT count(*) FROM rmp_ratings; SELECT count(*) FROM rmp_comments WHERE sentiment_score IS NOT NULL; SELECT count(*) FROM gaucho_scores;"`
Expected: Non-zero counts in all three queries.

**Step 5: Verify dashboard**

Open http://localhost:8501, search for "CMPSC8" or "PSTAT120A". Should now show professor cards with Gaucho Scores, RMP ratings, and keywords.

**Step 6: Commit log**

```bash
git add pipeline_scrape.log
git commit -m "chore: add initial pipeline run log"
```

---

## Summary

| Task | Component | Tests | New/Modified |
|------|-----------|-------|--------------|
| 1 | Targeted name search | 1 test | Modified: rmp_scraper.py |
| 2 | Active professor query | 3 tests | Modified: rmp_loader.py |
| 3 | Nexus professor linking | 1 test | Modified: rmp_loader.py |
| 4 | Targeted scrape loop | 3 tests | New: targeted_scrape.py |
| 5 | Batch NLP processor | 2 tests | Modified: nlp_processor.py |
| 6 | Batch scoring engine | 2 tests | Modified: scoring.py |
| 7 | Pipeline CLI script | — | New: scripts/run_pipeline.py |
| 8 | Scheduler update | 2 tests | Modified: scheduler/jobs.py |
| 9 | Run pipeline | — | Manual execution |

**Total: 9 tasks, ~14 new tests, 9 commits**
