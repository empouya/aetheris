from app.modules.processing.chunker import TextChunker


def test_chunk_empty_text_returns_empty_list() -> None:
    chunker = TextChunker()
    assert chunker.chunk("") == []


def test_chunk_whitespace_only_returns_empty_list() -> None:
    chunker = TextChunker()
    assert chunker.chunk("   ") == []


def test_chunk_short_text_produces_single_chunk() -> None:
    chunker = TextChunker(chunk_size=512, overlap=64)
    results = chunker.chunk("This is a short document.")

    assert len(results) == 1
    assert results[0].chunk_index == 0
    assert results[0].chunk_text == "This is a short document."
    assert results[0].token_count > 0
    assert len(results[0].text_hash) == 64


def test_chunk_long_text_produces_multiple_chunks() -> None:
    chunker = TextChunker(chunk_size=10, overlap=2)
    text = " ".join([f"word{i}" for i in range(100)])
    results = chunker.chunk(text)

    assert len(results) > 1
    for i, chunk in enumerate(results):
        assert chunk.chunk_index == i
        assert chunk.token_count <= 10
        assert chunk.token_count > 0


def test_chunk_indexes_are_sequential() -> None:
    chunker = TextChunker(chunk_size=10, overlap=2)
    text = " ".join([f"word{i}" for i in range(100)])
    results = chunker.chunk(text)

    indexes = [r.chunk_index for r in results]
    assert indexes == list(range(len(results)))


def test_chunk_text_hash_is_deterministic() -> None:
    chunker = TextChunker()
    text = "Deterministic hashing test."
    results_a = chunker.chunk(text)
    results_b = chunker.chunk(text)

    assert results_a[0].text_hash == results_b[0].text_hash


def test_chunk_each_result_has_nonempty_text() -> None:
    chunker = TextChunker(chunk_size=10, overlap=2)
    text = " ".join([f"word{i}" for i in range(50)])
    results = chunker.chunk(text)

    for chunk in results:
        assert chunk.chunk_text.strip() != ""
