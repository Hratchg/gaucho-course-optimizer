# RMP link audit, 2026-09-29

Read-only audit of every professor linked to a RateMyProfessors profile in
production (Neon project `ancient-river-48578866`, default branch `production`,
`br-steep-hill-akgx2zmo`). Nothing on that branch was changed. Triggered by the
2026-09-28 weekly RMP refresh refusing 13 saves because the best RMP profile
was already linked to a different professor.

## Summary

1,023 Daily Nexus professors have an `rmp_id` (plus 346 RMP-only rows, which
are RMP profiles with no Nexus name, not links).

| class | links | served now (match_confidence >= 85) | wrong person's ratings rows / comments | gaucho_scores rows |
|---|---:|---:|---:|---:|
| clearly wrong | 96 | 0 | 111 / 1265 | 784 |
| probably wrong | 31 | 7 | 45 / 431 | 305 |
| plausible (nickname, middle name, compound surname, surname-first RMP profile) | 29 | 2 | | |
| consistent (not suspicious) | 867 | 145 | | |

- **No clearly-wrong link is on the site today.** All 96 score 70-84 and sit
  under the serve-time gate (`is_confident_match` in `etl/name_matcher.py`, used by
  `get_professors_for_course` and `get_comments_for_professor` in `db/queries.py`,
  which `api/routers/courses.py` and `api/routers/professors.py` call).
  They still do damage: each one holds an RMP profile, so the weekly refresh cannot give
  it to the right professor (`load_rmp_teacher_to_db` raises "already linked"), and the
  wrong person's ratings, comments and Gaucho Scores sit on the professor's row.
- **7 probably-wrong links are served now**:
  ZIMMERMAN E D -> Don Zimmerman (id 5540, conf 85), MULFINGER J -> . Mulfinger (id 5787, conf 90), CHEN J -> Chen Ji (id 6618, conf 92), TARIKERE ASHO -> Ashwin Tarikere (id 9905, conf 86), BARACALDO LAN -> Laura Baracaldo (id 10360, conf 86), WALKER Z -> DR Walker (id 10865, conf 86), XIAO L -> Xiao Luo (id 11029, conf 86).
  These need a human look first.
- Clearly-wrong professor ids (96): 5154, 5176, 5194, 5274, 5342, 5395, 5421, 5510, 5547, 5644, 5653, 5676, 5832, 5848, 6099, 6107, 6159, 6197, 6256, 6288, 6998, 7254, 7264, 7356, 7517, 7567, 7592, 7755, 7756, 7778, 7810, 7865, 7971, 8050, 8091, 8370, 8399, 8633, 8660, 8698, 8716, 8717, 8755, 9031, 9214, 9291, 9411, 9423, 9462, 9509, 9720, 9917, 9919, 9935, 10007, 10147, 10231, 10315, 10321, 10329, 10364, 10380, 10431, 10442, 10448, 10467, 10484, 10489, 10528, 10542, 10561, 10586, 10627, 10645, 10661, 10678, 10697, 10728, 10750, 10809, 10821, 10830, 10842, 10878, 10904, 10923, 10947, 10958, 10977, 10998, 11003, 11006, 11009, 11018, 11060, 11096.
  The same list, pinned to the current `rmp_id`, is in
  `docs/audits/2026-09-29-rmp-links-clearly-wrong.txt`; the probably-wrong list is in
  `docs/audits/2026-09-29-rmp-links-probably-wrong.txt`.

## The refresh's 9 reported refusals

| RMP id | linked to now | refresh wanted | verdict |
|---:|---|---|---|
| 1406150 | HAWKER C J (5342, MATRL) as "Harmon C J", conf 70 | HARMON C J (5630, ECON) | **clearly wrong**: the surname differs. HARMON C J should get it. |
| 110288 | BERGSTROM T C (5623, ECON) as "Ted Bergstrom", conf 85 | BERGSTROM R E (5946, HIST) | **existing link is right** (Ted = Theodore C. Bergstrom, Economics). The refresh's match was the wrong one; the new guard rejects it. |
| 845193 | YANG M (5194, RG) as "Tao Yang", conf 71 | YANG T (6246, CMPSC) | **clearly wrong**. YANG T should get it. |
| 1860302 | YANG F (10842, MATH) as "XU Yang", conf 77 | YANG XU (7277, MATH) | **clearly wrong**. YANG XU should get it. |
| 2811373 | ZIMMERMAN E D (5540, ENV) as "Don Zimmerman", conf 85, **served** | ZIMMERMAN D S (10027, RG) | **probably wrong**. D matches E D's middle initial, but ZIMMERMAN D S fits better. The profile has 0 ratings, so nothing is shown yet. |
| 2940701 | CHANG A Y (8091, FAMST) as "Shiyu Chang", conf 70 | CHANG SHIYU (10165, CMPSC); also CHANG YU-CHI (10437, CHIN) | **clearly wrong**. CHANG SHIYU should get it. CHANG YU-CHI was also a wrong match; the guard rejects it. |
| 3049038 | SWEENEY S H (6197, GEOG) as "Ed Sweeney", conf 76 | SWEENEY E (10828, ENV) | **clearly wrong**. SWEENEY E should get it. |
| 2722854 | ZHU ZIMU (10113, PSTAT) as "Zimu Zhu", conf 100 | ZHU ZIMO (10801, PSTAT) | **existing link is right**. ZIMO vs ZIMU scores 88. The refusal protected the right link. The guard does not cover this, because the initials match. |
| 2682036 | RMP-only row 14358 "Ian Duncan" (Mathematics) | DUNCAN I (6602, PSTAT) | **not a link**. DUNCAN I is already linked to another "Ian Duncan" profile (1795165, conf 89). RMP has two profiles for him. The refresh tried to move him to the second one. No action; the unlink script skips RMP-only rows. |

## How the wrong links were made

- 869 of the 1,023 links score 70-84. The 70-84 "review" band in
  `scrapers/targeted_scrape.py` used to write straight to production. DATA-1 stopped new writes
  and hid these links at serve time, but did not remove them. Every clearly-wrong link comes from that band.
- The score is `thefuzz.token_sort_ratio` over the normalised names. It sorts tokens and
  compares characters, so a shared surname dominates and initials barely count: "yang m" vs
  "tao yang" is 71, "bergstrom r e" vs "ted bergstrom" is 85, and "chen j" vs the surname-first
  profile "chen ji" is 92. Nothing checked the given name.
- Paths that can still link a conflicting given name at >= 85 today:
  1. `scrape_active_professors` (weekly refresh): examples at or above 85 are BERGSTROM R E ->
     Ted Bergstrom (85, refused only because the profile was already taken), CHEN J -> "Chen Ji"
     (92, served), XIAO L -> "Xiao Luo" (86, served), WALKER Z -> "DR Walker" (86, served),
     MULFINGER J -> ". Mulfinger" (90, served) and CHANG YU-CHI -> Shiyu Chang (87).
  2. `_pass2_fullname_fuzzy` in `etl/enhanced_matcher.py`. `is_initial_only` is true only for
     one initial, so names like "HAWKER C J" skip passes 1 and 3 (which do check the initial)
     and land in the fuzzy pass, which does not.
