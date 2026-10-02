from app.ml.preprocess import clean_text, tokenize
from app.services.routing_service import route_ticket


def test_clean_text_and_tokenize():
    assert clean_text("Login FAILED! See https://example.com") == "login failed see"
    assert tokenize("Cannot access account") == ["cannot", "access", "account"]


def test_routing_category_and_priority():
    assert route_ticket("The invoice payment is wrong") == {
        "category": "billing",
        "priority": "normal",
    }
    assert route_ticket("Critical outage: service is down") == {
        "category": "general",
        "priority": "high",
    }
