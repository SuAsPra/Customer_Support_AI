import pytest
from pydantic import ValidationError

from app.models.schemas import RetrieveRequest, SessionCreate


@pytest.mark.parametrize("top_k", [0, -1])
def test_retrieve_request_rejects_non_positive_top_k(top_k):
    with pytest.raises(ValidationError):
        RetrieveRequest(query="question", top_k=top_k)


def test_retrieve_request_rejects_blank_query():
    with pytest.raises(ValidationError):
        RetrieveRequest(query="   ")


def test_simulator_rejects_whitespace_persona():
    with pytest.raises(ValidationError):
        SessionCreate(
            mode="simulator",
            product_context="ShopNest",
            scenario="Help with an order",
            persona="   ",
        )
