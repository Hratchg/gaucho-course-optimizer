"""Tests for tag vocabulary mapping in dashboard/queries.py.

Unit tests for map_keywords_to_tags() (no DB needed) and one integration test
for get_professors_for_course() returning structured tags.
"""
from datetime import datetime, timezone

import pytest

from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment


# ---------------------------------------------------------------------------
# Unit tests for map_keywords_to_tags (pure function, no DB)
# ---------------------------------------------------------------------------


class TestMapKeywordsToTags:
    """Unit tests for the map_keywords_to_tags function."""

    def test_basic_mapping_with_threshold(self):
        """Keywords with count >= 3 are returned; below threshold are dropped."""
        from dashboard.queries import map_keywords_to_tags

        # 5 comments with "easy", 3 with "clear", 1 with "helpful"
        raw = ["easy"] * 5 + ["clear"] * 3 + ["helpful"] * 1
        result = map_keywords_to_tags(raw)

        names = [t["name"] for t in result]
        assert "Easy Grader" in names
        assert "Clear Explanations" in names
        # "helpful" maps to "Helpful" but count=1 is below threshold
        assert "Helpful" not in names

    def test_all_below_threshold_returns_empty(self):
        """When all tags have count < 3, return empty list."""
        from dashboard.queries import map_keywords_to_tags

        raw = ["easy", "easy", "clear"]  # 2 and 1 -- both below 3
        result = map_keywords_to_tags(raw)
        assert result == []

    def test_unmapped_keyword_dropped(self):
        """Keywords that don't match any vocabulary entry are silently dropped."""
        from dashboard.queries import map_keywords_to_tags

        raw = ["xyzgarbage"] * 5
        result = map_keywords_to_tags(raw)
        assert result == []

    def test_max_six_tags_sorted_by_count(self):
        """Returns at most 6 tags, sorted by count descending."""
        from dashboard.queries import map_keywords_to_tags

        # Create 8 different keywords that map to different tags, each with count >= 3
        raw = (
            ["easy"] * 10
            + ["boring"] * 9
            + ["clear"] * 8
            + ["helpful"] * 7
            + ["tough exam"] * 6
            + ["heavy"] * 5
            + ["caring"] * 4
            + ["attendance"] * 3
        )
        result = map_keywords_to_tags(raw)

        assert len(result) <= 6
        # Sorted descending by count
        counts = [t["count"] for t in result]
        assert counts == sorted(counts, reverse=True)

    def test_multiple_raw_keywords_same_tag_counts_summed(self):
        """Multiple raw keywords mapping to the same tag have counts combined."""
        from dashboard.queries import map_keywords_to_tags

        # "easy" and "lenient" both map to "Easy Grader"
        raw = ["easy"] * 2 + ["lenient"] * 2
        # Total for "Easy Grader" = 4, which is >= 3
        result = map_keywords_to_tags(raw)

        names = [t["name"] for t in result]
        assert "Easy Grader" in names
        easy_tag = [t for t in result if t["name"] == "Easy Grader"][0]
        assert easy_tag["count"] == 4

    def test_case_insensitive_matching(self):
        """Matching is case-insensitive: 'Easy' and 'easy' both map to 'Easy Grader'."""
        from dashboard.queries import map_keywords_to_tags

        # 3 entries with different cases all map to "Easy Grader" -> count=3 meets threshold
        raw = ["Easy", "easy", "EASY"]
        result = map_keywords_to_tags(raw)
        assert len(result) == 1
        assert result[0]["name"] == "Easy Grader"
        assert result[0]["count"] == 3

        raw = ["Easy", "easy", "EASY", "easy"]
        result = map_keywords_to_tags(raw)
        assert len(result) == 1
        assert result[0]["name"] == "Easy Grader"
        assert result[0]["count"] == 4

    def test_tag_vocabulary_coverage(self):
        """TAG_VOCABULARY contains approximately 15 entries covering 6 categories."""
        from dashboard.queries import TAG_VOCABULARY

        assert isinstance(TAG_VOCABULARY, dict)
        # Should have roughly 15+ entries (raw keyword -> tag name)
        assert len(TAG_VOCABULARY) >= 15
        # All 6 categories should be represented
        tag_names = set(TAG_VOCABULARY.values())
        expected_tags = {
            "Easy Grader", "Tough Grader",
            "Engaging", "Dry Lectures", "Clear Explanations",
            "Heavy Workload", "Light Workload",
            "Tough Exams", "Fair Tests",
            "Helpful", "Caring", "Intimidating",
            "Attendance Mandatory", "Extra Credit",
            "Would Take Again",
        }
        assert expected_tags.issubset(tag_names)

    def test_empty_input(self):
        """Empty list returns empty result."""
        from dashboard.queries import map_keywords_to_tags

        assert map_keywords_to_tags([]) == []

    def test_result_structure(self):
        """Each result is a dict with 'name' (str) and 'count' (int)."""
        from dashboard.queries import map_keywords_to_tags

        raw = ["easy"] * 5
        result = map_keywords_to_tags(raw)
        assert len(result) >= 1
        for tag in result:
            assert "name" in tag
            assert "count" in tag
            assert isinstance(tag["name"], str)
            assert isinstance(tag["count"], int)

    def test_custom_min_count(self):
        """min_count parameter overrides the default threshold."""
        from dashboard.queries import map_keywords_to_tags

        raw = ["easy"] * 2
        # Default threshold (3) filters this out
        assert map_keywords_to_tags(raw) == []
        # Custom threshold of 1 includes it
        result = map_keywords_to_tags(raw, min_count=1)
        assert len(result) == 1
        assert result[0]["name"] == "Easy Grader"

    def test_per_comment_deduplication(self):
        """If one 'comment' has multiple keywords mapping to the same tag,
        it should only count as 1 toward that tag.

        The function receives a flat list where each entry represents one keyword
        from one comment. Per-comment dedup must happen at the call site
        (get_professors_for_course). This test verifies that the flat list
        counting works correctly -- each entry in the list is one vote."""
        from dashboard.queries import map_keywords_to_tags

        # If dedup is done at call site, each entry here is already one vote
        # 3 separate entries for "easy" means 3 comments mentioned it
        raw = ["easy", "easy", "easy"]
        result = map_keywords_to_tags(raw)
        assert len(result) == 1
        assert result[0]["count"] == 3