- Passes 1 and 3 already require the RMP first initial to match, and are not affected.

## Method

1. Pulled every row with `rmp_id IS NOT NULL` (1,369 rows: 1,023 linked Nexus rows and 346
   RMP-only rows), each with its rating, comment, score and grade counts. The rows came from a Neon
   branch copied from `production` at the time of the audit (`audit-rmp-links-dry-run`). The headline
   counts were checked against `production` with SELECT-only queries (below), and they match.
2. Parsed each Nexus name (`LAST F M`, `LAST FIRST`, `LAST, FIRST`) and RMP name (`First Last`),
   folding accents and splitting hyphens.
3. Surname: some Nexus surname token must share a 4-character prefix (or be equal, if shorter)
   with an RMP surname token. This allows truncation (`CHANDRASEKARA`), hyphenated and compound
   surnames (`READ DE ALANI`, `SAHA RAY R`, `ALVES FERREIR`). If the Nexus surname only matches
   the RMP *first* token, the RMP name is either stored surname-first ("Petzold Linda") or belongs
   to someone whose given name is the Nexus surname ("Nathan Schley" for NATHAN J S).
4. Given name. Nexus tokens that continue a surname are removed first: prefixes of RMP surname
   tokens, particles such as DE/VON/EL, and the second token when Nexus cut the name at 13
   characters. Then:
   - initials only: the RMP first name must start with the first initial (consistent), a middle
     initial (plausible: goes by middle name), or be a nickname of it (Bob/R, Liz/E, Fyl/P,
     Lupita/G and so on; plausible). Anything else is clearly wrong.
   - full given name: a shared 3-letter prefix is consistent. A different name with the same
     initial is probably wrong. A different initial is clearly wrong. A 13-character truncated
     name whose second token may be a surname is probably wrong, because the link rests on one
     surname token.
   - RMP profile with no given name ("DR Walker", ". Mulfinger", "MOLINA ROGERS"): probably wrong.
5. Competing professor: a plausible link is downgraded to probably wrong when another Nexus
   professor with the same surname, who has taught at least once, fits the RMP first name better.
   For example, PORTER S M -> Matt Porter, where PORTER M J teaches MATH in 2026. The "likely owner"
   column lists these professors.
6. Hand review. Every non-consistent row was read. Six classifications were set by hand, from
   known UCSB faculty: Petzold Linda, Janusonis Skirmantas and Ichiba Tomoyuki are stored
   surname-first; W. Hugh Lippincott uses his middle name; "Barbieri Low" is Anthony J.
   Barbieri-Low; SANJAY CHANDR is stored given-name first. "MOLINA ROGERS" was downgraded because
   the profile has no given name.
7. Department. Linked rows only keep the Nexus department code: `_link_professor` and
   `load_rmp_teacher_to_db` do not copy the RMP department. So department disagreement can only be
   checked where an RMP-only row carries the RMP department. That happens for the duplicate RMP
   names listed below. No stored RMP department was available for any clearly-wrong link, so
   department played no part in the classes.
8. One RMP id linked to more than one professor: **0**. The unique index
   `professors_rmp_id_key` prevents it. The same RMP *name* held by more than one row
   (duplicate RMP profiles):

   | RMP name | rows (id, Nexus name, rmp_id, department) |
   |---|---|
   | Ian Duncan | 6602 DUNCAN I 1795165 PSTAT; 14358 RMP-only 2682036 Mathematics |
   | Carole Paul | 6123 PAUL C 351220 ARTHI; 14196 RMP-only 2778592 Art |
   | Greg Siegel | 6560 SIEGEL G D 1003594 FLMST; 14209 RMP-only 2675072 Communication |
   | Matt Beane | 8881 BEANE M I 3077190 TMP; 14282 RMP-only 2605163 Business |
   | Yuksel Aslandogan | 10822 ASLANDOGAN Y 3075870 ECE; 14425 RMP-only 3075807 Computer Science |
   | Mia White | 10661 WHITE J A 1991216 ENV (clearly wrong); 14381 RMP-only 2043570 African-American Studies |
   | Jason Maier, Joan Dudney, Richard Nedjat-Haiem | RMP-only rows only (2, 3 and 2 profiles) |

   In each Nexus-linked pair the departments agree, or are close enough to be the same person
   (PSTAT/Mathematics, ARTHI/Art, TMP/Business). So these are RMP duplicates, not wrong links.
   They explain refusals like DUNCAN I.

## SQL used

Extraction (run on the audit branch; the same SELECT is safe on production):

```sql
SELECT p.id, p.name_nexus, p.name_rmp, p.rmp_id, p.department, p.match_confidence,
       (SELECT count(*) FROM rmp_ratings r WHERE r.professor_id = p.id) AS n_ratings,
       (SELECT r.num_ratings FROM rmp_ratings r WHERE r.professor_id = p.id
         ORDER BY r.id DESC LIMIT 1) AS latest_num,
       (SELECT count(*) FROM rmp_comments c JOIN rmp_ratings r ON r.id = c.rmp_rating_id
         WHERE r.professor_id = p.id) AS n_comments,
       (SELECT count(*) FROM gaucho_scores g WHERE g.professor_id = p.id) AS n_scores,
       (SELECT max(year) FROM grade_distributions g WHERE g.professor_id = p.id) AS last_year
FROM professors p
WHERE p.rmp_id IS NOT NULL
ORDER BY p.id;
```

Same-surname Nexus professors, for the "likely owner" check (`:surnames` = the flagged surnames):

```sql
SELECT p.id, p.name_nexus, p.department, p.rmp_id, p.name_rmp, p.match_confidence,
       (SELECT max(year) FROM grade_distributions g WHERE g.professor_id = p.id) AS last_year
FROM professors p
WHERE p.name_nexus IS NOT NULL
  AND split_part(replace(p.name_nexus, ',', ''), ' ', 1) = ANY(:surnames);
```

Checks run directly on `production` (SELECT only):

