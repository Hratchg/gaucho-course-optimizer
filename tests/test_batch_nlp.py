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
    """process_all_comments sets keywords on every comment with content."""
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

    # BUG-4: keywords must land on *every* comment, not just the first. Tag
    # aggregation counts one vote per comment, so keywords on a single row cap
    # every tag at one vote and the min_count filter drops them all.
    assert len(kw_comments) == len(comments)


def test_keywords_reflect_each_comments_own_text(db_session):
    """Each comment's keywords come from that comment, not the rating average."""
    prof = Professor(name_nexus="KW, PERCOMMENT", department="CS")
    db_session.add(prof)
    db_session.flush()

    rating = RmpRating(
        professor_id=prof.id, overall_quality=4.0, difficulty=3.0, num_ratings=10
    )
    db_session.add(rating)
    db_session.flush()

    grading = RmpComment(
        rmp_rating_id=rating.id, comment_text="Lenient grading and a generous curve"
    )
    workload = RmpComment(
        rmp_rating_id=rating.id, comment_text="Heavy workload with weekly homework"
    )
    db_session.add_all([grading, workload])
    db_session.commit()

    process_all_comments(db_session)
    db_session.refresh(grading)
    db_session.refresh(workload)

    assert any("grading" in kw or "lenient" in kw for kw in grading.keywords)
    assert not any("workload" in kw or "homework" in kw for kw in grading.keywords)
    assert any("workload" in kw or "homework" in kw for kw in workload.keywords)


def test_blank_comments_get_no_keywords(db_session):
    """Empty comment text yields no keywords rather than borrowing a neighbour's."""
    prof = Professor(name_nexus="KW, BLANK", department="CS")
    db_session.add(prof)
    db_session.flush()

    rating = RmpRating(
        professor_id=prof.id, overall_quality=4.0, difficulty=3.0, num_ratings=10
    )
    db_session.add(rating)
    db_session.flush()

    blank = RmpComment(rmp_rating_id=rating.id, comment_text="   ")
    filled = [
        RmpComment(rmp_rating_id=rating.id, comment_text="Clear lectures every week"),
        RmpComment(rmp_rating_id=rating.id, comment_text="Lectures were clear and helpful"),
    ]
    db_session.add_all([blank, *filled])
    db_session.commit()

    process_all_comments(db_session)
    db_session.refresh(blank)

    assert not blank.keywords
