import pytest

from app.agents.keyword_agent import _extract_candidate_phrases, cluster_keywords
from app.core.llm import FakeLLMClient
from app.core.schemas import CompetitorPage, KeywordCluster, SearchIntent
from app.rag.embedder import TfidfEmbedder


def test_extract_candidate_phrases_filters_stopwords():
    text = "The quick brown fox jumps over the lazy dog and the fox runs"
    phrases = _extract_candidate_phrases(text, top_n=10)
    assert "the" not in phrases
    assert "and" not in phrases
    assert any("fox" in p for p in phrases)


def test_extract_candidate_phrases_empty_text():
    assert _extract_candidate_phrases("") == []


def test_extract_filters_contraction_fragments():
    # "don't", "won't", "isn't" tokenize to fragments like "don", "won", "isn"
    # when apostrophes are stripped — these must not appear as candidates.
    text = (
        "Email marketing automation don't have to be complicated. "
        "It won't take long to set up your first campaign. "
        "Isn't it time you tried automation software for your business?"
    )
    phrases = _extract_candidate_phrases(text, top_n=20)
    noise = {"don", "won", "isn", "have", "taken", "out", "now", "time"}
    found_noise = noise & set(phrases)
    assert not found_noise, f"Noise words leaked into candidates: {found_noise}"
    # Real keyword candidates should survive
    assert any("automation" in p for p in phrases)
    assert any("email" in p for p in phrases)


def test_extract_filters_marketing_filler():
    # Realistic SERP snippet with filler like "taken", "out", "now", "guesswork"
    text = (
        "We have taken the guesswork out of email marketing. "
        "Now you can automate your campaigns and get more results. "
        "Our email automation platform helps businesses grow faster today."
    )
    phrases = _extract_candidate_phrases(text, top_n=20)
    filler = {"taken", "out", "now", "get", "have"}
    found_filler = filler & set(phrases)
    assert not found_filler, f"Filler words leaked into candidates: {found_filler}"
    assert any("email" in p for p in phrases)
    assert any("automat" in p for p in phrases)


def test_bigrams_only_pair_adjacent_content_words():
    # Stopword removal must not create phantom bigrams from non-adjacent words.
    # "email [is the] tool" should NOT produce "email tool" as a bigram.
    text = "email is the tool for automation"
    phrases = _extract_candidate_phrases(text, top_n=20)
    assert "email tool" not in phrases
    # "email automation" is not adjacent here either
    assert "email automation" not in phrases
    # "tool automation" is adjacent after stopword removal from the raw sequence
    # — but since bigrams are built from raw adjacency, "tool" and "for" are
    # adjacent, and "for" is a stopword, so "tool automation" should NOT appear.
    assert "tool automation" not in phrases


def test_extract_real_serp_noise():
    # Simulates the exact style of noisy output seen in production:
    # contractions, sentence fragments, filler — mix in real keyword signal.
    text = (
        "Don't let manual processes slow you down. We've taken all the "
        "guesswork out of email marketing automation. Now businesses can "
        "build drip campaigns, segment their lists, and track open rates "
        "without any coding. Try our marketing automation software today "
        "and see the difference in your campaign performance."
    )
    phrases = _extract_candidate_phrases(text, top_n=25)
    bad = {"don", "won", "isn", "now", "out", "taken", "down", "let",
           "see", "try", "get", "all", "any"}
    leaked = bad & set(phrases)
    assert not leaked, f"Noise leaked: {leaked}"
    # Must surface the real SEO terms
    keyword_signal = {"email", "marketing", "automation", "campaigns",
                      "campaign", "drip"}
    found = keyword_signal & {w for p in phrases for w in p.split()}
    assert found, f"No keyword signal found in: {phrases}"


@pytest.mark.asyncio
async def test_cluster_keywords_returns_llm_labeled_clusters():
    pages = [
        CompetitorPage(
            url="https://a.com",
            rank=1,
            title="SEO Guide",
            raw_text="seo automation tools content marketing seo strategy " * 10,
        )
    ]
    fake_cluster = KeywordCluster(
        primary_keyword="seo automation",
        related_keywords=["seo tools", "content marketing"],
        intent=SearchIntent.COMMERCIAL,
    )
    llm = FakeLLMClient(responses={"_ClusterLabelResponse": fake_cluster})

    clusters = await cluster_keywords(
        topic="seo automation",
        pages=pages,
        embedder=TfidfEmbedder(n_components=4),
        llm=llm,
        n_clusters=2,
    )

    assert len(clusters) >= 1
    assert all(isinstance(c, KeywordCluster) for c in clusters)
    assert len(llm.calls) == len(clusters)
