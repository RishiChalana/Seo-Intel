"""
Shared data contracts between agents.

Keeping every agent's input/output as a typed Pydantic model (rather than
passing raw dicts through the LangGraph state) is what makes this pipeline
debuggable: at any node we can log/validate exactly what shape the data is in,
and a bad LLM response fails fast at the schema boundary instead of silently
corrupting a downstream step.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.core.usage import TokenUsage


class SearchIntent(str, Enum):
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class CompetitorPage(BaseModel):
    """Raw scraped/fetched data for a single ranking competitor page."""

    url: str
    rank: int
    title: str
    headings: list[str] = Field(default_factory=list)
    word_count: int = 0
    raw_text: str = ""


class KeywordCluster(BaseModel):
    """A group of semantically related keywords sharing intent."""

    primary_keyword: str
    related_keywords: list[str]
    intent: SearchIntent
    est_difficulty: Optional[float] = Field(
        default=None, description="0-100 relative difficulty score, if available"
    )


class OutlineSection(BaseModel):
    heading: str
    level: int = Field(ge=1, le=3, description="1=H1, 2=H2, 3=H3")
    talking_points: list[str] = Field(default_factory=list)
    target_keywords: list[str] = Field(default_factory=list)


class ContentOutline(BaseModel):
    title: str
    meta_description: str
    sections: list[OutlineSection]
    estimated_word_count: int
    content_gaps_addressed: list[str] = Field(
        default_factory=list,
        description="Topics competitors cover that a naive brief would miss",
    )


class BriefScore(BaseModel):
    """Output of the evaluation agent - a rubric-based score, not vibes."""

    keyword_coverage: float = Field(ge=0, le=1, description="fraction of target cluster covered")
    structure_completeness: float = Field(ge=0, le=1)
    readability_grade: float = Field(description="Flesch-Kincaid grade level")
    eeat_signal_score: float = Field(
        ge=0, le=1, description="heuristic: author/source/citation cues present in outline"
    )
    overall: float = Field(ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class ContentBrief(BaseModel):
    """Final artifact returned by the pipeline."""

    topic: str
    keyword_clusters: list[KeywordCluster]
    competitor_pages_analyzed: int
    outline: ContentOutline
    score: BriefScore
    usage: TokenUsage = Field(
        default_factory=TokenUsage,
        description="LLM token + estimated cost telemetry for this run",
    )


class PipelineRequest(BaseModel):
    topic: str = Field(min_length=3)
    target_audience: Optional[str] = None
    max_competitors: int = Field(default=5, ge=1, le=10)
