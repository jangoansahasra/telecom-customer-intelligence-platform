"""Generate SHAP-based churn explanations for customer predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

from telecom_intelligence.ml.train_churn_models import (
    DEFAULT_FEATURES_PATH,
    ID_COLUMNS,
    split_features_target,
)

DEFAULT_MODEL_PATH = Path("models/artifacts/churn_model.joblib")
DEFAULT_OUTPUT_PATH = Path("data/processed/customer_churn_explanations.parquet")
DEFAULT_DEMO_OUTPUT_PATH = Path("data/demo/customer_churn_explanations_demo.parquet")
DEMO_SCORES_PATH = Path("data/demo/customer_risk_scores_demo.parquet")
TOP_FACTOR_COUNT = 3


def load_feature_table(path: Path) -> pd.DataFrame:
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


def clean_feature_name(feature_name: str) -> str:
    cleaned = feature_name
    cleaned = cleaned.replace("categorical__", "")
    cleaned = cleaned.replace("numeric__", "")
    cleaned = cleaned.replace("_", " ")

    replacements = {
        "contract type month to month": "month-to-month contract",
        "contract type one year": "one-year contract",
        "contract type two year": "two-year contract",
        "internet service fiber optic": "fiber optic internet",
        "internet service dsl": "DSL internet",
        "payment method electronic check": "electronic check payment",
        "payment method mailed check": "mailed check payment",
        "tenure months": "customer tenure",
        "monthly charges": "monthly charges",
        "total mrr": "total monthly recurring revenue",
        "support ticket count": "support ticket volume",
        "network incident count": "network incident volume",
        "late payment count": "late payment count",
        "late payment rate": "late payment rate",
        "cancellation request count": "cancellation request count",
        "network complaint count": "network complaint count",
        "billing complaint count": "billing complaint count",
        "has byod": "BYOD customer",
        "has mobile": "mobile customer",
        "has 5g": "5G enabled",
    }

    return replacements.get(cleaned, cleaned)


def get_transformed_feature_names(pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocessor"]
    feature_names = preprocessor.get_feature_names_out()
    return [str(feature_name) for feature_name in feature_names]


def transformed_features(
    features: pd.DataFrame,
    pipeline,
) -> tuple[np.ndarray, list[str]]:
    x, _ = split_features_target(features)
    preprocessor = pipeline.named_steps["preprocessor"]
    transformed = preprocessor.transform(x)
    feature_names = get_transformed_feature_names(pipeline)
    return transformed, feature_names


def shap_values_for_churn(transformed: np.ndarray, pipeline) -> np.ndarray:
    model = pipeline.named_steps["model"]
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(transformed)

    if isinstance(shap_values, list):
        return np.asarray(shap_values[1])

    shap_values_array = np.asarray(shap_values)

    if shap_values_array.ndim == 3:
        return shap_values_array[:, :, 1]

    return shap_values_array


def top_positive_factors(
    shap_row: np.ndarray,
    feature_names: list[str],
    top_n: int = TOP_FACTOR_COUNT,
) -> list[tuple[str, float]]:
    factor_frame = pd.DataFrame(
        {
            "feature_name": feature_names,
            "impact": shap_row,
        }
    )

    positive_factors = factor_frame.loc[factor_frame["impact"].gt(0)].copy()

    if positive_factors.empty:
        positive_factors = factor_frame.reindex(
            factor_frame["impact"].abs().sort_values(ascending=False).index
        ).head(top_n)
    else:
        positive_factors = positive_factors.sort_values("impact", ascending=False).head(
            top_n
        )

    factors = [
        (clean_feature_name(row.feature_name), round(float(row.impact), 4))
        for row in positive_factors.itertuples(index=False)
    ]

    while len(factors) < top_n:
        factors.append(("No additional positive driver", 0.0))

    return factors


def build_explanations(features: pd.DataFrame, pipeline) -> pd.DataFrame:
    transformed, feature_names = transformed_features(features, pipeline)
    shap_values = shap_values_for_churn(transformed, pipeline)
    probabilities = pipeline.predict_proba(split_features_target(features)[0])[:, 1]

    explanation_records = []

    for row_index, customer_id in enumerate(features[ID_COLUMNS[0]]):
        factors = top_positive_factors(shap_values[row_index], feature_names)

        record = {
            "customer_id": customer_id,
            "churn_probability": round(float(probabilities[row_index]), 6),
        }

        for factor_number, (factor_name, impact) in enumerate(factors, start=1):
            record[f"top_factor_{factor_number}"] = factor_name
            record[f"top_factor_{factor_number}_impact"] = impact

        explanation_records.append(record)

    return pd.DataFrame(explanation_records)


def write_explanations(explanations: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    explanations.to_parquet(output_path, index=False)
    return output_path


def write_demo_explanations(
    explanations: pd.DataFrame,
    demo_scores_path: Path = DEMO_SCORES_PATH,
    output_path: Path = DEFAULT_DEMO_OUTPUT_PATH,
) -> Path | None:
    if not demo_scores_path.exists():
        return None

    demo_scores = pd.read_parquet(demo_scores_path)
    demo_explanations = explanations.loc[
        explanations["customer_id"].isin(demo_scores["customer_id"])
    ].copy()

    demo_explanations = demo_explanations.sort_values("customer_id").reset_index(
        drop=True
    )

    return write_explanations(demo_explanations, output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-path", type=Path, default=DEFAULT_FEATURES_PATH)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    features = load_feature_table(args.features_path)
    model = load_model(args.model_path)
    explanations = build_explanations(features, model)

    output_path = write_explanations(explanations, args.output_path)
    demo_output_path = write_demo_explanations(explanations)

    print(f"Explanation rows: {len(explanations):,}")
    print(f"Output: {output_path}")

    if demo_output_path:
        print(f"Demo output: {demo_output_path}")

    print("Sample explanations:")
    print(
        explanations[
            [
                "customer_id",
                "churn_probability",
                "top_factor_1",
                "top_factor_1_impact",
                "top_factor_2",
                "top_factor_2_impact",
                "top_factor_3",
                "top_factor_3_impact",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
