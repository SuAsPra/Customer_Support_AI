import pytest

from app.rag.chunk import chunk_text


def test_heading_changes_keep_chunks_attributed_to_their_section():
    chunks = chunk_text(
        "## Alpha\n\n" + "a" * 150 + "\n\n## Beta\n\n" + "b" * 150,
        chunk_size_tokens=50,
        overlap_tokens=0,
    )

    assert [chunk.metadata["section"] for chunk in chunks] == ["Alpha", "Beta"]


def test_zero_overlap_does_not_repeat_text():
    chunks = chunk_text(
        "a" * 130 + "\n\n" + "b" * 130,
        chunk_size_tokens=50,
        overlap_tokens=0,
    )

    assert len(chunks) == 2
    assert chunks[0].text == "a" * 130
    assert chunks[1].text == "b" * 130


@pytest.mark.parametrize(
    ("chunk_size_tokens", "overlap_tokens"),
    [(0, 0), (10, -1), (10, 10)],
)
def test_invalid_chunk_parameters_fail_fast(chunk_size_tokens, overlap_tokens):
    with pytest.raises(ValueError):
        chunk_text(
            "Some text",
            chunk_size_tokens=chunk_size_tokens,
            overlap_tokens=overlap_tokens,
        )
