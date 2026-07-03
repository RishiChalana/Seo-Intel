from app.core.schemas import CompetitorPage
from app.rag.embedder import TfidfEmbedder
from app.rag.store import CompetitorRAGStore, chunk_text


def test_chunk_text_splits_long_text_with_overlap():
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    # verify overlap: last words of chunk[0] should reappear at start of chunk[1]
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    assert first_words[-1] in second_words[:25]


def test_chunk_text_handles_empty_string():
    assert chunk_text("") == []


def test_chunk_text_single_short_chunk_returned_whole():
    text = "just a few words here"
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_rag_store_indexes_and_retrieves_relevant_chunk():
    pages = [
        CompetitorPage(
            url="https://a.com",
            rank=1,
            title="Cooking Guide",
            raw_text="Pasta recipes require boiling water and salt. " * 20,
        ),
        CompetitorPage(
            url="https://b.com",
            rank=2,
            title="Finance Guide",
            raw_text="Stock market investing requires understanding risk. " * 20,
        ),
    ]
    store = CompetitorRAGStore(TfidfEmbedder(n_components=8))
    n_indexed = store.index_pages(pages)
    assert n_indexed > 0

    results = store.retrieve("pasta boiling water", k=2)
    assert len(results) > 0
    # the most relevant chunk should come from the cooking page, not finance
    assert results[0]["url"] == "https://a.com"


def test_rag_store_retrieve_before_index_returns_empty():
    store = CompetitorRAGStore(TfidfEmbedder())
    assert store.retrieve("anything") == []