```sql
-- link counts by serve-gate band
SELECT CASE WHEN match_confidence IS NULL THEN 'null' WHEN match_confidence >= 85 THEN '>=85'
            WHEN match_confidence >= 70 THEN '70-84' ELSE '<70' END AS band, count(*)
FROM professors WHERE rmp_id IS NOT NULL AND name_nexus IS NOT NULL GROUP BY 1;
-- 70-84: 869, >=85: 154

-- rmp_id held by more than one professor
SELECT rmp_id FROM professors WHERE rmp_id IS NOT NULL GROUP BY rmp_id HAVING count(*) > 1;
-- 0 rows

-- initials-only Nexus names whose RMP first initial conflicts (pure-SQL version of the main rule)
WITH linked AS (
  SELECT p.id, p.name_nexus, p.name_rmp, p.rmp_id, p.match_confidence,
         split_part(p.name_nexus, ' ', 1) AS nx_surname,
         string_to_array(lower(regexp_replace(p.name_nexus, '^\S+\s*', '')), ' ') AS nx_initials,
         lower(left(regexp_replace(trim(p.name_rmp), '^(dr\.?|prof\.?)\s+', '', 'i'), 1)) AS rmp_first_initial,
         lower(regexp_replace(trim(p.name_rmp), '^\S+\s*', '')) AS rmp_after_first
  FROM professors p
  WHERE p.rmp_id IS NOT NULL AND p.name_nexus IS NOT NULL
    AND p.name_nexus ~ '^[^ ,]+( [A-Z])+$'
)
SELECT count(*) AS initials_only_links,                                                    -- 914
       count(*) FILTER (WHERE NOT (rmp_first_initial = ANY (nx_initials))) AS conflicts,  -- 109
       count(*) FILTER (WHERE rmp_first_initial <> nx_initials[1]
                          AND rmp_first_initial = ANY (nx_initials)) AS middle_initial,   -- 32
       count(*) FILTER (WHERE rmp_after_first NOT LIKE '%' || lower(left(nx_surname, 4)) || '%')
         AS surname_not_in_rmp_surname,                                                   -- 27
       count(*) FILTER (WHERE NOT (rmp_first_initial = ANY (nx_initials))
                          AND match_confidence >= 85) AS conflicts_served                 -- 4
FROM linked;
-- the 4 served: 5787 MULFINGER J / ". Mulfinger", 6618 CHEN J / "Chen Ji",
--               10865 WALKER Z / "DR Walker", 11029 XIAO L / "Xiao Luo"
```

The 109 SQL conflicts are the initials-only part of the classes above. Most are clearly wrong. The
rest are nicknames, surname-first RMP profiles, or RMP profiles with no given name, which the
hand review put into plausible or probably wrong.

## The guard added with this audit

`given_name_conflict(nexus_name, rmp_first, rmp_last)` in `etl/name_utils.py` now runs before
scoring in `scrape_active_professors` and `_pass2_fullname_fuzzy`. When Nexus gives initials, the
RMP first name must start with one of them; a middle initial counts. When Nexus gives a full given
name, a different initial is only accepted if the token is really a surname fragment or a later
given name. Run against the 1,023 existing links it would reject:

| class | rejected by the guard | allowed |
|---|---:|---:|
| clearly wrong | 94 | 2 (THOMAS C T -> Thomas Pettus, ALEXANDER A S -> Alexander Swan: the Nexus surname is the RMP given name and an initial matches by chance) |
| probably wrong | 10 | 21 |
| plausible | 11 (nicknames, surname-first profiles, Lippincott; all score below 85 anyway) | 18 |
| consistent | 0 | 867 |

## Remediation

`scripts/unlink_rmp.py` unlinks professors. It runs as a dry run unless you pass `--apply`. The
script's docstring explains what unlinking changes and why. In short: `rmp_id`, `name_rmp` and
`match_confidence` become NULL. The professor's `rmp_ratings`, their `rmp_comments` and the
professor's `gaucho_scores` are deleted. Grades and scheduled sections are kept. The next weekly
refresh then searches RMP for the professor again, and the freed profile can be linked to the
right person.

```sh
python scripts/unlink_rmp.py --from-file docs/audits/2026-09-29-rmp-links-clearly-wrong.txt          # dry run
python scripts/unlink_rmp.py --from-file docs/audits/2026-09-29-rmp-links-clearly-wrong.txt --apply  # unlink
```

The id files pin each professor to the `rmp_id` the audit saw (`5194:845193`). A link that has
changed since the audit is skipped. On the `audit-rmp-links-dry-run` branch, the clearly-wrong
list (97 ids at the time; MADRIGAL G was reclassified as plausible afterwards, Lupita being short
for Guadalupe) unlinked 97 professors. It deleted 113 ratings, 1,273 comments and 786 score rows.
A second dry run then found nothing left to do. Linked Nexus rows went from 1,023 to 926 on the
branch, and production still has 1,023.

## Other finding (not fixed here)

`professors` has 92,341 rows with a Nexus name but only 6,829 distinct names. 84,450 rows have no
grades and no scheduled sections. For example, "HARMON C J" appears on about 100 rows, and only
id 5630 has grades. `ucsb_api/schedule_sync.py` `_auto_create_professor` looks like the source.
This does not affect the links above, but it inflates every professor scan, including
`_get_unmatched_nexus` and pass 4.

## Clearly wrong (96)

