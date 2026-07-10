"""Customer 360 Streamlit page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

FEATURES_PATH = Path("data/processed/customer_features.parquet")
SCORES_PATH = Path("data/processed/customer_risk_scores.parquet")


@st.cache_data
def load_customer_360() -> pd.DataFrame:
    features = pd.read_parquet(FEATURES_PATH)
    scores = pd.read_parquet(SCORES_PATH)

    return features.merge(
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


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def main() -> None:
    st.set_page_config(
        page_title="Customer 360",
        page_icon="👤",
        layout="wide",
    )

    st.title("👤 Customer 360")

    customer_360 = load_customer_360()

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
