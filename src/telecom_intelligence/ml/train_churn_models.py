"""Train churn classification models from the customer feature table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

DEFAULT_FEATURES_PATH = Path("data/processed/customer_features.parquet")
DEFAULT_ARTIFACT_DIR = Path("models/artifacts")
RANDOM_SEED = 42
TARGET_COLUMN = "churned"
ID_COLUMNS = ["customer_id"]
EXCLUDED_COLUMNS = [
    TARGET_COLUMN,
    "source_system",
    "is_synthetic",
    "monthly_revenue_at_risk",
]


def load_feature_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing feature table: {path}. "
            "Run python -m telecom_intelligence.features.build_customer_features first."
        )

    features = pd.read_parquet(path)

    if TARGET_COLUMN not in features.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    return features


def split_features_target(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    excluded = set(EXCLUDED_COLUMNS + ID_COLUMNS)
    x = features.drop(
        columns=[column for column in excluded if column in features.columns]
    )
    y = features[TARGET_COLUMN].astype(int)
    return x, y


def column_groups(features: pd.DataFrame) -> tuple[list[str], list[str]]:
    categorical_columns = features.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()
    numeric_columns = features.select_dtypes(
        include=["number", "bool"]
    ).columns.tolist()
    return categorical_columns, numeric_columns


def build_preprocessor(features: pd.DataFrame) -> ColumnTransformer:
    categorical_columns, numeric_columns = column_groups(features)

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_columns,
            ),
            ("numeric", StandardScaler(), numeric_columns),
        ],
        remainder="drop",
    )


def candidate_models() -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2_000,
            class_weight="balanced",
            random_state=RANDOM_SEED,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
    }


def evaluate_predictions(
    y_true: pd.Series, probabilities: pd.Series
) -> dict[str, float]:
    predictions = probabilities.ge(0.5).astype(int)

    return {
        "roc_auc": roc_auc_score(y_true, probabilities),
        "average_precision": average_precision_score(y_true, probabilities),
        "accuracy": accuracy_score(y_true, predictions),
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
    }


def train_and_evaluate_models(
    features: pd.DataFrame,
) -> tuple[str, dict[str, dict[str, float]], Pipeline]:
    x, y = split_features_target(features)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    metrics: dict[str, dict[str, float]] = {}
    trained_pipelines: dict[str, Pipeline] = {}

    for model_name, model in candidate_models().items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(x_train)),
                ("model", model),
            ]
        )
        pipeline.fit(x_train, y_train)

        probabilities = pd.Series(
            pipeline.predict_proba(x_test)[:, 1],
            index=y_test.index,
        )
        metrics[model_name] = evaluate_predictions(y_test, probabilities)
        trained_pipelines[model_name] = pipeline

    best_model_name = max(metrics, key=lambda name: metrics[name]["roc_auc"])
    return best_model_name, metrics, trained_pipelines[best_model_name]


def write_metrics(metrics: dict[str, dict[str, float]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output_path


def write_model(model: Pipeline, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-path", type=Path, default=DEFAULT_FEATURES_PATH)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    args = parser.parse_args()

    features = load_feature_table(args.features_path)
    best_model_name, metrics, best_model = train_and_evaluate_models(features)

    metrics_path = write_metrics(
        metrics, args.artifact_dir / "churn_model_metrics.json"
    )
    model_path = write_model(best_model, args.artifact_dir / "churn_model.joblib")

    print(f"Rows: {len(features):,}")
    print(f"Target churn rate: {features[TARGET_COLUMN].mean():.2%}")
    print(f"Best model: {best_model_name}")
    print(f"Metrics: {metrics_path}")
    print(f"Model artifact: {model_path}")
    print(json.dumps(metrics[best_model_name], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
