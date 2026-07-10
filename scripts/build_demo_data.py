"""Build a small committed demo dataset for the Streamlit app.

The full processed dataset is ignored. This script creates a smaller demo
subset that can be committed and used by deployment platforms.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

FEATURES_INPUT = Path("data/processed/customer_features.parquet")
SCORES_INPUT = Path("data/processed/customer_risk_scores.parquet")
DEMO_DIR = Path("data/demo")
DEMO_FEATURES_OUTPUT = DEMO_DIR / "customer_features_demo.parquet"
DEMO_SCORES_OUTPUT = DEMO_DIR / "customer_risk_scores_demo.parquet"
DEMO_ROW_COUNT = 500


def load_required_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing required table: {path}. "
            "Run the feature builder and customer scorer first."
        )

    return pd.read_parquet(path)


def build_demo_data(
    row_count: int = DEMO_ROW_COUNT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = load_required_table(FEATURES_INPUT)
    scores = load_required_table(SCORES_INPUT)

    high_risk = scores.loc[scores["risk_category"].eq("high")]
    medium_risk = scores.loc[scores["risk_category"].eq("medium")]
    low_risk = scores.loc[scores["risk_category"].eq("low")]

    high_count = int(row_count * 0.5)
    medium_count = int(row_count * 0.3)
    low_count = row_count - high_count - medium_count

    selected_scores = pd.concat(
        [
            high_risk.sort_values(
                "estimated_monthly_revenue_at_risk",
                ascending=False,
            ).head(high_count),
            medium_risk.sort_values(
                "estimated_monthly_revenue_at_risk",
                ascending=False,
            ).head(medium_count),
            low_risk.sort_values(
                "estimated_monthly_revenue_at_risk",
                ascending=False,
            ).head(low_count),
        ],
        ignore_index=True,
    )

    demo_customer_ids = selected_scores["customer_id"].tolist()

    demo_features = features.loc[features["customer_id"].isin(demo_customer_ids)].copy()
    demo_scores = scores.loc[scores["customer_id"].isin(demo_customer_ids)].copy()
    demo_features = demo_features.sort_values("customer_id").reset_index(drop=True)
    demo_scores = demo_scores.sort_values("customer_id").reset_index(drop=True)

    return demo_features, demo_scores


def write_demo_data(
    demo_features: pd.DataFrame,
    demo_scores: pd.DataFrame,
    demo_dir: Path = DEMO_DIR,
) -> tuple[Path, Path]:
    demo_dir.mkdir(parents=True, exist_ok=True)

    demo_features.to_parquet(DEMO_FEATURES_OUTPUT, index=False)
    demo_scores.to_parquet(DEMO_SCORES_OUTPUT, index=False)

    return DEMO_FEATURES_OUTPUT, DEMO_SCORES_OUTPUT


def main() -> None:
    demo_features, demo_scores = build_demo_data()
    features_path, scores_path = write_demo_data(demo_features, demo_scores)

    print(f"Demo feature rows: {len(demo_features):,} -> {features_path}")
    print(f"Demo score rows: {len(demo_scores):,} -> {scores_path}")
    print(
        "Demo risk category counts:\n"
        f"{demo_scores['risk_category'].value_counts().sort_index().to_string()}"
    )


if __name__ == "__main__":
    main()
