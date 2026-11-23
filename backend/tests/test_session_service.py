import pytest

from app.models.schemas import SessionCreate
from app.services.session_service import create_session


class UnusedDatabase:
    def add(self, _item):
        raise AssertionError(f"unexpected persistence: {_item!r}")


@pytest.mark.parametrize("transcript", [[], {"messages": []}, ""])
def test_replay_session_rejects_empty_transcript(transcript):
    payload = SessionCreate(
        mode="replay",
        product_context="ShopNest",
        scenario="Review a support conversation",
        transcript=transcript,
    )

    with pytest.raises(ValueError, match="at least one non-empty message"):
        create_session(UnusedDatabase(), payload)
