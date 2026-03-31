# Coding Conventions

**Analysis Date:** 2026-03-30

## Naming Patterns

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `snake_case.py` | `test_name_matcher.py`, `rmp_loader.py` |
| Classes | `PascalCase` | `Professor`, `GradeDistribution`, `RmpRating` |
| Functions | `snake_case` | `normalize_nexus_name`, `match_confidence`, `get_engine` |
| Constants | `SCREAMING_SNAKE_CASE` | `TITLE_PATTERNS` (regex pattern) |
| DB tables | `snake_case` | `professors`, `grade_distributions`, `rmp_ratings` |
| DB columns | `snake_case` | `name_nexus`, `rmp_id`, `match_confidence`, `would_take_again_pct` |
| Private functions | `_snake_case` | `_parse_rmp_date`, `_get_unmatched_nexus`, `_link_professor` |
| Module-level globals | `_snake_case` | `_engine`, `_sia` (singleton lazy-loaded objects) |

## Code Style

**Formatting:**
- No explicit tool configured (no .black, .ruff, .flake8, etc. in project root)
- Code appears manually formatted with consistent 4-space indentation
- Line length varies; typical range 80-100 characters
- No pre-commit hooks detected

**Linting:**
- No explicit linting tool configured
- Code follows PEP 8 conventions informally

## Import Organization

**Order (as observed in codebase):**

1. Standard library imports (e.g., `import os`, `from datetime import datetime`)
2. Third-party imports (e.g., `from sqlalchemy import`, `from vaderSentiment import`, `import pandas`)
3. Local imports (e.g., `from db.models import`, `from etl.name_matcher import`)

**Path Style:**
- Absolute imports used throughout: `from db.models import`, `from etl.scoring import`
- `pythonpath = ["."]` configured in `pyproject.toml` to enable root-level imports
- No relative imports (e.g., no `from ..models import`) found in codebase

**Typical pattern:**
```python
# Standard library
import os
import re
from datetime import datetime, timezone
from collections import defaultdict

# Third-party
from sqlalchemy import Column, Integer, ForeignKey, func
from sqlalchemy.orm import Session, sessionmaker
from thefuzz import fuzz

# Local
from db.models import Professor, GradeDistribution
from db.connection import get_engine
from etl.name_matcher import normalize_rmp_name
```

## Error Handling

**Approach:** Exceptions + precondition checks

**Patterns observed:**

- **Explicit validation with ValueError:** Preconditions checked at function entry:
  ```python
  def load_rmp_teacher_to_db(teacher: dict, session, nexus_professor_id: int | None = None):
      # ...
      if nexus_professor_id is not None:
          prof = session.get(Professor, nexus_professor_id)
          if prof is None:
              raise ValueError(f"No professor with id={nexus_professor_id}")
          existing = session.query(Professor).filter_by(rmp_id=rmp_id).first()
          if existing and existing.id != nexus_professor_id:
              raise ValueError(f"RMP ID {rmp_id} already linked to professor id=...")
  ```

- **Silent fallbacks for parsing failures:**
  ```python
  def _parse_rmp_date(date_str: str | None) -> datetime | None:
      if not date_str:
          return None
      try:
          return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
      except ValueError:
          try:
              return datetime.fromisoformat(date_str)
          except ValueError:
              return None  # Silent failure
  ```

- **Logging for warnings (not exceptions):**
  ```python
  logger = logging.getLogger(__name__)
  # ...
  logger.warning(f"Collision: RMP ID {rmp_prof.rmp_id} already linked to ...")
  ```

- **No try-except for database operations:** SQLAlchemy exceptions propagate

## Async Patterns

**Approach:** Synchronous only

**Details:**
- No `async`/`await` found in codebase
- All database operations use SQLAlchemy ORM synchronously
- Scrapers (`rmp_scraper.py`, `targeted_scrape.py`) use blocking HTTP (`curl_cffi`)
- Scheduler (`apscheduler`) handles periodic jobs synchronously

## Type Hints

**Convention:** Type hints used throughout, modern Python 3.12+ syntax

**Patterns:**

- Function parameters and returns typed:
  ```python
  def normalize_gpa(gpa: float, dept_median: float = 3.0, dept_max: float = 4.0) -> float:
  def match_names(nexus_names: list[str], rmp_names: list[str], auto_threshold: int = 85) -> dict:
  def _parse_rmp_date(date_str: str | None) -> datetime | None:
  ```

