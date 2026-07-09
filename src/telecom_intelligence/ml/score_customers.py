"""Score customers for churn risk and retention priority."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

DEFAULT_FEATURES_PATH = Path("data/processed/customer_features.parquet")
DEFAULT_MODEL_PATH = Path("models/artifacts/churn_model.joblib")
DEFAULT_OUTPUT_PATH = Path("data/processed/customer_risk_scores.parquet")


def load_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing feature table: {path}. "
            "Run python -m telecom_intelligence.features.build_customer_features first."
        )
    return pd.read_parquet(path)


def load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing model artifact: {path}. "
            "Run python -m telecom_intelligence.ml.train_churn_models first."
        )
    return joblib.load(path)


def assign_risk_category(churn_probability: pd.Series) -> pd.Series:
    return pd.cut(
        churn_probability,
        bins=[-0.01, 0.30, 0.60, 1.0],
        labels=["low", "medium", "high"],
    ).astype(str)


def recommend_retention_action(row: pd.Series) -> str:
    if row["risk_category"] == "low":
        return "monitor"

    if row["cancellation_request_count"] > 0:
        return "urgent_save_call"

    if row["network_incident_count"] >= 2 or row["network_complaint_count"] > 0:
        return "service_recovery_credit"

    if row["late_payment_rate"] >= 0.25:
        return "billing_support_offer"

    if row["contract_type"] == "month_to_month":
        return "contract_discount_offer"

    if row["has_byod"]:
        return "byod_loyalty_perk"

    return "general_retention_offer"


def assign_retention_priority(scores: pd.DataFrame) -> pd.Series:
    priority_score = (
        scores["churn_probability"] * scores["total_mrr"].fillna(0)
        + scores["support_ticket_count"].fillna(0) * 5
        + scores["network_incident_count"].fillna(0) * 5
        + scores["late_payment_count"].fillna(0) * 3
    )

    return pd.qcut(
        priority_score.rank(method="first"),
        q=4,
        labels=["low", "medium", "high", "critical"],
    ).astype(str)


def score_customers(features: pd.DataFrame, model) -> pd.DataFrame:
    probabilities = model.predict_proba(features)[:, 1]

    scores = features[
        [
            "customer_id",
            "contract_type",
            "churned",
            "monthly_charges",
            "total_mrr",
            "monthly_revenue_at_risk",
            "support_ticket_count",
            "network_incident_count",
            "network_complaint_count",
            "cancellation_request_count",
            "late_payment_count",
            "late_payment_rate",
            "has_byod",
        ]
    ].copy()

    scores["churn_probability"] = probabilities
    scores["risk_category"] = assign_risk_category(scores["churn_probability"])
    scores["estimated_monthly_revenue_at_risk"] = (
        scores["churn_probability"] * scores["total_mrr"]
    ).round(2)
    scores["retention_priority"] = assign_retention_priority(scores)
    scores["recommended_action"] = scores.apply(recommend_retention_action, axis=1)

    return scores.sort_values(
        ["retention_priority", "estimated_monthly_revenue_at_risk"],
        ascending=[True, False],
    ).reset_index(drop=True)


def write_scores(scores: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-path", type=Path, default=DEFAULT_FEATURES_PATH)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    features = load_features(args.features_path)
    model = load_model(args.model_path)
    scores = score_customers(features, model)
    output_path = write_scores(scores, args.output_path)

    print(f"Scored customers: {len(scores):,}")
    print(f"Output: {output_path}")
    print("Risk category counts:")
    print(scores["risk_category"].value_counts().sort_index().to_string())
    print("Top recommended actions:")
    print(scores["recommended_action"].value_counts().head(10).to_string())


if __name__ == "__main__":
    main()
