"""Remove wrong RateMyProfessors links from professors. Dry run by default.

Usage:
    python scripts/unlink_rmp.py 5194 6197                # dry run: show what would change
    python scripts/unlink_rmp.py 5194:845193 6197:3049038 # only if still linked to that RMP id
    python scripts/unlink_rmp.py --from-file ids.txt      # one ID or ID:RMP_ID per line, # comments
    python scripts/unlink_rmp.py 5194 --apply             # make the change (one transaction)

Uses DATABASE_URL, like the rest of the pipeline.

What "unlink" does to each professor, and why:

- professors: rmp_id, name_rmp and match_confidence are set to NULL. The row,
  its name_nexus, department, grade history and scheduled sections stay.
  Freeing rmp_id is what lets the weekly refresh give that RMP profile to the
  right professor; load_rmp_teacher_to_db refuses a profile another row holds.
- rmp_ratings and their rmp_comments are deleted. They are the other person's
  ratings, fetched under the wrong link, and the serve-time gate would show
  them again if a later link lifted match_confidence to 85+. The refresh
  fetches fresh ratings for whoever the profile really belongs to.
- gaucho_scores are deleted. They were computed from those ratings, and
  scoring only rewrites scores for linked professors, so they would linger.

With no ratings left the professor counts as stale, so the next weekly
refresh searches RMP for them again. The given-name guard stops it relinking
a profile whose first name conflicts with the Nexus initials. Links the guard
allows (middle-initial or same-initial matches) can come back if the same
profile is still the best-scoring result, so check those after the refresh.

Rows with no Daily Nexus name (RMP-only rows) are skipped: they are the RMP
profile itself, not a link.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.models import GauchoScore, Professor, RmpComment, RmpRating  # noqa: E402


def parse_targets(args: list[str], from_file: str | None = None) -> list[tuple[int, int | None]]:
    """Parse "ID" / "ID:RMP_ID" tokens from the command line and an optional file."""
    tokens = list(args)
    if from_file:
        with open(from_file) as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    tokens.extend(line.split())
    targets = []
    for token in tokens:
        prof_id, _, rmp_id = token.partition(":")
        targets.append((int(prof_id), int(rmp_id) if rmp_id else None))
    return targets


def _rating_ids(session, professor_id: int) -> list[int]:
    return [
        rid for (rid,) in session.query(RmpRating.id).filter_by(professor_id=professor_id)
    ]


def unlink_professors(
    session,
    targets: list[tuple[int, int | None]],
    apply: bool = False,
) -> list[dict]:
    """Plan (and with apply=True, perform) the unlink for each (professor_id, expected_rmp_id).

    expected_rmp_id, when given, must match the professor's current rmp_id or
    the professor is skipped: the link changed since the audit.
    Returns one dict per target with the action taken and the row counts.
    """
    results = []
    for professor_id, expected_rmp_id in targets:
        prof = session.get(Professor, professor_id)
        result = {
            "professor_id": professor_id,
            "name_nexus": prof.name_nexus if prof else None,
            "name_rmp": prof.name_rmp if prof else None,
            "rmp_id": prof.rmp_id if prof else None,
            "match_confidence": prof.match_confidence if prof else None,
            "ratings": 0, "comments": 0, "scores": 0,
        }
        results.append(result)

        if prof is None:
            result["action"] = "skip: no such professor"
            continue
        if prof.rmp_id is None:
            result["action"] = "skip: not linked"
            continue
        if prof.name_nexus is None:
            result["action"] = "skip: RMP-only row (no Nexus name), not a link"
            continue
        if expected_rmp_id is not None and prof.rmp_id != expected_rmp_id:
            result["action"] = (
                f"skip: linked to RMP {prof.rmp_id}, not the expected {expected_rmp_id}"
            )
            continue

        rating_ids = _rating_ids(session, professor_id)
        comments_q = session.query(RmpComment).filter(RmpComment.rmp_rating_id.in_(rating_ids))
        scores_q = session.query(GauchoScore).filter_by(professor_id=professor_id)
        result.update(
            action="unlink",
            ratings=len(rating_ids),
            comments=comments_q.count() if rating_ids else 0,
            scores=scores_q.count(),
        )
        if not apply:
            continue

        if rating_ids:
            comments_q.delete(synchronize_session=False)
            session.query(RmpRating).filter(RmpRating.id.in_(rating_ids)).delete(
                synchronize_session=False
            )
        scores_q.delete(synchronize_session=False)
        prof.rmp_id = None
        prof.name_rmp = None
        prof.match_confidence = None
        session.flush()

    if apply:
        session.commit()
    else:
        session.rollback()
    return results


def _print_report(results: list[dict], apply: bool) -> None:
    print("APPLIED" if apply else "DRY RUN (nothing changed; pass --apply to unlink)")
    for r in results:
        print(
            f"  id={r['professor_id']:<7} {str(r['name_nexus']):<16} -> "
            f"{str(r['name_rmp']):<26} rmp_id={str(r['rmp_id']):<8} "
            f"conf={str(r['match_confidence']):<5} ratings={r['ratings']} "
            f"comments={r['comments']} scores={r['scores']}  {r['action']}"
        )
    done = [r for r in results if r["action"] == "unlink"]
    verb = "Unlinked" if apply else "Would unlink"
    print(
        f"{verb} {len(done)} of {len(results)} professors; "
        f"{'deleted' if apply else 'would delete'} "
        f"{sum(r['ratings'] for r in done)} ratings, "
        f"{sum(r['comments'] for r in done)} comments, "
        f"{sum(r['scores'] for r in done)} scores."
    )


def main(argv: list[str] | None = None, session=None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove wrong RMP links (dry run unless --apply).",
    )
    parser.add_argument("ids", nargs="*", help="professor ids, optionally ID:EXPECTED_RMP_ID")
    parser.add_argument("--from-file", help="file with one ID or ID:RMP_ID per line")
    parser.add_argument("--apply", action="store_true", help="make the change")
    args = parser.parse_args(argv)

    targets = parse_targets(args.ids, args.from_file)
    if not targets:
        parser.error("give at least one professor id")

    own_session = session is None
    if own_session:
        from dotenv import load_dotenv
        from db.connection import get_session

        load_dotenv()
        session = get_session()
    try:
        results = unlink_professors(session, targets, apply=args.apply)
    finally:
        if own_session:
            session.close()
    _print_report(results, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