- Union types use `|` operator (not `Union`):
  ```python
  dict[str, float] | None
  str | None
  ```

- Default dict/list types: lowercase `dict[K, V]`, `list[T]`

## Function Design

**Size:** Generally 5-30 lines; utility functions kept concise

**Parameters:**
- Most functions take 1-3 required parameters
- Optional parameters use `| None` union types with defaults
- Session objects passed as `session` parameter when needed (no context managers)

**Return values:**
- Scalar functions return typed values (float, dict, list)
- Batch operations return stats dict: `{"computed": N, "skipped": M}`
- Lookup functions return the object or `None`

**Example:**
```python
def compute_gaucho_score(
    gpa_factor: float,
    quality_factor: float,
    difficulty_factor: float,
    sentiment_factor: float,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute Gaucho Value Score (0-100) from normalized factors and weights."""
    if weights is None:
        weights = {"gpa": 0.25, "quality": 0.25, "difficulty": 0.25, "sentiment": 0.25}
    raw = (gpa_factor * weights.get("gpa", 0.25) + ...)
    return round(max(0.0, min(100.0, raw * 100)), 2)
```

## Module Design

**Exports:**
- Modules export all public functions
- Private functions prefixed with `_`
- No `__all__` declarations found

**Barrel files:**
- `__init__.py` files exist but are mostly empty: `db/__init__.py`, `etl/__init__.py`
- No re-exports defined

**Organization:**
- Each module has a single responsibility: `name_matcher.py` handles name matching, `scoring.py` handles score computation
- Shared utilities in separate module: `name_utils.py` for parsing helpers

## Comments

**Docstrings:**
- Module-level docstrings on some files (e.g., `enhanced_matcher.py`)
- Function docstrings in Google/PEP 257 style:
  ```python
  def match_names(nexus_names: list[str], rmp_names: list[str],
                  auto_threshold: int = 85) -> dict:
      """Match Nexus names to RMP names.

      Returns dict: {nexus_name: {"rmp_name": str, "confidence": int, "status": str}}
      status is "auto" (>=85), "review" (70-84), or absent if <70.
      """
  ```

- Inline comments used for clarification:
  ```python
  # Strip trailing timezone label (e.g. " UTC")
  cleaned = re.sub(r"\s+[A-Z]{2,4}$", "", date_str.strip())
  ```

**When to comment:**
- Non-obvious logic (e.g., Bayesian adjustment formula)
- Intent of regex patterns
- SAVEPOINT explanation in test fixtures

**No TODOs, FIXMEs, or XXX markers found** in codebase.

## Database Conventions

**Column naming:**
- Underscores for multi-word columns: `name_nexus`, `rmp_id`, `would_take_again_pct`, `avg_gpa`
- Grade columns named explicitly: `a_plus`, `a`, `a_minus`, `b_plus`, `b`, `b_minus`, etc.

**Relationships:**
- SQLAlchemy ORM relationships use lowercase names: `grades`, `rmp_ratings`, `scores`, `comments`
- Foreign key columns explicit: `professor_id`, `course_id`, `rmp_rating_id`

**Timestamps:**
- Default to UTC timezone: `Column(DateTime, default=lambda: datetime.now(timezone.utc))`
- Nullable timestamp columns for optional dates: `fetched_at`, `created_at`

## Singleton/Caching Patterns

**Global singletons with lazy initialization:**

```python
# db/connection.py
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL", "...")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine

# etl/nlp_processor.py
_sia = None

def _get_sia():
    global _sia
    if _sia is None:
        _sia = SentimentIntensityAnalyzer()
    return _sia
```

## Anti-patterns to Avoid

**Not used in this codebase:**
- Relative imports — Use absolute imports with `pythonpath` configuration
- `try-except` bare except clauses — Always specify exception type
- Class-based views or models beyond SQLAlchemy ORM
- Context managers for session management — Pass sessions explicitly; tests use SAVEPOINT pattern
- Wildcard imports (`from module import *`)
- F-strings not used in logging (older codebase style uses string formatting in some areas)

---

*Convention analysis: 2026-03-30*
