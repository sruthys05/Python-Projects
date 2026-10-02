from app.ml.classifier import predict_category

URGENT_TERMS = {"urgent", "outage", "down", "blocked", "critical", "security"}


def route_ticket(text: str) -> dict[str, str]:
    normalized = text.lower()
    priority = "high" if any(term in normalized for term in URGENT_TERMS) else "normal"
    return {"category": predict_category(text), "priority": priority}
