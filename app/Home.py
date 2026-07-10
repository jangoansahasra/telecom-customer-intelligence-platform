"""Streamlit app for the Telecom B2C Customer Intelligence Platform."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

FEATURES_PATH = Path("data/processed/customer_features.parquet")
SCORES_PATH = Path("data/processed/customer_risk_scores.parquet")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not FEATURES_PATH.exists():
        st.error(
            "Missing customer feature table. Run "
            "`python -m telecom_intelligence.features.build_customer_features` first."
        )
        st.stop()

    if not SCORES_PATH.exists():
        st.error(
            "Missing customer risk scores. Run "
            "`python -m telecom_intelligence.ml.score_customers` first."
        )
        st.stop()

    features = pd.read_parquet(FEATURES_PATH)
    scores = pd.read_parquet(SCORES_PATH)
    return features, scores


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def main() -> None:
    st.set_page_config(
        page_title="Telecom Customer Intelligence",
        page_icon="📡",
        layout="wide",
    )

    features, scores = load_data()
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

    st.title("📡 Telecom B2C Customer Intelligence Platform")
    st.caption(
        "Portfolio analytics platform using IBM Telco churn data plus clearly "
        "labeled synthetic telecom domain tables."
    )

    total_customers = len(customer_360)
    churn_rate = customer_360["churned"].mean()
    total_mrr = customer_360["total_mrr"].sum()
    expected_revenue_at_risk = customer_360["estimated_monthly_revenue_at_risk"].sum()

    metric_cols = st.columns(4)
    metric_cols[0].metric("Customers", f"{total_customers:,}")
    metric_cols[1].metric("Observed churn rate", f"{churn_rate:.1%}")
    metric_cols[2].metric("Monthly recurring revenue", format_currency(total_mrr))
    metric_cols[3].metric(
        "Expected monthly revenue at risk",
        format_currency(expected_revenue_at_risk),
    )

    st.divider()

    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Risk distribution")
        risk_counts = (
            customer_360["risk_category"]
            .value_counts()
            .rename_axis("risk_category")
            .reset_index(name="customer_count")
        )
        fig = px.bar(
            risk_counts,
            x="risk_category",
            y="customer_count",
            color="risk_category",
            title="Customers by churn risk category",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Recommended retention actions")
        action_counts = (
            customer_360["recommended_action"]
            .value_counts()
            .rename_axis("recommended_action")
            .reset_index(name="customer_count")
        )
        fig = px.bar(
            action_counts.head(10),
            x="customer_count",
            y="recommended_action",
            orientation="h",
            title="Top recommended actions",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Highest-priority customers")
    top_customers = customer_360.sort_values(
        "estimated_monthly_revenue_at_risk",
        ascending=False,
    ).head(25)

    st.dataframe(
        top_customers[
            [
                "customer_id",
                "risk_category",
                "retention_priority",
                "churn_probability",
                "total_mrr",
                "estimated_monthly_revenue_at_risk",
                "contract_type",
                "support_ticket_count",
                "network_incident_count",
                "recommended_action",
            ]
        ],
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
