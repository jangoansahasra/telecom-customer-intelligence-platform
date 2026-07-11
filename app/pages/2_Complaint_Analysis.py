"""Complaint analysis Streamlit page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

CLASSIFIED_TICKETS_PATH = Path("data/processed/classified_support_tickets.parquet")
DEMO_CLASSIFIED_TICKETS_PATH = Path("data/demo/classified_support_tickets_demo.parquet")


@st.cache_data
def load_classified_tickets() -> tuple[pd.DataFrame, str]:
    if CLASSIFIED_TICKETS_PATH.exists():
        tickets = pd.read_parquet(CLASSIFIED_TICKETS_PATH)
        return tickets, "full local processed dataset"

    if DEMO_CLASSIFIED_TICKETS_PATH.exists():
        tickets = pd.read_parquet(DEMO_CLASSIFIED_TICKETS_PATH)
        return tickets, "committed demo dataset"

    st.error(
        "Missing classified support tickets. Run "
        "`python -m telecom_intelligence.nlp.classify_complaints`."
    )
    st.stop()


def main() -> None:
    st.set_page_config(
        page_title="Complaint Analysis",
        page_icon="💬",
        layout="wide",
    )

    st.title("💬 Complaint Analysis")

    tickets, data_mode = load_classified_tickets()
    st.info(f"Data mode: {data_mode}")

    total_tickets = len(tickets)
    unique_customers = tickets["customer_id"].nunique()
    match_rate = tickets["complaint_category_matches_seed"].mean()

    metric_cols = st.columns(3)
    metric_cols[0].metric("Classified tickets", f"{total_tickets:,}")
    metric_cols[1].metric("Customers with tickets", f"{unique_customers:,}")
    metric_cols[2].metric("Seed-label match rate", f"{match_rate:.1%}")

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Predicted complaint categories")
        category_counts = (
            tickets["complaint_category_predicted"]
            .value_counts()
            .rename_axis("complaint_category")
            .reset_index(name="ticket_count")
        )
        fig = px.bar(
            category_counts,
            x="complaint_category",
            y="ticket_count",
            title="Tickets by predicted complaint category",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Classifier confidence")
        fig = px.box(
            tickets,
            x="complaint_category_predicted",
            y="complaint_category_score",
            title="Prediction confidence by category",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Classified ticket samples")
    st.dataframe(
        tickets[
            [
                "ticket_id",
                "customer_id",
                "complaint_category_seed",
                "complaint_category_predicted",
                "complaint_category_score",
                "complaint_category_matches_seed",
                "ticket_text",
            ]
        ].head(100),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Complaint categories are generated using Hugging Face Transformers "
        "zero-shot classification. The source support tickets are synthetic."
    )


if __name__ == "__main__":
    main()
