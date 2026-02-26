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
