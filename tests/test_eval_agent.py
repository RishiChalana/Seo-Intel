from app.agents.eval_agent import score_brief
from app.core.schemas import ContentOutline, KeywordCluster, OutlineSection, SearchIntent


def _sample_clusters():
    return [
        KeywordCluster(
            primary_keyword="content automation",
            related_keywords=["automated content", "ai content tools"],
            intent=SearchIntent.COMMERCIAL,
        ),
        KeywordCluster(
            primary_keyword="seo brief generator",
            related_keywords=["content brief", "seo outline"],
            intent=SearchIntent.INFORMATIONAL,
        ),
    ]


def _good_outline():
    return ContentOutline(
        title="Content Automation: The Complete SEO Brief Generator Guide",
        meta_description="Learn how content automation and an SEO brief generator can scale content ops.",
        sections=[
            OutlineSection(
                heading="What is content automation",
                level=2,
                talking_points=["Define automated content", "Cite a recent study on adoption"],
                target_keywords=["content automation", "automated content"],
            ),
            OutlineSection(
                heading="Why use an SEO brief generator",
                level=2,
                talking_points=["Expert opinion on content briefs", "Case study example"],
                target_keywords=["seo brief generator", "content brief"],
            ),
            OutlineSection(
                heading="How AI content tools compare",
                level=2,
                talking_points=["Data from vendor comparison", "Cited source review"],
                target_keywords=["ai content tools", "seo outline"],
            ),
        ],
        estimated_word_count=1500,
    )


def _empty_outline():
    return ContentOutline(
        title="",
        meta_description="",
        sections=[],
        estimated_word_count=0,
    )


def test_good_outline_scores_highly_on_all_axes():
    score = score_brief(_good_outline(), _sample_clusters())
    assert score.keyword_coverage > 0.8
    assert score.structure_completeness == 1.0
    assert score.eeat_signal_score > 0.5
    assert score.overall > 0.7
    assert score.notes == []


def test_empty_outline_scores_zero_and_flags_notes():
    score = score_brief(_empty_outline(), _sample_clusters())
    assert score.keyword_coverage == 0.0
    assert score.structure_completeness == 0.0
    assert score.overall == 0.0
    assert len(score.notes) == 3


def test_readability_grade_is_computed_not_hardcoded():
    simple = ContentOutline(
        title="Cats",
        meta_description="Cats are fun. Cats are cute. Cats are pets.",
        sections=[],
        estimated_word_count=10,
    )
    complex_ = ContentOutline(
        title="An Exhaustive Epistemological Examination",
        meta_description=(
            "This comprehensive treatise interrogates the multifaceted, "
            "interdisciplinary ramifications of algorithmic content "
            "generation methodologies within contemporary digital ecosystems."
        ),
        sections=[],
        estimated_word_count=10,
    )
    simple_score = score_brief(simple, [])
    complex_score = score_brief(complex_, [])
    assert simple_score.readability_grade < complex_score.readability_grade


def test_notes_flag_low_coverage_specifically():
    outline = ContentOutline(
        title="Unrelated Title",
        meta_description="Nothing to do with the clusters.",
        sections=[
            OutlineSection(heading="Random", level=2, talking_points=["x"], target_keywords=[])
        ],
        estimated_word_count=500,
    )
    score = score_brief(outline, _sample_clusters())
    assert score.keyword_coverage < 0.5
    assert any("keyword coverage" in n.lower() for n in score.notes)
