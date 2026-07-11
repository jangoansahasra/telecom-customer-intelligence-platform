"""Classify support-ticket complaints with Hugging Face Transformers.

This script uses zero-shot transformer classification to label synthetic
support-ticket text. Results are precomputed and saved as parquet outputs so
the deployed Streamlit app does not need to run the transformer model live.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_SUPPORT_TICKETS_PATH = Path("data/processed/support_tickets.parquet")
DEFAULT_OUTPUT_PATH = Path("data/processed/classified_support_tickets.parquet")
DEFAULT_DEMO_SCORES_PATH = Path("data/demo/customer_risk_scores_demo.parquet")
DEFAULT_DEMO_OUTPUT_PATH = Path("data/demo/classified_support_tickets_demo.parquet")
DEFAULT_MODEL_NAME = "facebook/bart-large-mnli"

COMPLAINT_LABELS = [
    "billing",
    "network outage",
    "slow internet",
    "device problem",
    "activation issue",
    "pricing complaint",
    "cancellation request",
]


def normalize_label(label: str) -> str:
    return label.lower().replace(" ", "_")


def load_support_tickets(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing support ticket table: {path}. "
            "Run python -m telecom_intelligence.synthetic.generate_telecom_data first."
        )

    tickets = pd.read_parquet(path)

    required_columns = {"ticket_id", "customer_id", "ticket_text"}
    missing_columns = required_columns - set(tickets.columns)
    if missing_columns:
        raise ValueError(f"Support tickets missing columns: {sorted(missing_columns)}")

    return tickets


def build_classifier(model_name: str = DEFAULT_MODEL_NAME):
    try:
        from transformers import pipeline
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "Missing optional NLP dependency `transformers`. "
            "Install NLP dependencies with: "
            "python -m pip install -r requirements-nlp.txt"
        ) from error

    return pipeline(
        task="zero-shot-classification",
        model=model_name,
    )


def classify_unique_texts(
    ticket_texts: pd.Series,
    classifier: Any,
    candidate_labels: list[str] = COMPLAINT_LABELS,
) -> dict[str, dict[str, float | str]]:
    classifications: dict[str, dict[str, float | str]] = {}

    for text in sorted(ticket_texts.dropna().unique()):
        result = classifier(
            text,
            candidate_labels=candidate_labels,
            multi_label=False,
        )
        top_label = str(result["labels"][0])
        top_score = float(result["scores"][0])

        classifications[text] = {
            "complaint_category_predicted": normalize_label(top_label),
            "complaint_category_score": round(top_score, 6),
        }

    return classifications


def classify_support_tickets(
    tickets: pd.DataFrame,
    classifier: Any,
) -> pd.DataFrame:
    classifications = classify_unique_texts(tickets["ticket_text"], classifier)

    classified = tickets.copy()
    classified["complaint_category_predicted"] = classified["ticket_text"].map(
        lambda text: classifications[text]["complaint_category_predicted"]
    )
    classified["complaint_category_score"] = classified["ticket_text"].map(
        lambda text: classifications[text]["complaint_category_score"]
    )

    classified["complaint_category_matches_seed"] = classified[
        "complaint_category_predicted"
    ].eq(classified["complaint_category_seed"])

    return classified


def write_classified_tickets(classified: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    classified.to_parquet(output_path, index=False)
    return output_path


def write_demo_classified_tickets(
    classified: pd.DataFrame,
    demo_scores_path: Path = DEFAULT_DEMO_SCORES_PATH,
    output_path: Path = DEFAULT_DEMO_OUTPUT_PATH,
) -> Path | None:
    if not demo_scores_path.exists():
        return None

    demo_scores = pd.read_parquet(demo_scores_path)
    demo_classified = classified.loc[
        classified["customer_id"].isin(demo_scores["customer_id"])
    ].copy()

    demo_classified = demo_classified.sort_values(
        ["customer_id", "ticket_id"]
    ).reset_index(drop=True)

    return write_classified_tickets(demo_classified, output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--support-tickets-path",
        type=Path,
        default=DEFAULT_SUPPORT_TICKETS_PATH,
    )
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--model-name", type=str, default=DEFAULT_MODEL_NAME)
    args = parser.parse_args()

    tickets = load_support_tickets(args.support_tickets_path)
    classifier = build_classifier(args.model_name)
    classified = classify_support_tickets(tickets, classifier)

    output_path = write_classified_tickets(classified, args.output_path)
    demo_output_path = write_demo_classified_tickets(classified)

    print(f"Classified support tickets: {len(classified):,}")
    print(f"Output: {output_path}")

    if demo_output_path:
        print(f"Demo output: {demo_output_path}")

    print("Predicted complaint categories:")
    print(
        classified["complaint_category_predicted"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    match_rate = classified["complaint_category_matches_seed"].mean()
    print(f"Seed-label match rate: {match_rate:.2%}")


if __name__ == "__main__":
    main()
