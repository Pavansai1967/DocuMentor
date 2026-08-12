from app.chunker import Chunk, chunk_pages


def word_count(text: str) -> int:
    return len(text.split())


def test_single_page_single_chunk():
    text = " ".join(["word"] * 100)
    chunks = chunk_pages([text], word_count, chunk_size=80, chunk_overlap=10)
    assert [c.page_number for c in chunks] == [1, 1]
    assert [c.chunk_index for c in chunks] == [0, 1]
    assert all(word_count(c.text) <= 80 for c in chunks)


def test_overlap_reuses_tail_words():
    text = " ".join(f"w{i}" for i in range(100))
    chunks = chunk_pages([text], word_count, chunk_size=40, chunk_overlap=10)
    assert len(chunks) == 3
    assert chunks[0].text == " ".join(f"w{i}" for i in range(40))
    assert chunks[1].text.startswith("w30 ")
    assert chunks[2].text == " ".join(f"w{i}" for i in range(60, 100))


def test_page_numbers_stay_in_page():
    pages = ["alpha beta gamma delta", "epsilon zeta eta theta iota kappa lambda"]
    chunks = chunk_pages(pages, word_count, chunk_size=4, chunk_overlap=1)
    assert [c.page_number for c in chunks] == [1, 1, 2, 2]
    assert [c.chunk_index for c in chunks] == [0, 1, 2, 3]


def test_blank_page_yields_no_chunks():
    chunks = chunk_pages(["   \n ", "some real text here"], word_count, chunk_size=10, chunk_overlap=1)
    assert [c.page_number for c in chunks] == [2]