| id | Nexus name | Nexus dept | RMP name | rmp_id | conf | served | ratings / comments | why | likely owner of the RMP profile |
|---:|---|---|---|---:|---:|:-:|---:|---|---|
| 8717 | CHRISTOPHER P | CH | Christopher Parker | 2638009 | 84 |  | 24 / 20 | Nexus surname only matches the RMP given name "Christopher" (a given name on other RMP profiles); the Nexus initial matching "Parker" is a coincidence |  |
| 8716 | RODRIGUEZ C H | CH | R Rodriguez | 1184514 | 83 |  | 3 / 3 | RMP initial R conflicts with Nexus initials C H |  |
| 10329 | ANDERSON O E | EARTH | Bob Anderson | 409420 | 83 |  | 231 / 40 | RMP first name "Bob" conflicts with Nexus initials O E |  |
| 6159 | CARLSON J M | PHYS | Tom Carlson | 569952 | 82 |  | 43 / 20 | RMP first name "Tom" conflicts with Nexus initials J M | CARLSON T A (id=5201, RG, last taught 2026) |
| 6256 | WEBER E | C | Rene Weber | 962184 | 82 |  | 53 / 20 | RMP first name "Rene" conflicts with Nexus initials E | WEBER R (id=5681, COMM, last taught 2026) |
| 7810 | WOLFSON E R | RG | Ben Wolfson | 1684178 | 82 |  | 4 / 4 | RMP first name "Ben" conflicts with Nexus initials E R | WOLFSON B A (id=6891, PHIL, last taught 2012) |
| 7971 | ROBERTS S A | ED | Dar Roberts | 463564 | 82 |  | 25 / 20 | RMP first name "Dar" conflicts with Nexus initials S A | ROBERTS D A (id=6194, GEOG, last taught 2026) |
| 10977 | TRUMBLE E K | EACS | Ben Trumble | 1981587 | 82 |  | 1 / 1 | RMP first name "Ben" conflicts with Nexus initials E K | TRUMBLE B C (id=7802, ANTH, last taught 2014) |
| 7517 | SCHNEIDER C A | ED | Nick Schneider | 583502 | 81 |  | 31 / 20 | RMP first name "Nick" conflicts with Nexus initials C A | SCHNEIDER N J (id=6046, ECON, last taught 2023) |
| 10697 | ALEXANDER A S | PSY | Alexander Swan | 1748491 | 81 |  | 17 / 17 | Nexus surname only matches the RMP given name "Alexander"; RMP surname "Swan" is a different person | ALEXANDER A (id=8275, ARTHI, last taught 2017) |
| 5653 | ROSE K | ECE | Mark Rose | 383414 | 80 |  | 40 / 20 | RMP first name "Mark" conflicts with Nexus initials K | ROSE M A (id=5558, ENGL, last taught 2020) |
| 9720 | DOUGLAS P L | INT | Douglas Kulper | 762307 | 80 |  | 55 / 20 | Nexus surname only matches the RMP given name "Douglas"; RMP surname "Kulper" is a different person |  |
| 10321 | FERNANDEZ M | ED | Leah Fernandez | 2422058 | 80 |  | 20 / 40 | RMP first name "Leah" conflicts with Nexus initials M | FERNANDEZ L (id=6344, HIST, last taught 2020) |
| 10528 | NGUYEN C | INT | Alice Nguyen | 2109478 | 80 |  | 83 / 20 | RMP first name "Alice" conflicts with Nexus initials C | NGUYEN A (id=8997, MCDB, last taught 2018); NGUYEN A T (id=7001, EEMB, last taught 2025) |
| 10998 | WILLIS L | INT | Chloe Willis | 2656017 | 80 |  | 2 / 2 | RMP first name "Chloe" conflicts with Nexus initials L | WILLIS C M (id=9830, LING, last taught 2020) |
| 10231 | MCLAUGHLIN J | EEMB | Kayla McLaughlin | 1837313 | 79 |  | 14 / 14 | RMP first name "Kayla" conflicts with Nexus initials J | MCLAUGHLIN K (id=7642, SPAN, last taught 2014) |
| 6998 | BROWN M S | ENV | Tim Brown | 1440546 | 78 |  | 1 / 1 | RMP first name "Tim" conflicts with Nexus initials M S | BROWN T M (id=6160, PHYS, last taught 2012) |
| 7865 | YOUNG A F | PHYS | Kay Young | 204377 | 78 |  | 29 / 20 | RMP first name "Kay" conflicts with Nexus initials A F | YOUNG K (id=5554, ENGL, last taught 2021) |
| 10315 | AHMED N S | ENGL | Ahmed Asi | 2464893 | 78 |  | 5 / 5 | Nexus surname only matches the RMP given name "Ahmed"; RMP surname "Asi" is a different person |  |
| 10431 | MARTIN D | ECON | Jen Martin | 1981967 | 78 |  | 89 / 20 | RMP first name "Jen" conflicts with Nexus initials D | MARTIN J (id=101046, HIST, last taught 2013); MARTIN J A (id=7688, HIST, last taught 2026) |
| 10484 | ROBERTS C K | WRIT | Luke Roberts | 315248 | 78 |  | 68 / 20 | RMP first name "Luke" conflicts with Nexus initials C K |  |
| 10661 | WHITE J A | ENV | Mia White | 1991216 | 78 |  | 12 / 12 | RMP first name "Mia" conflicts with Nexus initials J A | WHITE M C (id=7629, BL, last taught 2016) |
| 11018 | NGUYEN G | MATH | Huy Nguyen | 2272432 | 78 |  | 12 / 12 | RMP first name "Huy" conflicts with Nexus initials G | NGUYEN H X (id=8564, ECON, last taught 2017) |
| 9935 | THOMPSON M E | CNCSP | Keith Thompson | 1519338 | 77 |  | 1 / 2 | RMP first name "Keith" conflicts with Nexus initials M E | THOMPSON K C (id=5913, MATH, last taught 2011) |
| 10380 | BANERJEE T | FAMST | Kaustav Banerjee | 757949 | 77 |  | 9 / 9 | RMP first name "Kaustav" conflicts with Nexus initials T | BANERJEE K (id=5642, ECE, last taught 2026) |
| 10842 | YANG F | MATH | XU Yang | 1860302 | 77 |  | 24 / 20 | RMP first name "Xu" conflicts with Nexus initials F | YANG XU (id=7277, MATH, last taught 2026) |
| 5510 | HANNAH L J | ESM | Hannah Wohl | 2464708 | 76 |  | 13 / 13 | Nexus surname only matches the RMP given name "Hannah"; RMP surname "Wohl" is a different person |  |
| 5644 | BOWERS J E | ECE | Mike Bowers | 823927 | 76 |  | 32 / 20 | RMP first name "Mike" conflicts with Nexus initials J E | BOWERS M T (id=6085, CHEM, last taught 2026) |
| 6197 | SWEENEY S H | GEOG | Ed Sweeney | 3049038 | 76 |  | 1 / 1 | RMP first name "Ed" conflicts with Nexus initials S H | SWEENEY E (id=10828, ENV, last taught 2026) |
| 9423 | STEIN E A | POL | Daniel Stein | 2483526 | 76 |  | 1 / 1 | RMP first name "Daniel" conflicts with Nexus initials E A | STEIN D A (id=8286, THTR, last taught 2026) |
| 5395 | KENNEDY R A | LING | Grace Kennedy | 1618627 | 75 |  | 1 / 1 | RMP first name "Grace" conflicts with Nexus initials R A |  |
| 5421 | DIGESER E D | HIST | Paige Digeser | 333925 | 75 |  | 68 / 20 | RMP first name "Paige" conflicts with Nexus initials E D | DIGESER P (id=5235, POL, last taught 2022) |
| 7254 | PRICE S P | CHEM | Z Price | 1208604 | 75 |  | 5 / 5 | RMP initial Z conflicts with Nexus initials S P |  |
| 9031 | JACK B K | ESM | Jack Erb | 1381568 | 75 |  | 3 / 3 | Nexus surname only matches the RMP given name "Jack"; RMP surname "Erb" is a different person |  |
| 9462 | SPENCER M H | FEMST | Spencer Smith | 2918454 | 75 |  | 12 / 12 | Nexus surname only matches the RMP given name "Spencer"; RMP surname "Smith" is a different person |  |
| 9919 | ADAMS B | HIST | Ann Adams | 676196 | 75 |  | 38 / 40 | RMP first name "Ann" conflicts with Nexus initials B | ADAMS A J (id=5800, ARTHI, last taught 2023); ADAMS A R (id=10961, ESM, last taught 2025) |
| 5154 | MORGAN M | THTR | Doug Morgan | 59021 | 74 |  | 50 / 20 | RMP first name "Doug" conflicts with Nexus initials M |  |
| 5176 | ROBINSON W I | SOC | Cedric Robinson | 166062 | 74 |  | 28 / 20 | RMP first name "Cedric" conflicts with Nexus initials W I | ROBINSON C J (id=5781, BL, last taught 2015) |
| 8633 | WILLIAMS D L | ENV | Alison Williams | 2450766 | 74 |  | 13 / 13 | RMP first name "Alison" conflicts with Nexus initials D L | WILLIAMS A (id=5520, ES, last taught 2020); WILLIAMS A K (id=9123, CHEM, last taught 2019) |
| 10627 | SALEH A A | BMSE | Omar Saleh | 789324 | 74 |  | 4 / 4 | RMP first name "Omar" conflicts with Nexus initials A A | SALEH O A (id=5352, MATRL, last taught 2026) |
| 10678 | PANDEY P | PSTAT | Kanu Pandey | 3012426 | 74 |  | 9 / 9 | RMP first name "Kanu" conflicts with Nexus initials P | PANDEY K (id=10702, COMM, last taught 2026) |
| 5848 | THOMAS C M | RG | Thomas Moody | 2960957 | 73 |  | 7 / 7 | Nexus surname only matches the RMP given name "Thomas"; RMP surname "Moody" is a different person |  |
| 6288 | RAYMOND G | SOC | Elena Raymond | 2198952 | 73 |  | 53 / 40 | RMP first name "Elena" conflicts with Nexus initials G | RAYMOND E (id=8067, SOC, last taught 2026) |
| 7778 | COTTER E E | ESM | Peggy Cotter | 1081052 | 73 |  | 9 / 18 | RMP first name "Peggy" conflicts with Nexus initials E E |  |
| 8399 | PERRONE G | HIST | Debra Perrone | 2654734 | 73 |  | 13 / 13 | RMP first name "Debra" conflicts with Nexus initials G | PERRONE D (id=8740, ENV, last taught 2026) |
| 9291 | SPRAGUE T C | PSY | Sprague Jeb | 1459222 | 73 |  | 5 / 5 | Nexus surname only matches the RMP given name "Sprague"; RMP surname "Jeb" is a different person |  |
| 9411 | TAYLOR C M | PSY | Taylor Moore | 3075017 | 73 |  | 2 / 2 | Nexus surname only matches the RMP given name "Taylor"; RMP surname "Moore" is a different person |  |
| 10007 | NELSON T A | GEOG | Harry Nelson | 224351 | 73 |  | 24 / 20 | RMP first name "Harry" conflicts with Nexus initials T A | NELSON H (id=6162, PHYS, last taught 2026) |
| 10561 | RAMIREZ Y | CNCSP | Roque Ramirez | 810995 | 73 |  | 4 / 4 | RMP first name "Roque" conflicts with Nexus initials Y |  |
| 10645 | BURNETT M D | BL | Les Burnett | 1845726 | 73 |  | 4 / 4 | RMP first name "Les" conflicts with Nexus initials M D |  |
| 10728 | GUO W | CMPSC | Guo Yu | 2631936 | 73 |  | 29 / 20 | Nexus surname only matches the RMP given name "Guo"; RMP surname "Yu" is a different person |  |
| 10750 | MILLER L B | COMM | Karly Miller | 2803226 | 73 |  | 7 / 7 | RMP first name "Karly" conflicts with Nexus initials L B | MILLER K M (id=10224, GEOG, last taught 2026) |
| 11006 | MILLETT R M | MAT | Ken Millett | 494641 | 73 |  | 46 / 20 | RMP first name "Ken" conflicts with Nexus initials R M | MILLETT K C (id=5368, MATH, last taught 2020) |
| 7592 | BERNARD M A | THTR | Bernard Comrie | 586093 | 72 |  | 7 / 14 | Nexus surname only matches the RMP given name "Bernard"; RMP surname "Comrie" is a different person |  |
| 8660 | GONZALEZ J H | RG | Nino Gonzalez | 2496787 | 72 |  | 13 / 13 | RMP first name "Nino" conflicts with Nexus initials J H | GONZALEZ N (id=10790, MATH, last taught 2024); GONZALEZ NINO (id=8022, MCDB, last taught 2026) |
| 10542 | WATERS E A | GEOG | Diamante Waters | 1856939 | 72 |  | 2 / 2 | RMP first name "Diamante" conflicts with Nexus initials E A |  |
| 10830 | CALLAHAN D | ENV | Manual Callahan | 1337298 | 72 |  | 1 / 2 | RMP first name "Manual" conflicts with Nexus initials D | CALLAHAN M (id=6091, CH, last taught 2011) |
| 10904 | JOHNSON L D | MUS | Edmond Johnson | 1038307 | 72 |  | 27 / 20 | RMP first name "Edmond" conflicts with Nexus initials L D |  |
| 5194 | YANG M | RG | Tao Yang | 845193 | 71 |  | 17 / 17 | RMP first name "Tao" conflicts with Nexus initials M | YANG T (id=6246, CMPSC, last taught 2026) |
| 5547 | LIU A Y | ENGL | Lan Liu | 2163119 | 71 |  | 1 / 1 | RMP first name "Lan" conflicts with Nexus initials A Y | LIU L (id=8217, MATH, last taught 2017) |
| 6107 | ZHAO X | AS | Ben Zhao | 539490 | 71 |  | 18 / 36 | RMP first name "Ben" conflicts with Nexus initials X | ZHAO B (id=8057, BMSE, last taught 2015); ZHAO B Y (id=5704, CMPSC, last taught 2019) |
| 7356 | GRAY S M | SOC | Lisa Gray | 1997578 | 71 |  | 8 / 16 | RMP first name "Lisa" conflicts with Nexus initials S M | GRAY L A (id=7844, ECON, last taught 2018) |
| 8050 | SANCHEZ C A | DANCE | Micaela Diaz Sanchez | 2153389 | 71 |  | 21 / 20 | RMP first name "Micaela" conflicts with Nexus initials C A | SANCHEZ M (id=9669, CHEM, last taught 2019) |
| 10442 | JONES B | BL | Alie Jones | 2741878 | 71 |  | 0 / 0 | RMP first name "Alie" conflicts with Nexus initials B | JONES A T (id=7842, ECON, last taught 2015) |
| 10448 | WILLIAMS R C | THTR | Deborah Williams | 2450102 | 71 |  | 5 / 5 | RMP first name "Deborah" conflicts with Nexus initials R C |  |
| 10586 | ZHANG J | ECON | Qing Zhang | 2947498 | 71 |  | 19 / 19 | RMP first name "Qing" conflicts with Nexus initials J | ZHANG Q (id=10601, MATH, last taught 2025) |
| 10958 | CHEN TED | TMP | Eric Chen | 2543407 | 71 |  | 27 / 20 | different given names ("TED" vs "Eric") | CHEN E (id=9564, MATH, last taught 2021) |
| 5274 | NATHAN J S | MUS | Nathan Schley | 1984011 | 70 |  | 132 / 20 | Nexus surname only matches the RMP given name "Nathan"; RMP surname "Schley" is a different person |  |
| 5342 | HAWKER C J | MATRL | Harmon C J | 1406150 | 70 |  | 3 / 3 | Nexus surname does not appear in the RMP name |  |
| 5676 | AFIFI T D | COMM | Walid Afifi | 933080 | 70 |  | 62 / 20 | RMP first name "Walid" conflicts with Nexus initials T D | AFIFI W A (id=5675, COMM, last taught 2026) |
| 5832 | SEGURA D A | SOC | Nathan Segura | 2813586 | 70 |  | 6 / 6 | RMP first name "Nathan" conflicts with Nexus initials D A |  |
| 6099 | STEWART J C | BL | Earl Stewart | 1251959 | 70 |  | 20 / 20 | RMP first name "Earl" conflicts with Nexus initials J C | STEWART E L (id=5777, BL, last taught 2016) |
| 7264 | WOODS V E | PSY | Clyde Woods | 849882 | 70 |  | 6 / 6 | RMP first name "Clyde" conflicts with Nexus initials V E | WOODS C A (id=5776, BL, last taught 2011) |
| 7567 | YOUNG H S | EEMB | Chun-Jan Young | 2875880 | 70 |  | 2 / 2 | RMP first name "Chun" conflicts with Nexus initials H S | YOUNG C (id=10221, LING, last taught 2026) |
| 7755 | SMITH S L | ME | Haley Smith | 2706607 | 70 |  | 6 / 12 | RMP first name "Haley" conflicts with Nexus initials S L | SMITH H M (id=9308, MCDB, last taught 2021) |
| 7756 | WILSON S D | MATRL | Justin Wilson | 3150990 | 70 |  | 10 / 10 | RMP first name "Justin" conflicts with Nexus initials S D | WILSON J R (id=7046, ESM, last taught 2012) |
| 8091 | CHANG A Y | FAMST | Shiyu Chang | 2940701 | 70 |  | 3 / 3 | RMP first name "Shiyu" conflicts with Nexus initials A Y | CHANG S (id=101071, CMPSC, last taught 2023); CHANG SHIYU (id=10165, CMPSC, last taught 2025) |
| 8370 | HARRIS O | THTR | Sabra Harris | 3012848 | 70 |  | 2 / 4 | RMP first name "Sabra" conflicts with Nexus initials O | HARRIS S (id=7418, FLMST, last taught 2013); HARRIS S M (id=7414, GEOG, last taught 2016); HARRIS S Y (id=8833, ED, last taught 2024) |
| 8698 | ANDREA B D | ENGL | Andrea Medina | 2557157 | 70 |  | 2 / 2 | Nexus surname only matches the RMP given name "Andrea"; RMP surname "Medina" is a different person |  |
| 8755 | FRANK D M | WRIT | Frank Dutra | 570392 | 70 |  | 24 / 40 | Nexus surname only matches the RMP given name "Frank" (a given name on other RMP profiles); the Nexus initial matching "Dutra" is a coincidence |  |
| 9214 | EVERETT C J | EEMB | Anna Everett | 296137 | 70 |  | 12 / 12 | RMP first name "Anna" conflicts with Nexus initials C J | EVERETT A (id=5983, FLMST, last taught 2022) |
| 9509 | CARTER M L | SPAN | Delwin Carter | 2621758 | 70 |  | 1 / 1 | RMP first name "Delwin" conflicts with Nexus initials M L | CARTER D B (id=9800, PSY, last taught 2026) |
| 9917 | MOORE K A | HIST | Laura Moore | 2137644 | 70 |  | 2 / 2 | RMP first name "Laura" conflicts with Nexus initials K A | MOORE L B (id=8230, HIST, last taught 2017) |
| 10147 | THOMAS C T | ENGL | Thomas Pettus | 335426 | 70 |  | 72 / 20 | Nexus surname only matches the RMP given name "Thomas"; RMP surname "Pettus" is a different person |  |
| 10364 | SUNG B O | MATH | Sung Soo Kim | 2671866 | 70 |  | 4 / 4 | Nexus surname only matches the RMP given name "Sung"; RMP surname "Soo Kim" is a different person |  |
| 10467 | SNYDER C L | ESM | Jon Snyder | 157425 | 70 |  | 31 / 20 | RMP first name "Jon" conflicts with Nexus initials C L | SNYDER J R (id=5927, ITAL, last taught 2019) |
| 10489 | DAVID J S | SOC | David Stone | 1676569 | 70 |  | 21 / 20 | Nexus surname only matches the RMP given name "David"; RMP surname "Stone" is a different person |  |
| 10809 | KAPLAN K H | RG | Ari Kaplan | 2776040 | 70 |  | 1 / 1 | RMP first name "Ari" conflicts with Nexus initials K H | KAPLAN A K (id=8921, PHYS, last taught 2022) |
| 10821 | PEARSON A | DANCE | Justin Pearson | 1905324 | 70 |  | 14 / 14 | RMP first name "Justin" conflicts with Nexus initials A | PEARSON J (id=5667, DANCE, last taught 2016) |
| 10878 | CHAPMAN D A | BL | Kyle Chapman | 2054236 | 70 |  | 47 / 20 | RMP first name "Kyle" conflicts with Nexus initials D A | CHAPMAN K L (id=7122, MATH, last taught 2016) |
| 10923 | BECKMAN C | TMP | Laurel Beckman | 522867 | 70 |  | 14 / 14 | RMP first name "Laurel" conflicts with Nexus initials C | BECKMAN L B (id=5794, ARTST, last taught 2022) |
| 10947 | ZHAO LIANG | PHYS | Xiaojian Zhao | 109015 | 70 |  | 70 / 20 | different given names ("LIANG" vs "Xiaojian") |  |
| 11003 | WHEELER B M | INT | Sara Wheeler | 455026 | 70 |  | 14 / 14 | RMP first name "Sara" conflicts with Nexus initials B M | WHEELER S A (id=5442, HEB, last taught 2013) |
| 11009 | KEITH M T | MATH | Keith Mayes | 3107422 | 70 |  | 2 / 4 | Nexus surname only matches the RMP given name "Keith" (a given name on other RMP profiles); the Nexus initial matching "Mayes" is a coincidence |  |
| 11060 | OLGUIN D S | ECON | Ben Olguin | 2383501 | 70 |  | 22 / 20 | RMP first name "Ben" conflicts with Nexus initials D S | OLGUIN B V (id=8696, ENGL, last taught 2026) |
| 11096 | DAVIS S A | ESM | David Davis | 1751884 | 70 |  | 2 / 2 | RMP first name "David" conflicts with Nexus initials S A |  |

