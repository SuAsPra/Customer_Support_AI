import pytest
from app.services.rag.extractor import (
    DocumentExtractor,
    DocumentExtractionError,
    CorruptedDocumentError,
    EmptyDocumentError,
)

def test_extract_valid_pdf(sample_pdf_bytes):
    pages = DocumentExtractor.extract_from_bytes(sample_pdf_bytes, "sample.pdf", "pdf")
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "Warranty and Return Terms" in pages[0]["text"]
    assert pages[1]["page_number"] == 2
    assert "Technical Support Guidelines" in pages[1]["text"]

def test_extract_empty_bytes():
    with pytest.raises(EmptyDocumentError) as exc_info:
        DocumentExtractor.extract_from_bytes(b"", "empty.pdf", "pdf")
    assert "completely empty" in str(exc_info.value)

def test_extract_corrupted_pdf(corrupted_pdf_bytes):
    with pytest.raises(CorruptedDocumentError) as exc_info:
        DocumentExtractor.extract_from_bytes(corrupted_pdf_bytes, "broken.pdf", "pdf")
    assert "Corrupted or invalid" in str(exc_info.value)

def test_extract_empty_pdf_no_text(empty_pdf_bytes):
    with pytest.raises(EmptyDocumentError) as exc_info:
        DocumentExtractor.extract_from_bytes(empty_pdf_bytes, "blank.pdf", "pdf")
    assert "no extractable text" in str(exc_info.value)

def test_extract_plain_text():
    content = b"# Returns FAQ\nCustomers have 30 days to return defective items."
    pages = DocumentExtractor.extract_from_bytes(content, "faq.md", "markdown")
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert "Returns FAQ" in pages[0]["text"]
