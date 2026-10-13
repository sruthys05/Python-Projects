from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.ml.preprocess import clean_text

CATEGORY_TERMS = {
    "billing": {"billing", "invoice", "payment", "refund", "charge"},
    "technical": {"error", "bug", "crash", "failed", "broken", "login"},
    "account": {"account", "password", "access", "profile", "user"},
}


@lru_cache(maxsize=1)
def _load_model():
    model_path = Path(get_settings().model_path)
    if not model_path.is_file():
        return None
    import joblib

    return joblib.load(model_path)


def predict_category(text: str) -> str:
    cleaned = clean_text(text)
    model = _load_model()
    if model is not None:
        return str(model.predict([cleaned])[0])

    words = set(cleaned.split())
    scores = {category: len(words & terms) for category, terms in CATEGORY_TERMS.items()}
    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] else "general"
