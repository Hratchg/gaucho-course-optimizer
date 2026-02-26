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
