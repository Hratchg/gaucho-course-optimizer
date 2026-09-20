"""Regression test for BUG-4 — professor tags must actually reach the API.

Keyword extraction used to write keywords onto only the first comment of each
rating, while tag aggregation counts one vote per comment and filters with
min_count=3. Every tag therefore topped out at one vote and the curated
TAG_VOCABULARY was unreachable — 0 of 55 professors on MATH4A had tags in
production. This test drives the whole path: comments -> NLP -> tags.
"""
from db.models import Professor, Course, GradeDistribution, RmpRating, RmpComment
from etl.nlp_processor import process_all_comments, backfill_keywords
from dashboard.queries import get_professors_for_course, map_keywords_to_tags


def test_tags_appear_for_a_professor_with_consistent_comments(db_session):
    prof = Professor(name_nexus="TAGS, TEST", name_rmp="Tag Test", department="CMPSC")
    course = Course(code="CMPSCTAG", title="Tagging", department="CMPSC")
    db_session.add_all([prof, course])
    db_session.flush()

    db_session.add(
        GradeDistribution(
            professor_id=prof.id,
            course_id=course.id,
            quarter="Fall",
            year=2024,
            avg_gpa=3.3,
        )
    )

    rating = RmpRating(
        professor_id=prof.id, overall_quality=4.2, difficulty=2.5, num_ratings=12
    )
    db_session.add(rating)
    db_session.flush()

    # Five separate students independently describing easy grading. Each is its
    # own comment, so each contributes its own vote.
    db_session.add_all([
        RmpComment(rmp_rating_id=rating.id, comment_text=t)
        for t in [
            "Super easy grader, generous curve on every exam",
            "Easy grading and the curve really helps your grade",
            "The grading is easy, most people get an easy A",
            "Easy class with lenient grading throughout",
            "Lenient grader, easy exams, generous curve",
        ]
    ])
    db_session.commit()

    process_all_comments(db_session)

    professors = get_professors_for_course(db_session, course.id)

    assert len(professors) == 1
    tags = professors[0]["tags"]
    assert tags, "professor tags are empty — the min_count threshold is unreachable again"
    assert max(t["count"] for t in tags) >= 3


def test_single_comment_professor_has_no_tags(db_session):
    """One comment cannot reach min_count — absence here is correct, not a bug."""
    prof = Professor(name_nexus="TAGS, SOLO", name_rmp="Solo", department="CMPSC")
    course = Course(code="CMPSCSOLO", title="Solo", department="CMPSC")
    db_session.add_all([prof, course])
    db_session.flush()

    db_session.add(
        GradeDistribution(
            professor_id=prof.id, course_id=course.id, quarter="Fall", year=2024, avg_gpa=3.0
        )
    )
    rating = RmpRating(
        professor_id=prof.id, overall_quality=3.0, difficulty=3.0, num_ratings=1
    )
    db_session.add(rating)
    db_session.flush()
    db_session.add(
        RmpComment(rmp_rating_id=rating.id, comment_text="Easy grader with a generous curve")
    )
    db_session.commit()

    process_all_comments(db_session)

    professors = get_professors_for_course(db_session, course.id)
    assert professors[0]["tags"] == []


def test_min_count_threshold_is_reachable():
    """Guards the threshold itself: three votes for a tag must pass the filter."""
    votes = ["Easy Grader"] * 3 + ["Clear Lectures"] * 2
    tags = map_keywords_to_tags(votes, min_count=3)

    assert [t["name"] for t in tags] == ["Easy Grader"]
    assert tags[0]["count"] == 3


def test_backfill_recovers_tags_for_already_processed_comments(db_session):
    """Existing rows are skipped by process_all_comments; backfill fixes them.

    Reproduces production state: comments already have sentiment scores and the
    old single-row keyword layout, so the BUG-4 fix alone leaves them tagless.
    """
    prof = Professor(name_nexus="TAGS, OLD", name_rmp="Old Data", department="CMPSC")
    course = Course(code="CMPSCOLD", title="Legacy", department="CMPSC")
    db_session.add_all([prof, course])
    db_session.flush()

    db_session.add(
        GradeDistribution(
            professor_id=prof.id, course_id=course.id, quarter="Fall", year=2024, avg_gpa=3.2
        )
    )
    rating = RmpRating(
        professor_id=prof.id, overall_quality=4.0, difficulty=2.5, num_ratings=9
    )
    db_session.add(rating)
    db_session.flush()

    texts = [
        "Super easy grader, generous curve on every exam",
        "Easy grading and the curve really helps your grade",
        "The grading is easy, most people get an easy A",
        "Easy class with lenient grading throughout",
    ]
    comments = [
        # sentiment already set => process_all_comments will skip these
        RmpComment(rmp_rating_id=rating.id, comment_text=t, sentiment_score=0.5)
        for t in texts
    ]
    # Old layout: keywords on the first comment only.
    comments[0].keywords = ["easy", "grading", "curve"]
    db_session.add_all(comments)
    db_session.commit()

    # The forward fix alone changes nothing, because nothing is unprocessed.
    process_all_comments(db_session)
    assert get_professors_for_course(db_session, course.id)[0]["tags"] == []

    stats = backfill_keywords(db_session)
    assert stats["keywords_set"] >= len(texts)

    tags = get_professors_for_course(db_session, course.id)[0]["tags"]
    assert tags, "backfill did not restore tags for pre-existing comments"
