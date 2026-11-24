from app.services.rag.cleaner import TextCleaner

def test_clean_unicode_normalization():
    # Ligatures and special spaces
    raw_text = "Standard\xa030-Day\u2002Return Policy ﬁle"
    cleaned = TextCleaner.clean(raw_text)
    assert "Standard 30-Day Return Policy file" in cleaned

def test_clean_excessive_whitespace_and_blank_lines():
    raw_text = "Heading\n\n\n\n\nParagraph 1.\n\n\n\nParagraph 2."
    cleaned = TextCleaner.clean(raw_text)
    # At most 2 consecutive newlines
    assert "\n\n\n" not in cleaned
    assert "Paragraph 1." in cleaned
    assert "Paragraph 2." in cleaned

def test_clean_preserves_structure():
    raw_text = "# Section 1: Policies\n* Rule 1\n* Rule 2\n\n1. First Step\n2. Second Step"
    cleaned = TextCleaner.clean(raw_text)
    assert "# Section 1: Policies" in cleaned
    assert "* Rule 1" in cleaned
    assert "1. First Step" in cleaned
