import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.preprocess import clean_text


def train(data_path: Path, model_path: Path) -> None:
    data = pd.read_csv(data_path)
    required_columns = {"text", "category"}
    if not required_columns.issubset(data.columns):
        raise ValueError("Training CSV must contain 'text' and 'category' columns")
    if data.empty or data["category"].nunique() < 2:
        raise ValueError("Training data must contain examples from at least two categories")

    training_text = data["text"].fillna("").map(clean_text)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("classifier", LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(training_text, data["category"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"Saved classifier to {model_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the ticket category classifier")
    parser.add_argument("--data", type=Path, default=Path("data/tickets_sample.csv"))
    parser.add_argument("--output", type=Path, default=Path("app/ml/models/ticket_classifier.joblib"))
    args = parser.parse_args()
    train(args.data, args.output)


if __name__ == "__main__":
    main()