## Probably wrong (31)

| id | Nexus name | Nexus dept | RMP name | rmp_id | conf | served | ratings / comments | why | likely owner of the RMP profile |
|---:|---|---|---|---:|---:|:-:|---:|---|---|
| 6618 | CHEN J | MATH | Chen Ji | 1992617 | 92 | yes | 7 / 14 | RMP name looks stored surname-first; Nexus initial matches the RMP last token, but that reading needs the RMP profile to confirm | CHEN C (id=101063, MUS, last taught 2019) |
| 5787 | MULFINGER J | ARTST | . Mulfinger | 1034218 | 90 | yes | 5 / 10 | RMP profile has no given name to check against the Nexus initials |  |
| 9905 | TARIKERE ASHO | MATH | Ashwin Tarikere | 2640789 | 86 | yes | 43 / 40 | Nexus name is cut at 13 characters, so "ASHO" may be the rest of a compound surname rather than a given name; RMP "Ashwin Tarikere" has neither, so the link rests on one surname token |  |
| 10360 | BARACALDO LAN | PSTAT | Laura Baracaldo | 2843432 | 86 | yes | 27 / 60 | Nexus name is cut at 13 characters, so "LAN" may be the rest of a compound surname rather than a given name; RMP "Laura Baracaldo" has neither, so the link rests on one surname token |  |
| 10865 | WALKER Z | CMPSC | DR Walker | 1629752 | 86 | yes | 1 / 2 | RMP profile has no given name to check against the Nexus initials |  |
| 11029 | XIAO L | PSTATW | Xiao Luo | 2915832 | 86 | yes | 7 / 14 | RMP name looks stored surname-first; Nexus initial matches the RMP last token, but that reading needs the RMP profile to confirm | XIAO X (id=7796, CHIN, last taught 2016) |
| 5540 | ZIMMERMAN E D | ENV | Don Zimmerman | 2811373 | 85 | yes | 0 / 0 | RMP first name "Don" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | ZIMMERMAN D S (id=10027, RG, last taught 2024) |
| 8373 | ALVES FERREIR | SPAN | Aline Ferreira | 2353893 | 81 |  | 7 / 7 | compound surname; RMP keeps only the second part; no Nexus given name to check; another Nexus professor fits the RMP first name better | ALVES A R (id=9983, BL, last taught 2021) |
| 10206 | THOMPSON GONZ | ANTH | Amoni Thompson | 2559798 | 81 |  | 1 / 8 | Nexus name is cut at 13 characters, so "GONZ" may be the rest of a compound surname rather than a given name; RMP "Amoni Thompson" has neither, so the link rests on one surname token |  |
| 6938 | BROOKS A J | EEMB | J F Brooks | 1982826 | 80 |  | 2 / 4 | RMP first name "J" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | BROOKS J F (id=7227, HIST, last taught 2019) |
| 5685 | SMITH S R | CNCSP | Roy Smith | 886081 | 78 |  | 7 / 7 | RMP first name "Roy" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | SMITH R S (id=5311, ME, last taught 2010) |
| 8043 | COHEN N A | ENV | Ami Cohen | 1404439 | 78 |  | 11 / 22 | RMP first name "Ami" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | COHEN A P (id=9213, EEMB, last taught 2019); COHEN A S (id=6720, PSY, last taught 2011) |
| 9704 | JOHNSON M J | RG | John Johnson | 972966 | 78 |  | 13 / 13 | RMP first name "John" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | JOHNSON J A (id=10020, WRIT, last taught 2021); JOHNSON J K (id=5821, WRIT, last taught 2026); JOHNSON J M (id=7004, ECE, last taught 2021) |
| 11002 | JOHNSON C A | INT | Alli Johnson | 2188434 | 78 |  | 14 / 14 | RMP first name "Alli" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | JOHNSON A M (id=8282, WRIT, last taught 2018); JOHNSON A Y (id=9811, POL, last taught 2020) |
| 8880 | WILLIAMS A M | WRIT | Megan Williams | 2818268 | 77 |  | 1 / 2 | RMP first name "Megan" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | WILLIAMS M J (id=6328, MATH, last taught 2010); WILLIAMS M L (id=9819, MUS, last taught 2022) |
| 10858 | MARTINEZ CERN | SPAN | Espa Martinez | 2163230 | 77 |  | 1 / 1 | Nexus name is cut at 13 characters, so "CERN" may be the rest of a compound surname rather than a given name; RMP "Espa Martinez" has neither, so the link rests on one surname token | MARTINEZ ESPA (id=8024, MATH, last taught 2018) |
| 6193 | PORTER S M | GEOL | Matt Porter | 1857546 | 76 |  | 310 / 20 | RMP first name "Matt" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | PORTER M J (id=7390, MATH, last taught 2026) |
| 10183 | MILLER M J | INT | Jack Miller | 2889823 | 76 |  | 49 / 20 | RMP first name "Jack" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | MILLER J B (id=10407, PSTAT, last taught 2026); MILLER J E (id=9733, ENGL, last taught 2020); MILLER J K (id=10636, ESM, last taught 2023) |
| 10423 | MURRAY D A | ESM | Alan Murray | 2688419 | 76 |  | 1 / 1 | RMP first name "Alan" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | MURRAY A (id=8143, GEOG, last taught 2026) |
| 10974 | WANG MINGHUI | COMM | Mian Wang | 2669943 | 76 |  | 3 / 3 | different given names with the same initial ("MINGHUI" vs "Mian") | WANG M (id=6031, ED, last taught 2026) |
| 5438 | ROBERTS L S | HIST | Sarah Roberts | 1579697 | 75 |  | 18 / 36 | RMP first name "Sarah" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | ROBERTS S C (id=6639, FR, last taught 2021) |
| 7062 | HIRSCH S A | ENGL | . Hirsch | 878357 | 75 |  | 11 / 11 | RMP profile has no given name to check against the Nexus initials |  |
| 8915 | CRAVEIRO DE M | PORT | Pedro Craveiro | 2238787 | 74 |  | 46 / 20 | Nexus name is cut at 13 characters, so "DE M" may be the rest of a compound surname rather than a given name; RMP "Pedro Craveiro" has neither, so the link rests on one surname token |  |
| 10522 | KIM HAEWON | KOR | Henry Kim | 1967189 | 74 |  | 7 / 14 | different given names with the same initial ("HAEWON" vs "Henry") | KIM H A (id=7748, POL, last taught 2015); KIM H S (id=5216, PSY, last taught 2026) |
| 9920 | JACOBS R E | GLOBL | Emily Jacobs | 2238451 | 73 |  | 18 / 18 | RMP first name "Emily" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | JACOBS E (id=8379, PSY, last taught 2026) |
| 10719 | HARRIS S D | JAPAN | David Harris | 12659 | 73 |  | 51 / 20 | RMP first name "David" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | HARRIS D R (id=10173, WRIT, last taught 2026) |
| 10888 | MARTINEZ GUTI | EARTH | Amy Martinez | 2837674 | 72 |  | 17 / 17 | Nexus name is cut at 13 characters, so "GUTI" may be the rest of a compound surname rather than a given name; RMP "Amy Martinez" has neither, so the link rests on one surname token | MARTINEZ A A (id=10356, SOC, last taught 2026) |
| 5124 | DEAN C W | WRIT | Dean Chen | 1504296 | 71 |  | 11 / 11 | RMP name looks stored surname-first; Nexus initial matches the RMP last token, but that reading needs the RMP profile to confirm |  |
| 6269 | SMITH S T | ANTH | Terry Smith | 593229 | 70 |  | 11 / 11 | RMP first name "Terry" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | SMITH T R (id=5473, GEOG, last taught 2010) |
| 8033 | WHITE K D | GER | David White | 2095253 | 70 |  | 9 / 9 | RMP first name "David" matches a Nexus middle initial (goes by middle name); another Nexus professor fits the RMP first name better | WHITE D G (id=5195, RG, last taught 2021); WHITE D W (id=9689, ART, last taught 2019) |
| 10019 | ROGERS P M | WRIT | MOLINA ROGERS | 2908059 | 70 |  | 2 / 2 | RMP profile "MOLINA ROGERS" has no given name; the M only matches the Nexus middle initial |  |

