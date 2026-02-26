import base64
import json
import random
import time
from typing import Optional


GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"

TEACHER_SEARCH_QUERY = """
query TeacherSearchPaginationQuery($schoolID: ID!, $cursor: String) {
  newSearch {
    teachers(query: {schoolID: $schoolID}, first: 20, after: $cursor) {
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


def parse_teacher_node(node: dict) -> dict:
    """Parse a single teacher node from the GraphQL response."""
    comments = []
    for edge in node.get("ratings", {}).get("edges", []):
        comment_node = edge["node"]
        comments.append({
            "text": comment_node.get("comment", ""),
            "date": comment_node.get("date"),
        })

    return {
        "legacy_id": node["legacyId"],
        "first_name": node["firstName"],
        "last_name": node["lastName"],
        "department": node.get("department", ""),
        "avg_rating": node.get("avgRating"),
        "avg_difficulty": node.get("avgDifficulty"),
        "would_take_again_pct": node.get("wouldTakeAgainPercent"),
        "num_ratings": node.get("numRatings", 0),
        "comments": comments,
    }


class RmpScraper:
    """Scrape RateMyProfessors via their internal GraphQL endpoint."""

    def __init__(self, school_id: int = 1077, auth_token: str = "dGVzdDp0ZXN0"):
        self.school_id = school_id
        self.school_id_encoded = base64.b64encode(f"School-{school_id}".encode()).decode()
        self.auth_token = auth_token

    def _request(self, query: str, variables: dict) -> dict:
        """Make a GraphQL request to RMP. Uses curl_cffi for TLS fingerprint mimicry."""
        from curl_cffi import requests as cffi_requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth_token}",
            "Referer": "https://www.ratemyprofessors.com/",
        }
        payload = json.dumps({"query": query, "variables": variables})
        resp = cffi_requests.post(GRAPHQL_URL, data=payload, headers=headers, impersonate="chrome")
        resp.raise_for_status()
        return resp.json()

    def fetch_all_teachers(self) -> list[dict]:
        """Fetch all teachers for the configured school. Returns list of parsed teacher dicts."""
        teachers = []
        cursor: Optional[str] = None

        while True:
            variables = {"schoolID": self.school_id_encoded}
            if cursor:
                variables["cursor"] = cursor

            data = self._request(TEACHER_SEARCH_QUERY, variables)
            edges = data["data"]["newSearch"]["teachers"]["edges"]

            for edge in edges:
                teachers.append(parse_teacher_node(edge["node"]))

            page_info = data["data"]["newSearch"]["teachers"]["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]

            # Human-like delay
            time.sleep(random.uniform(3, 7))

        return teachers
