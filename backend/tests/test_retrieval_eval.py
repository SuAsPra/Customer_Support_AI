from scripts.evaluate_retrieval import matches_expected_result


def test_expected_section_must_be_present_to_count_as_a_match():
    assert not matches_expected_result(
        {"source": "refund_policy.md"},
        "refund_policy.md",
        "duplicate or incorrect charges",
    )


def test_expected_document_and_section_match_case_insensitively():
    assert matches_expected_result(
        {"source": "refund_policy.md", "section": "Duplicate or Incorrect Charges"},
        "refund_policy.md",
        "duplicate or incorrect charges",
    )
