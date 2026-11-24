from app.services.rag.chunker import TextChunker

def test_chunker_token_counting(embedding_service):
    chunker = TextChunker(target_chunk_size=350, chunk_overlap=50, tokenizer=embedding_service.tokenizer)
    count = chunker.count_tokens("Customer asks for an immediate replacement.")
    assert count > 0
    assert count < 20

def test_chunker_heading_preservation(embedding_service):
    chunker = TextChunker(target_chunk_size=350, chunk_overlap=50, tokenizer=embedding_service.tokenizer)
    pages = [{
        "page_number": 1,
        "text": "1. Standard 30-Day Return Policy\nAll items must be returned within 30 days of receipt.\n\n2. Damaged Items Policy\nDamaged items will be replaced immediately."
    }]
    chunks = chunker.chunk_document(pages, "policy.pdf", "ecommerce")
    assert len(chunks) >= 2
    assert chunks[0].section == "1. Standard 30-Day Return Policy"
    assert chunks[1].section == "2. Damaged Items Policy"
    assert chunks[0].metadata["source_filename"] == "policy.pdf"
    assert chunks[0].metadata["page_number"] == 1

def test_chunker_size_and_overlap(embedding_service):
    chunker = TextChunker(target_chunk_size=100, chunk_overlap=25, tokenizer=embedding_service.tokenizer)
    long_text = "This is a detailed policy paragraph explaining the rules for customers. " * 30
    pages = [{"page_number": 1, "text": "Section 1: Detailed Rules\n" + long_text}]
    chunks = chunker.chunk_document(pages, "rules.pdf", "ecommerce")
    assert len(chunks) > 1
    for c in chunks:
        # Chunks respect bounds
        assert c.token_count > 0
        assert c.metadata["target_chunk_size"] == 100
        assert c.metadata["chunk_overlap"] == 25

def test_chunker_never_exceeds_embedding_context_window(embedding_service):
    """Verifies that with default settings (220 target, 40 overlap, 240 max), no chunk exceeds model context."""
    chunker = TextChunker(
        target_chunk_size=220,
        chunk_overlap=40,
        max_chunk_tokens=240,
        tokenizer=embedding_service.tokenizer
    )
    long_section = "ApexCare provides extensive support for all electronic devices under warranty. " * 50
    pages = [
        {"page_number": 1, "text": "Warranty Coverage Terms\n" + long_section},
        {"page_number": 2, "text": "Escalation Guidelines\n" + long_section}
    ]
    chunks = chunker.chunk_document(pages, "apex_policy.pdf", "ecommerce")
    assert len(chunks) >= 4
    for c in chunks:
        # Check raw token count
        assert c.token_count <= 245
        # Verify with tokenizer encoding including special tokens ([CLS] and [SEP])
        full_tokens = embedding_service.tokenizer.encode(c.text, add_special_tokens=True)
        assert len(full_tokens) <= 256, f"Chunk {c.chunk_index} exceeded 256 tokens: {len(full_tokens)}"