# ---------------------------------------------------------------------------
# Integration test: get_professors_for_course returns "tags" field
# ---------------------------------------------------------------------------


class TestGetProfessorsTagsIntegration:
    """Integration tests verifying get_professors_for_course returns structured tags."""

    def test_returns_tags_field_not_keywords(self, db_session):
        """get_professors_for_course returns 'tags' key (not 'keywords')
        with structured {name, count} objects."""
        from dashboard.queries import get_professors_for_course

        prof = Professor(name_nexus="Tag Prof", department="CMPSC")
        course = Course(code="TAG001", title="Tag Testing", department="CMPSC")
        db_session.add_all([prof, course])
        db_session.flush()

        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter="Fall", year=2024, avg_gpa=3.5,
        ))
        db_session.flush()

        rating = RmpRating(
            professor_id=prof.id, overall_quality=4.0,
            difficulty=2.0, num_ratings=20,
        )
        db_session.add(rating)
        db_session.flush()

        # Add 4 comments each with "easy" keyword -- should produce "Easy Grader" tag
        for i in range(4):
            db_session.add(RmpComment(
                rmp_rating_id=rating.id,
                comment_text=f"Easy class {i}",
                sentiment_score=0.5,
                keywords=["easy"],
                created_at=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
            ))
        db_session.flush()

        results = get_professors_for_course(db_session, course.id)
        assert len(results) == 1
        prof_result = results[0]

        # Should have "tags", not "keywords"
        assert "tags" in prof_result
        assert "keywords" not in prof_result

        # Tags should be a list of dicts with name and count
        tags = prof_result["tags"]
        assert isinstance(tags, list)
        assert len(tags) >= 1

        easy_tags = [t for t in tags if t["name"] == "Easy Grader"]
        assert len(easy_tags) == 1
        assert easy_tags[0]["count"] == 4

    def test_per_comment_dedup_in_integration(self, db_session):
        """When a single comment has multiple keywords mapping to the same tag,
        it only counts as 1 toward that tag's count."""
        from dashboard.queries import get_professors_for_course

        prof = Professor(name_nexus="Dedup Prof", department="CMPSC")
        course = Course(code="TAG002", title="Dedup Test", department="CMPSC")
        db_session.add_all([prof, course])
        db_session.flush()

        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter="Fall", year=2024, avg_gpa=3.5,
        ))
        db_session.flush()

        rating = RmpRating(
            professor_id=prof.id, overall_quality=4.0,
            difficulty=2.0, num_ratings=20,
        )
        db_session.add(rating)
        db_session.flush()

        # 3 comments: each has ["easy", "lenient"] -- both map to "Easy Grader"
        # Per-comment dedup means each comment counts as 1 for "Easy Grader"
        # So total should be 3 (not 6)
        for i in range(3):
            db_session.add(RmpComment(
                rmp_rating_id=rating.id,
                comment_text=f"Easy and lenient {i}",
                sentiment_score=0.5,
                keywords=["easy", "lenient"],
                created_at=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
            ))
        db_session.flush()

        results = get_professors_for_course(db_session, course.id)
        assert len(results) == 1
        tags = results[0]["tags"]

        easy_tags = [t for t in tags if t["name"] == "Easy Grader"]
        assert len(easy_tags) == 1
        # 3 comments, each counts as 1 (deduped) → total 3
        assert easy_tags[0]["count"] == 3

    def test_no_rmp_returns_empty_tags(self, db_session):
        """Professor with no RMP data returns empty tags list."""
        from dashboard.queries import get_professors_for_course

        prof = Professor(name_nexus="No RMP Prof", department="CMPSC")
        course = Course(code="TAG003", title="No RMP", department="CMPSC")
        db_session.add_all([prof, course])
        db_session.flush()

        db_session.add(GradeDistribution(
            professor_id=prof.id, course_id=course.id,
            quarter="Fall", year=2024, avg_gpa=3.5,
        ))
        db_session.flush()

        results = get_professors_for_course(db_session, course.id)
        assert len(results) == 1
        assert results[0]["tags"] == []
