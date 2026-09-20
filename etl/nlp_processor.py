from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
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


def _fit_tfidf(non_empty: list[str]):
    """Fit the shared TF-IDF vectorizer over a professor's comments."""
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=200,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform(non_empty)
    return tfidf_matrix, vectorizer.get_feature_names_out()


def extract_keywords(comments: list[str], top_n: int = 8) -> list[str]:
    """Extract top-N distinctive keywords across a list of comments using TF-IDF."""
    if not comments:
        return []

    non_empty = [c for c in comments if c and c.strip()]
    if not non_empty:
        return []

    tfidf_matrix, feature_names = _fit_tfidf(non_empty)

    # Average TF-IDF across all comments
    avg_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
    top_indices = avg_scores.argsort()[-top_n:][::-1]

    return [feature_names[i] for i in top_indices]


def extract_keywords_per_comment(
    comments: list[str], top_n: int = 8
) -> list[list[str]]:
    """Extract top-N keywords for *each* comment, sharing one TF-IDF fit.

    Returns a list parallel to *comments* — index i holds the keywords for
    comments[i], and empty/blank comments yield an empty list.

    Tag aggregation counts one vote per comment (see
    dashboard.queries.get_professors_for_course), so keywords have to exist on
    every comment row. Collapsing a professor's comments into a single keyword
    list caps every tag at one vote, which can never reach the min_count
    threshold — that was BUG-4.

    The vectorizer is still fit across the whole set so IDF reflects what is
    distinctive within this professor's comments, but the top-N is taken per
    row rather than from the corpus average.
    """
    if not comments:
        return []

    indexed_non_empty = [
        (i, c) for i, c in enumerate(comments) if c and c.strip()
    ]
    if not indexed_non_empty:
        return [[] for _ in comments]

    tfidf_matrix, feature_names = _fit_tfidf([c for _, c in indexed_non_empty])

    results: list[list[str]] = [[] for _ in comments]
    dense = tfidf_matrix.toarray()
    for row, (original_index, _) in enumerate(indexed_non_empty):
        scores = dense[row]
        # Only keep features this comment actually contains (score > 0);
        # argsort would otherwise pad the list with unrelated zero-score terms.
        nonzero = np.flatnonzero(scores)
        if nonzero.size == 0:
            continue
        ranked = nonzero[np.argsort(scores[nonzero])[::-1]][:top_n]
        results[original_index] = [feature_names[i] for i in ranked]

    return results


def _set_keywords_for_ratings(session, rating_ids) -> int:
    """Write per-comment keywords for each rating. Returns rows updated."""
    from db.models import RmpComment

    updated = 0
    for rating_id in rating_ids:
        comments_for_rating = (
            session.query(RmpComment)
            .filter_by(rmp_rating_id=rating_id)
            .all()
        )
        texts = [c.comment_text or "" for c in comments_for_rating]
        # TF-IDF needs at least two documents to produce meaningful IDF.
        if sum(1 for t in texts if t.strip()) < 2:
            continue

        # Store keywords on *every* comment, not just the first. Tag
        # aggregation gives each comment one vote per tag, so keywords on a
        # single row cap every tag at one vote and the min_count filter drops
        # them all (BUG-4).
        per_comment = extract_keywords_per_comment(texts, top_n=8)
        for comment, keywords in zip(comments_for_rating, per_comment):
            if keywords:
                comment.keywords = keywords
                updated += 1
    return updated


def process_all_comments(session) -> dict:
    """Batch process all unprocessed RMP comments: VADER sentiment + TF-IDF keywords.

    Returns stats dict: {processed, keywords_set}.
    """
    from db.models import RmpComment

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
    stats["keywords_set"] = _set_keywords_for_ratings(session, rating_ids)

    session.commit()
    return stats


def backfill_keywords(session) -> dict:
    """Recompute keywords for comments already processed under the old scheme.

    process_all_comments only touches comments whose sentiment_score is NULL,
    so rows written before the BUG-4 fix keep their single-row keyword layout
    and their professors stay tagless forever. This re-runs extraction across
    every rating that has comments. Safe to run repeatedly.

    Returns stats dict: {ratings, keywords_set}.
    """
    from db.models import RmpComment

    rating_ids = [
        rid
        for (rid,) in session.query(RmpComment.rmp_rating_id).distinct().all()
        if rid is not None
    ]

    keywords_set = _set_keywords_for_ratings(session, rating_ids)
    session.commit()
    return {"ratings": len(rating_ids), "keywords_set": keywords_set}
