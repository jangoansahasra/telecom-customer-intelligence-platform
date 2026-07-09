import pandas as pd

from telecom_intelligence.ml.train_churn_models import (
    EXCLUDED_COLUMNS,
    split_features_target,
    train_and_evaluate_models,
)


def sample_feature_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_id": f"cust_{index:03d}",
                "contract_type": "month_to_month" if index % 2 else "one_year",
                "internet_service": "fiber_optic" if index % 3 else "dsl",
                "payment_method": "electronic_check" if index % 2 else "mailed_check",
                "tenure_months": index,
                "monthly_charges": 50 + index,
                "total_charges": (50 + index) * max(index, 1),
                "fixed_mrr": 50 + index,
                "mobile_mrr": 20 if index % 2 else 0,
                "total_mrr": 70 + index if index % 2 else 50 + index,
                "monthly_revenue_at_risk": 9999 if index % 4 == 0 else 0,
                "late_payment_count": index % 3,
                "support_ticket_count": index % 4,
                "network_incident_count": index % 5,
                "has_mobile": index % 2 == 1,
                "has_byod": index % 3 == 1,
                "has_5g": index % 2 == 0,
                "source_system": "unit_test",
                "is_synthetic": False,
                "churned": index % 4 == 0,
            }
            for index in range(1, 81)
        ]
    )


def test_split_features_target_excludes_target_and_leakage_columns() -> None:
    features = sample_feature_table()

    x, y = split_features_target(features)

    assert "customer_id" not in x.columns
    assert "churned" not in x.columns
    assert "source_system" not in x.columns
    assert "is_synthetic" not in x.columns
    assert "monthly_revenue_at_risk" not in x.columns
    assert "monthly_revenue_at_risk" in EXCLUDED_COLUMNS
    assert y.name == "churned"


def test_train_and_evaluate_models_returns_metrics_and_pipeline() -> None:
    best_model_name, metrics, best_model = train_and_evaluate_models(
        sample_feature_table()
    )

    assert best_model_name in metrics
    assert set(metrics) == {"logistic_regression", "random_forest", "xgboost"}

    for model_metrics in metrics.values():
        assert set(model_metrics) == {
            "roc_auc",
            "average_precision",
            "accuracy",
            "precision",
            "recall",
            "f1",
        }
        for value in model_metrics.values():
            assert 0.0 <= value <= 1.0

    assert hasattr(best_model, "predict_proba")
