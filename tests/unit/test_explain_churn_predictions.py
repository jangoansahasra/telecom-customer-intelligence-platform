import numpy as np

from telecom_intelligence.ml.explain_churn_predictions import (
    clean_feature_name,
    top_positive_factors,
)


def test_clean_feature_name_returns_business_labels() -> None:
    assert clean_feature_name("categorical__contract_type_month_to_month") == (
        "month-to-month contract"
    )
    assert clean_feature_name("numeric__late_payment_rate") == "late payment rate"


def test_top_positive_factors_returns_largest_positive_impacts() -> None:
    feature_names = [
        "numeric__tenure_months",
        "numeric__late_payment_count",
        "numeric__support_ticket_count",
        "numeric__total_mrr",
    ]
    shap_row = np.array([-0.2, 1.5, 0.7, 0.1])

    factors = top_positive_factors(shap_row, feature_names, top_n=3)

    assert factors == [
        ("late payment count", 1.5),
        ("support ticket volume", 0.7),
        ("total monthly recurring revenue", 0.1),
    ]


def test_top_positive_factors_falls_back_to_largest_absolute_impacts() -> None:
    feature_names = [
        "numeric__tenure_months",
        "numeric__late_payment_count",
        "numeric__support_ticket_count",
    ]
    shap_row = np.array([-1.2, -0.5, -0.1])

    factors = top_positive_factors(shap_row, feature_names, top_n=2)

    assert factors == [
        ("customer tenure", -1.2),
        ("late payment count", -0.5),
    ]
