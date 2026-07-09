import numpy as np
import pandas as pd

from telecom_intelligence.ml.score_customers import (
    assign_risk_category,
    recommend_retention_action,
    score_customers,
)


class FakeModel:
    def predict_proba(self, features):
        probabilities = np.array([0.2, 0.45, 0.8])
        return np.column_stack([1 - probabilities, probabilities])


def sample_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_id": "cust_low",
                "contract_type": "one_year",
                "churned": False,
                "monthly_charges": 50.0,
                "total_mrr": 50.0,
                "monthly_revenue_at_risk": 0.0,
                "support_ticket_count": 0,
                "network_incident_count": 0,
                "network_complaint_count": 0,
                "cancellation_request_count": 0,
                "late_payment_count": 0,
                "late_payment_rate": 0.0,
                "has_byod": False,
            },
            {
                "customer_id": "cust_medium",
                "contract_type": "month_to_month",
                "churned": False,
                "monthly_charges": 70.0,
                "total_mrr": 90.0,
                "monthly_revenue_at_risk": 0.0,
                "support_ticket_count": 1,
                "network_incident_count": 0,
                "network_complaint_count": 0,
                "cancellation_request_count": 0,
                "late_payment_count": 0,
                "late_payment_rate": 0.0,
                "has_byod": False,
            },
            {
                "customer_id": "cust_high",
                "contract_type": "two_year",
                "churned": True,
                "monthly_charges": 100.0,
                "total_mrr": 150.0,
                "monthly_revenue_at_risk": 150.0,
                "support_ticket_count": 2,
                "network_incident_count": 2,
                "network_complaint_count": 1,
                "cancellation_request_count": 1,
                "late_payment_count": 2,
                "late_payment_rate": 0.5,
                "has_byod": True,
            },
        ]
    )


def test_assign_risk_category_uses_expected_thresholds() -> None:
    categories = assign_risk_category(pd.Series([0.1, 0.3, 0.31, 0.6, 0.61]))

    assert categories.tolist() == ["low", "low", "medium", "medium", "high"]


def test_recommend_retention_action_prioritizes_cancellation_request() -> None:
    row = pd.Series(
        {
            "risk_category": "high",
            "cancellation_request_count": 1,
            "network_incident_count": 5,
            "network_complaint_count": 1,
            "late_payment_rate": 0.5,
            "contract_type": "month_to_month",
            "has_byod": True,
        }
    )

    assert recommend_retention_action(row) == "urgent_save_call"


def test_score_customers_outputs_risk_and_recommendations() -> None:
    scores = score_customers(sample_features(), FakeModel())

    assert set(scores["customer_id"]) == {"cust_low", "cust_medium", "cust_high"}
    assert set(scores["risk_category"]) == {"low", "medium", "high"}

    high_customer = scores.loc[scores["customer_id"].eq("cust_high")].iloc[0]
    medium_customer = scores.loc[scores["customer_id"].eq("cust_medium")].iloc[0]
    low_customer = scores.loc[scores["customer_id"].eq("cust_low")].iloc[0]

    assert high_customer["churn_probability"] == 0.8
    assert high_customer["estimated_monthly_revenue_at_risk"] == 120.0
    assert high_customer["recommended_action"] == "urgent_save_call"

    assert medium_customer["recommended_action"] == "contract_discount_offer"
    assert low_customer["recommended_action"] == "monitor"
