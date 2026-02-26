import streamlit as st
import plotly.express as px
from db.connection import get_engine
from sqlalchemy.orm import sessionmaker
from dashboard.queries import search_courses, get_professors_for_course, get_grade_history
from etl.scoring import (
    compute_gaucho_score, normalize_gpa, normalize_quality,
    normalize_difficulty, bayesian_adjust,
)

st.set_page_config(page_title="Gaucho Course Optimizer", page_icon="\U0001f393", layout="wide")
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
    selected_course = None

    if not courses:
        st.warning("No courses found. Try a different search term.")
    elif len(courses) == 1:
        selected_course = courses[0]
    else:
        options = {f"{c['code']} — {c['title'] or 'N/A'}": c for c in courses}
        selected_label = st.selectbox("Select a course:", list(options.keys()))
        selected_course = options[selected_label]

    if selected_course:
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
            for prof in professors:
                score = prof.get("gaucho_score", 0)
                if score >= 70:
                    color = "\U0001f7e2"
                elif score >= 50:
                    color = "\U0001f7e1"
                else:
                    color = "\U0001f534"

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
                            st.write(f"Avg GPA: **{prof['mean_gpa']:.2f}** (+/-{prof['std_gpa'] or 0:.2f})")
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
                    with st.expander(f"Grade history for {prof['name']}"):
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
