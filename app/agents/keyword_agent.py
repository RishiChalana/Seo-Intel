"""
Keyword Agent: extracts candidate keywords from competitor content and
clusters them by topical similarity + search intent.

Clustering uses KMeans over the same embedding space as the RAG store
(rather than asking the LLM to "guess" clusters), so the grouping is
grounded in what competitors actually wrote, not an LLM's prior.
The LLM is used only for the part that requires judgment: labeling each
cluster's search intent and picking a human-readable primary keyword.
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np
from sklearn.cluster import KMeans

from app.core.llm import LLMClient
from app.core.schemas import CompetitorPage, KeywordCluster, SearchIntent
from app.rag.embedder import Embedder

# Comprehensive English stopword set: NLTK's 179-word corpus plus contraction
# fragments that appear when tokenizing real scraped text (e.g. "don't" →
# "don" + "t"; the "t" is filtered by the 3-char minimum but "don" slips
# through without this list) plus common web/marketing filler that appears
# in SERP snippets but carries no keyword signal.
_STOPWORDS: frozenset[str] = frozenset({
    # Core function words
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "at", "to",
    "of", "for", "by", "as", "is", "it", "be", "was", "are", "were",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "from",
    "with", "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "each", "few", "more", "most", "other", "some", "such", "than", "too",
    "very", "just", "also", "about", "above", "after", "before", "between",
    "during", "into", "through", "until", "while", "against", "along",
    "among", "around", "because", "below", "down", "out", "off", "over",
    "under", "up", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "own", "same",
    # Pronouns
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    # Common auxiliary / high-frequency verbs with low keyword value
    "get", "got", "getting", "gets", "let", "lets", "letting",
    "make", "makes", "making", "made", "take", "takes", "taking", "taken",
    "give", "gives", "giving", "given", "keep", "keeps", "keeping", "kept",
    "come", "comes", "coming", "came", "put", "puts", "putting",
    "set", "sets", "setting", "go", "goes", "going", "went", "gone",
    "know", "knows", "knowing", "knew", "known",
    "think", "thinks", "thinking", "thought",
    "say", "says", "saying", "said",
    "see", "sees", "seeing", "saw", "seen",
    "use", "uses", "using", "used",
    "want", "wants", "wanting", "wanted",
    "need", "needs", "needing", "needed",
    "help", "helps", "helping", "helped",
    "try", "tries", "trying", "tried",
    "ask", "asks", "asking", "asked",
    "seem", "seems", "seeming", "seemed",
    "show", "shows", "showing", "showed", "shown",
    "work", "works", "working", "worked",
    "look", "looks", "looking", "looked",
    "turn", "turns", "turning", "turned",
    "start", "starts", "starting", "started",
    # Adverbs / filler with no keyword signal
    "now", "only", "even", "still", "already", "often", "always",
    "never", "sometimes", "today", "well", "much", "many", "every",
    "however", "therefore", "although", "though", "unless",
    "including", "without", "within", "whether", "across", "since",
    # Contraction stems from real scraped text ("don't" → "don" + "t";
    # "t" caught by 3-char min, but these stems slip through)
    "don", "won", "isn", "aren", "doesn", "wasn", "weren",
    "couldn", "shouldn", "wouldn", "hadn", "hasn", "haven",
    "didn", "mightn", "needn", "shan", "mustn", "ain",
    # Generic web-content nouns with no topical signal
    "page", "site", "web", "link", "links", "click", "read",
    "find", "learn", "things", "thing", "part", "parts",
    "time", "times", "way", "ways", "case", "cases",
    "point", "points", "people", "person",
})


def _extract_candidate_phrases(text: str, top_n: int = 30) -> list[str]:
    """Extract frequent 1-2 word phrases as keyword candidates from noisy text.

    Bigrams are built from the original token sequence (before stopword
    removal) so adjacency is preserved — without this, removing a stopword
    between two content words creates a phantom bigram of words that were
    never actually adjacent in the source text.

    Bigrams are weighted 3x so they dominate the candidate list. Single
    generic words are almost never good SEO keyword targets; multi-word
    phrases are what people actually type into Google.
    """
    raw_words = re.findall(r"[a-zA-Z]{3,}", text.lower())

    unigrams = Counter(w for w in raw_words if w not in _STOPWORDS)

    # Keep a bigram only when both tokens are content words
    bigrams = Counter(
        f"{a} {b}"
        for a, b in zip(raw_words, raw_words[1:])
        if a not in _STOPWORDS and b not in _STOPWORDS
    )

    # Bigrams weighted 3x: a bigram appearing once scores higher than a
    # unigram appearing twice, ensuring phrases dominate the candidate list.
    boosted = Counter({phrase: count * 3 for phrase, count in bigrams.items()})
    combined = unigrams + boosted
    return [phrase for phrase, _ in combined.most_common(top_n)]


class _ClusterLabelResponse(KeywordCluster):
    """Reuses KeywordCluster as the direct LLM structured-output target."""


async def cluster_keywords(
    topic: str,
    pages: list[CompetitorPage],
    embedder: Embedder,
    llm: LLMClient,
    n_clusters: int = 3,
) -> list[KeywordCluster]:
    candidates: list[str] = [topic]
    for page in pages:
        candidates.extend(_extract_candidate_phrases(page.raw_text, top_n=15))
    candidates = list(dict.fromkeys(candidates))  # dedupe, preserve order

    if len(candidates) < n_clusters:
        n_clusters = max(1, len(candidates))

    embeddings = embedder.fit_transform(candidates)
    k = min(n_clusters, len(candidates))
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(embeddings)

    grouped: dict[int, list[str]] = {}
    for phrase, label in zip(candidates, labels):
        grouped.setdefault(int(label), []).append(phrase)

    clusters: list[KeywordCluster] = []
    for group in grouped.values():
        primary = max(group, key=len) if group else topic
        labeled = await llm.complete_structured(
            system=(
                "You are an SEO strategist. Given a group of keyword candidates "
                "extracted from competitor pages, select the single best primary "
                "keyword and 3-5 high-quality related keywords — only phrases "
                "that a real person would type into Google. "
                "Discard single generic words, filler terms, and anything that "
                "is not a real search query. Classify the dominant search intent."
            ),
            prompt=f"Keyword candidates: {group}\nTopic context: {topic}",
            schema=_ClusterLabelResponse,
        )
        clusters.append(KeywordCluster(**labeled.model_dump()))

    return clusters
