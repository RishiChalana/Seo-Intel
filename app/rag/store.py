"""
RAG store: chunks competitor pages, embeds them, and supports similarity
retrieval so the Structure agent can ground its outline in what top-ranking
pages actually cover instead of hallucinating a generic outline.

Uses an in-memory Chroma collection (ephemeral per pipeline run) since each
run is analyzing a fresh topic - there's no need to persist embeddings across
unrelated topics, and it keeps the pipeline stateless/horizontally scalable.
"""

from __future__ import annotations

import uuid

import chromadb

from app.core.schemas import CompetitorPage
from app.rag.embedder import Embedder


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Simple sliding-window word chunker. Good enough for short-form SERP content."""
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


class CompetitorRAGStore:
    def __init__(self, embedder: Embedder):
        self._embedder = embedder
        self._client = chromadb.Client()
        self._collection = self._client.create_collection(
            name=f"competitors-{uuid.uuid4().hex[:8]}"
        )
        self._loaded = False

    def index_pages(self, pages: list[CompetitorPage]) -> int:
        """Chunk + embed every competitor page. Returns number of chunks indexed."""
        docs, metadatas, ids = [], [], []
        for page in pages:
            for i, chunk in enumerate(chunk_text(page.raw_text)):
                docs.append(chunk)
                metadatas.append({"url": page.url, "rank": page.rank, "title": page.title})
                ids.append(f"{page.url}-{i}")

        if not docs:
            return 0

        embeddings = self._embedder.fit_transform(docs)
        self._collection.add(
            ids=ids,
            documents=docs,
            metadatas=metadatas,
            embeddings=embeddings.tolist(),
        )
        self._loaded = True
        return len(docs)

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        """Return the top-k most relevant competitor chunks for a query."""
        if not self._loaded:
            return []
        query_emb = self._embedder.transform([query])
        results = self._collection.query(query_embeddings=query_emb.tolist(), n_results=k)
        out = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            out.append({"text": doc, **meta})
        return out
