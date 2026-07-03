"""
Embedding backends for the RAG layer.

Two implementations:
- TfidfEmbedder: pure local, zero API dependency, zero cost. Good enough for
  clustering competitor content by topical similarity and works offline/in CI.
- AnthropicVoyageEmbedder: production-grade embeddings via Voyage AI
  (Anthropic's recommended embedding partner). Swap in by setting
  EMBEDDING_BACKEND=voyage and VOYAGE_API_KEY in the environment.

The RAG store depends only on the Embedder protocol, so this swap requires
no changes anywhere else in the pipeline - this is the actual point of the
RAG layer being provider-agnostic rather than hardwired to one embedding API.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class Embedder(ABC):
    @abstractmethod
    def fit_transform(self, documents: list[str]) -> np.ndarray:
        """Embed a corpus, fitting any local vocabulary/state on it."""
        raise NotImplementedError

    @abstractmethod
    def transform(self, documents: list[str]) -> np.ndarray:
        """Embed new documents against already-fit state."""
        raise NotImplementedError


class TfidfEmbedder(Embedder):
    """
    Local, dependency-free embedder based on TF-IDF + SVD dimensionality
    reduction. Not as semantically rich as a transformer embedding, but
    deterministic, free, and sufficient for clustering competitor pages by
    topic overlap - which is all the Research/Keyword agents need it for.
    """

    def __init__(self, n_components: int = 64):
        self._vectorizer = TfidfVectorizer(
            max_features=4096, stop_words="english", ngram_range=(1, 2)
        )
        self._n_components = n_components
        self._svd = None
        self._fitted = False

    def fit_transform(self, documents: list[str]) -> np.ndarray:
        from sklearn.decomposition import TruncatedSVD

        sparse = self._vectorizer.fit_transform(documents)
        # TruncatedSVD requires n_components < min(n_samples, n_features).
        # On tiny corpora (a handful of test fixtures) that ceiling can be 1,
        # which makes explained_variance_ratio_ divide-by-zero internally
        # (harmless but noisy) - guard it explicitly instead of relying on
        # sklearn's warning.
        max_components = max(1, min(sparse.shape) - 1)
        n_comp = max(1, min(self._n_components, max_components))
        self._svd = TruncatedSVD(n_components=n_comp, random_state=42)
        dense = self._svd.fit_transform(sparse)
        self._fitted = True
        return dense

    def transform(self, documents: list[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Call fit_transform before transform.")
        sparse = self._vectorizer.transform(documents)
        return self._svd.transform(sparse)


class VoyageEmbedder(Embedder):
    """Production embedder via Voyage AI. Requires VOYAGE_API_KEY."""

    def __init__(self, model: str = "voyage-3"):
        import voyageai  # optional dependency, only imported if selected

        api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError("VOYAGE_API_KEY not set.")
        self._client = voyageai.Client(api_key=api_key)
        self._model = model

    def fit_transform(self, documents: list[str]) -> np.ndarray:
        return self.transform(documents)

    def transform(self, documents: list[str]) -> np.ndarray:
        result = self._client.embed(documents, model=self._model)
        return np.array(result.embeddings)


def get_embedder() -> Embedder:
    backend = os.environ.get("EMBEDDING_BACKEND", "tfidf")
    if backend == "voyage":
        return VoyageEmbedder()
    return TfidfEmbedder()