## Plausible (29)

| id | Nexus name | Nexus dept | RMP name | rmp_id | conf | served | ratings / comments | why | likely owner of the RMP profile |
|---:|---|---|---|---:|---:|:-:|---:|---|---|
| 6678 | HOWELL D A | ASTRO | Andy Howell | 1692527 | 86 | yes | 6 / 18 | RMP first name "Andy" matches a Nexus middle initial (goes by middle name) |  |
| 9502 | SHEFFIELD C A | THTR | Ann Sheffield | 3019244 | 85 | yes | 0 / 0 | RMP first name "Ann" matches a Nexus middle initial (goes by middle name) |  |
| 5552 | HUANG YU | ENGL | Yunte Huang | 374673 | 84 |  | 73 / 20 | Nexus given "YU" is only a 2-letter prefix of "Yunte" |  |
| 5700 | PETZOLD L | CMPSC | Petzold Linda | 1380586 | 82 |  | 3 / 3 | Linda Petzold (Computer Science); RMP stores the name surname-first |  |
| 6109 | FULBECK L K | ARTST | Kip Fulbeck | 414910 | 82 |  | 51 / 20 | RMP first name "Kip" matches a Nexus middle initial (goes by middle name) |  |
| 9460 | THOMPSON A M | FEMSTW | Miriam Thompson | 3079301 | 81 |  | 1 / 1 | RMP first name "Miriam" matches a Nexus middle initial (goes by middle name) |  |
| 5414 | O'CONNOR A M | INT | Mary O'Connor | 702674 | 80 |  | 6 / 6 | RMP first name "Mary" matches a Nexus middle initial (goes by middle name) |  |
| 5746 | LITTLE R D | CHEM | Dan Little | 646593 | 80 |  | 13 / 26 | RMP first name "Dan" matches a Nexus middle initial (goes by middle name) |  |
| 5399 | RIGHTMIRE S R | LING | Randy Rightmire | 500137 | 79 |  | 30 / 20 | RMP first name "Randy" matches a Nexus middle initial (goes by middle name) |  |
| 6467 | ELIZONDO E S | PHIL | Sonny Elizondo | 1549475 | 77 |  | 15 / 15 | RMP first name "Sonny" matches a Nexus middle initial (goes by middle name) |  |
| 10881 | SANJAY CHANDR | CMPSC | Sanjay Chandrasekaran | 3082586 | 76 |  | 1 / 1 | Nexus stores this name given-name first; RMP surname is the truncated token |  |
| 9725 | CARLISLE E W | GEOG | Liz Carlisle | 2769977 | 75 |  | 5 / 5 | "Liz" is a nickname for a E- name |  |
| 9838 | BARBIERI A J | HIST | Barbieri Low | 1136145 | 75 |  | 5 / 5 | Anthony J. Barbieri-Low (History); RMP split the hyphenated surname into first/last |  |
| 6223 | DUFFY A E | ENGL | Enda Duffy | 218269 | 74 |  | 67 / 20 | RMP first name "Enda" matches a Nexus middle initial (goes by middle name) |  |
| 6470 | WAITE J H | MCDB | Herb Waite | 1588035 | 74 |  | 18 / 18 | RMP first name "Herb" matches a Nexus middle initial (goes by middle name) |  |
| 8684 | DAHL SARNELLI | ITAL | Laura Sarnelli | 2563995 | 74 |  | 12 / 12 | compound surname; RMP keeps only the second part; no Nexus given name to check |  |
| 9709 | LIPPINCOTT W | PHYS | Hugh Lippincott | 2677827 | 74 |  | 6 / 6 | W. Hugh Lippincott (UCSB Physics) goes by his middle name; rare surname, same field |  |
| 5672 | POTTER W J | COMM | James Potter | 290333 | 73 |  | 58 / 20 | RMP first name "James" matches a Nexus middle initial (goes by middle name) |  |
| 6275 | SAMUELS R D | WRIT | Bob Samuels | 1663645 | 73 |  | 22 / 20 | "Bob" is a nickname for a R- name |  |
| 10886 | MADRIGAL G | COMM | Lupita Madrigal | 3085078 | 72 |  | 4 / 8 | "Lupita" is a nickname for a G- name |  |
| 5224 | JANUSONIS S | PSY | Janusonis Skirmantas | 1539405 | 71 |  | 6 / 6 | Skirmantas Janusonis (Psychological & Brain Sciences); RMP stores the name surname-first |  |
| 6393 | PAGE H M | EEMB | Mark Page | 887948 | 71 |  | 10 / 10 | RMP first name "Mark" matches a Nexus middle initial (goes by middle name) |  |
| 9493 | MENA H P | WRIT | Paul Mena | 2573230 | 71 |  | 11 / 22 | RMP first name "Paul" matches a Nexus middle initial (goes by middle name) |  |
| 5764 | SHELL M S | CH | Scott Shell | 1113393 | 70 |  | 17 / 17 | RMP first name "Scott" matches a Nexus middle initial (goes by middle name) |  |
| 6318 | ICHIBA T | PSTAT | Ichiba Tomoyuki | 1549722 | 70 |  | 2 / 2 | Tomoyuki Ichiba (Statistics & Applied Probability); RMP stores the name surname-first |  |
| 6517 | PINCUS P A | BMSE | Fyl Pincus | 37182 | 70 |  | 16 / 16 | "Fyl" is a nickname for a P- name |  |
| 8087 | LARUE R J | INT | Jerry Larue | 1002782 | 70 |  | 3 / 3 | RMP first name "Jerry" matches a Nexus middle initial (goes by middle name) |  |
| 9583 | ACKERT E S | GEOG | Liz Ackert | 2558388 | 70 |  | 17 / 34 | "Liz" is a nickname for a E- name |  |
| 11044 | MUNDAY E M | SOC | Liz Munday | 3117727 | 70 |  | 5 / 5 | "Liz" is a nickname for a E- name |  |
