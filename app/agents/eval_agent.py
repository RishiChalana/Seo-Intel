"""
Evaluation Agent: scores the generated brief against a fixed rubric.

Deliberately NOT another "ask the LLM to grade itself" step - that's noisy
and ungrounded. Instead:
  - keyword_coverage / structure_completeness / eeat_signal_score are computed
    deterministically from the outline (measurable, reproducible)
  - readability_grade uses the textstat library (Flesch-Kincaid), a real
    established formula
This is what makes the "score" defensible in an interview: it's not an LLM
opinion, it's a rubric anyone can re-run and get the same number from.
"""

from __future__ import annotations

import textstat

from app.core.schemas import BriefScore, ContentOutline, KeywordCluster

_EEAT_MARKERS = {
    "expert", "study", "research", "data", "source", "cited", "according to",
    "case study", "example", "statistics", "author", "review",
}


def _keyword_coverage(outline: ContentOutline, clusters: list[KeywordCluster]) -> float:
    outline_text = " ".join(
        [outline.title]
        + [s.heading for s in outline.sections]
        + [kw for s in outline.sections for kw in s.target_keywords]
    ).lower()

    all_keywords = [c.primary_keyword for c in clusters] + [
        kw for c in clusters for kw in c.related_keywords
    ]
    if not all_keywords:
        return 0.0

    covered = sum(1 for kw in all_keywords if kw.lower() in outline_text)
    return round(covered / len(all_keywords), 3)


def _structure_completeness(outline: ContentOutline) -> float:
    """Rewards having an H1, multiple H2s, and at least some H3 depth/talking points."""
    has_title = bool(outline.title)
    has_meta = bool(outline.meta_description)
    h2_count = sum(1 for s in outline.sections if s.level == 2)
    has_talking_points = all(len(s.talking_points) > 0 for s in outline.sections) if outline.sections else False

    score = 0.0
    score += 0.25 if has_title else 0
    score += 0.25 if has_meta else 0
    score += 0.25 if h2_count >= 3 else (0.1 if h2_count >= 1 else 0)
    score += 0.25 if has_talking_points else 0
    return round(score, 3)


def _eeat_signal_score(outline: ContentOutline) -> float:
    text = " ".join(
        [outline.title] + [tp for s in outline.sections for tp in s.talking_points]
    ).lower()
    hits = sum(1 for marker in _EEAT_MARKERS if marker in text)
    return round(min(1.0, hits / 4), 3)


def score_brief(outline: ContentOutline, clusters: list[KeywordCluster]) -> BriefScore:
    coverage = _keyword_coverage(outline, clusters)
    structure = _structure_completeness(outline)
    eeat = _eeat_signal_score(outline)

    sample_text = " ".join(
        [outline.title, outline.meta_description]
        + [s.heading for s in outline.sections]
        + [tp for s in outline.sections for tp in s.talking_points]
    )
    readability = textstat.flesch_kincaid_grade(sample_text) if sample_text.strip() else 0.0

    overall = round((coverage * 0.4) + (structure * 0.35) + (eeat * 0.25), 3)

    notes = []
    if coverage < 0.5:
        notes.append("Low keyword coverage - outline may underperform target cluster.")
    if structure < 0.7:
        notes.append("Structure incomplete - check for missing meta description or H2 depth.")
    if eeat < 0.3:
        notes.append("Few E-E-A-T signals - consider adding expert quotes/citations/data points.")

    return BriefScore(
        keyword_coverage=coverage,
        structure_completeness=structure,
        readability_grade=round(float(readability), 2),
        eeat_signal_score=eeat,
        overall=overall,
        notes=notes,
    )
