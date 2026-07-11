"""Customer 360 Streamlit page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

FEATURES_PATH = Path("data/processed/customer_features.parquet")
SCORES_PATH = Path("data/processed/customer_risk_scores.parquet")
DEMO_FEATURES_PATH = Path("data/demo/customer_features_demo.parquet")
DEMO_SCORES_PATH = Path("data/demo/customer_risk_scores_demo.parquet")
EXPLANATIONS_PATH = Path("data/processed/customer_churn_explanations.parquet")
DEMO_EXPLANATIONS_PATH = Path("data/demo/customer_churn_explanations_demo.parquet")


@st.cache_data
def load_customer_360() -> tuple[pd.DataFrame, str]:
    explanations = None

    if FEATURES_PATH.exists() and SCORES_PATH.exists():
        features = pd.read_parquet(FEATURES_PATH)
        scores = pd.read_parquet(SCORES_PATH)
        data_mode = "full local processed dataset"

        if EXPLANATIONS_PATH.exists():
            explanations = pd.read_parquet(EXPLANATIONS_PATH)

    elif DEMO_FEATURES_PATH.exists() and DEMO_SCORES_PATH.exists():
        features = pd.read_parquet(DEMO_FEATURES_PATH)
        scores = pd.read_parquet(DEMO_SCORES_PATH)
        data_mode = "committed demo dataset"

        if DEMO_EXPLANATIONS_PATH.exists():
            explanations = pd.read_parquet(DEMO_EXPLANATIONS_PATH)
    else:
        st.error(
            "Missing customer data. Run the local pipeline or build demo data with "
            "`python scripts/build_demo_data.py`."
        )
        st.stop()

    customer_360 = features.merge(
        scores[
            [
                "customer_id",
                "churn_probability",
                "risk_category",
                "retention_priority",
                "recommended_action",
                "estimated_monthly_revenue_at_risk",
            ]
        ],
        on="customer_id",
        how="left",
    )

    if explanations is not None:
        explanation_columns = [
            "customer_id",
            "top_factor_1",
            "top_factor_1_impact",
            "top_factor_2",
            "top_factor_2_impact",
            "top_factor_3",
            "top_factor_3_impact",
        ]
        customer_360 = customer_360.merge(
            explanations[explanation_columns],
            on="customer_id",
            how="left",
        )

    return customer_360, data_mode


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def main() -> None:
    st.set_page_config(
        page_title="Customer 360",
        page_icon="👤",
        layout="wide",
    )

    st.title("👤 Customer 360")

    customer_360, data_mode = load_customer_360()
    st.info(f"Data mode: {data_mode}")

    selected_customer_id = st.selectbox(
        "Select a customer",
        customer_360["customer_id"].sort_values().tolist(),
    )

    customer = customer_360.loc[
        customer_360["customer_id"].eq(selected_customer_id)
    ].iloc[0]

    st.subheader(f"Customer {selected_customer_id}")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Risk category", customer["risk_category"])
    metric_cols[1].metric("Churn probability", f"{customer['churn_probability']:.1%}")
    metric_cols[2].metric("Total MRR", format_currency(customer["total_mrr"]))
    metric_cols[3].metric(
        "Expected revenue at risk",
        format_currency(customer["estimated_monthly_revenue_at_risk"]),
    )

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Profile")
        st.write(
            {
                "Contract": customer["contract_type"],
                "Internet service": customer["internet_service"],
                "Payment method": customer["payment_method"],
                "Tenure months": int(customer["tenure_months"]),
                "Has mobile": bool(customer["has_mobile"]),
                "Has BYOD": bool(customer["has_byod"]),
                "Has 5G": bool(customer["has_5g"]),
            }
        )
    st.subheader("Top churn risk factors")

    if "top_factor_1" in customer_360.columns:
        explanation_rows = [
            {
                "rank": 1,
                "factor": customer["top_factor_1"],
                "impact": customer["top_factor_1_impact"],
            },
            {
                "rank": 2,
                "factor": customer["top_factor_2"],
                "impact": customer["top_factor_2_impact"],
            },
            {
                "rank": 3,
                "factor": customer["top_factor_3"],
                "impact": customer["top_factor_3_impact"],
            },
        ]

        st.dataframe(
            pd.DataFrame(explanation_rows),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Positive SHAP impact values indicate features that pushed the churn "
            "prediction higher for this customer."
        )
    else:
        st.info(
            "SHAP explanations are not available yet. Run "
            "`python -m telecom_intelligence.ml.explain_churn_predictions`."
        )

    with right_col:
        st.subheader("Retention recommendation")
        st.write(
            {
                "Retention priority": customer["retention_priority"],
                "Recommended action": customer["recommended_action"],
                "Late payment rate": f"{customer['late_payment_rate']:.1%}",
                "Support tickets": int(customer["support_ticket_count"]),
                "Network incidents": int(customer["network_incident_count"]),
                "Cancellation requests": int(customer["cancellation_request_count"]),
            }
        )

    st.subheader("Feature details")
    st.dataframe(customer.to_frame(name="value"), use_container_width=True)


if __name__ == "__main__":
    main()
