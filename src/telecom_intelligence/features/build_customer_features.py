"""Build customer-level ML feature table from cleaned and synthetic data."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_INPUT_DIR = Path("data/processed")
DEFAULT_OUTPUT_PATH = Path("data/processed/customer_features.parquet")


def read_table(input_dir: Path, table_name: str) -> pd.DataFrame:
    path = input_dir / f"{table_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing required table: {path}. "
            "Run the customer cleaner and synthetic generator first."
        )
    return pd.read_parquet(path)


def summarize_fixed(fixed: pd.DataFrame) -> pd.DataFrame:
    return fixed.groupby("customer_id", as_index=False).agg(
        fixed_subscription_count=("fixed_subscription_id", "count"),
        fixed_mrr=("monthly_recurring_revenue", "sum"),
        max_download_speed_mbps=("download_speed_mbps", "max"),
    )


def summarize_mobile(mobile: pd.DataFrame) -> pd.DataFrame:
    return mobile.groupby("customer_id", as_index=False).agg(
        mobile_subscription_count=("mobile_subscription_id", "count"),
        mobile_line_count=("line_count", "sum"),
        mobile_mrr=("monthly_recurring_revenue", "sum"),
        has_5g=("is_5g_enabled", "max"),
    )


def summarize_byod(byod: pd.DataFrame) -> pd.DataFrame:
    return byod.groupby("customer_id", as_index=False).agg(
        byod_device_count=("device_id", "count"),
        avg_byod_device_age_months=("device_age_months", "mean"),
    )


def summarize_usage(usage: pd.DataFrame) -> pd.DataFrame:
    return usage.groupby("customer_id", as_index=False).agg(
        total_data_gb=("data_gb", "sum"),
        avg_monthly_data_gb=("data_gb", "mean"),
        total_voice_minutes=("voice_minutes", "sum"),
        total_sms_count=("sms_count", "sum"),
    )


def summarize_billing(billing: pd.DataFrame) -> pd.DataFrame:
    billing = billing.copy()
    billing["late_payment_flag"] = billing["payment_status"].eq("late")

    return billing.groupby("customer_id", as_index=False).agg(
        invoice_count=("invoice_id", "count"),
        total_invoice_amount=("invoice_amount", "sum"),
        avg_invoice_amount=("invoice_amount", "mean"),
        late_payment_count=("late_payment_flag", "sum"),
        avg_days_late=("days_late", "mean"),
    )


def summarize_network(network: pd.DataFrame) -> pd.DataFrame:
    return network.groupby("customer_id", as_index=False).agg(
        network_incident_count=("incident_id", "count"),
        total_incident_minutes=("duration_minutes", "sum"),
        avg_incident_minutes=("duration_minutes", "mean"),
    )


def summarize_support(support: pd.DataFrame) -> pd.DataFrame:
    support = support.copy()
    support["cancellation_request_flag"] = support["complaint_category_seed"].eq(
        "cancellation_request"
    )
    support["billing_complaint_flag"] = support["complaint_category_seed"].eq("billing")
    support["network_complaint_flag"] = support["complaint_category_seed"].isin(
        ["network_outage", "slow_internet"]
    )

    return support.groupby("customer_id", as_index=False).agg(
        support_ticket_count=("ticket_id", "count"),
        avg_resolution_hours=("resolution_hours", "mean"),
        cancellation_request_count=("cancellation_request_flag", "sum"),
        billing_complaint_count=("billing_complaint_flag", "sum"),
        network_complaint_count=("network_complaint_flag", "sum"),
    )


def summarize_retention(retention: pd.DataFrame) -> pd.DataFrame:
    return retention.groupby("customer_id", as_index=False).agg(
        retention_offer_count=("campaign_id", "count"),
        accepted_offer_count=("accepted_offer", "sum"),
        avg_offer_value=("offer_value", "mean"),
    )


def build_customer_features(input_dir: Path = DEFAULT_INPUT_DIR) -> pd.DataFrame:
    customers = read_table(input_dir, "customers")
    fixed = read_table(input_dir, "fixed_subscriptions")
    mobile = read_table(input_dir, "mobile_subscriptions")
    byod = read_table(input_dir, "byod_devices")
    usage = read_table(input_dir, "monthly_usage")
    billing = read_table(input_dir, "billing_history")
    network = read_table(input_dir, "network_incidents")
    support = read_table(input_dir, "support_tickets")
    retention = read_table(input_dir, "retention_campaigns")

    features = customers.copy()

    summaries = [
        summarize_fixed(fixed),
        summarize_mobile(mobile),
        summarize_byod(byod),
        summarize_usage(usage),
        summarize_billing(billing),
        summarize_network(network),
        summarize_support(support),
        summarize_retention(retention),
    ]

    for summary in summaries:
        features = features.merge(summary, on="customer_id", how="left")

    count_columns = [
        "fixed_subscription_count",
        "mobile_subscription_count",
        "mobile_line_count",
        "byod_device_count",
        "invoice_count",
        "late_payment_count",
        "network_incident_count",
        "support_ticket_count",
        "cancellation_request_count",
        "billing_complaint_count",
        "network_complaint_count",
        "retention_offer_count",
        "accepted_offer_count",
    ]

    amount_columns = [
        "fixed_mrr",
        "mobile_mrr",
        "max_download_speed_mbps",
        "avg_byod_device_age_months",
        "total_data_gb",
        "avg_monthly_data_gb",
        "total_voice_minutes",
        "total_sms_count",
        "total_invoice_amount",
        "avg_invoice_amount",
        "avg_days_late",
        "total_incident_minutes",
        "avg_incident_minutes",
        "avg_resolution_hours",
        "avg_offer_value",
    ]

    features[count_columns] = features[count_columns].fillna(0).astype(int)
    features[amount_columns] = features[amount_columns].fillna(0.0)
    features["has_5g"] = (
        features["has_5g"].where(features["has_5g"].notna(), False).astype(bool)
    )

    features["total_mrr"] = features["fixed_mrr"] + features["mobile_mrr"]
    features["monthly_revenue_at_risk"] = features["total_mrr"].where(
        features["churned"],
        0.0,
    )
    features["has_byod"] = features["byod_device_count"].gt(0)
    features["has_mobile"] = features["mobile_subscription_count"].gt(0)
    features["has_network_incident"] = features["network_incident_count"].gt(0)
    features["has_support_ticket"] = features["support_ticket_count"].gt(0)
    invoice_denominator = features["invoice_count"].replace(0, pd.NA)
    retention_denominator = features["retention_offer_count"].replace(0, pd.NA)

    features["late_payment_rate"] = (
        features["late_payment_count"] / invoice_denominator
    ).where(invoice_denominator.notna(), 0.0)

    features["retention_acceptance_rate"] = (
        features["accepted_offer_count"] / retention_denominator
    ).where(retention_denominator.notna(), 0.0)

    return features


def write_customer_features(features: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    features = build_customer_features(args.input_dir)
    output_path = write_customer_features(features, args.output_path)

    print(f"Customer feature rows: {len(features):,}")
    print(f"Customer feature columns: {features.shape[1]:,}")
    print(f"Output: {output_path}")
    print(f"Churn rate: {features['churned'].mean():.2%}")
    print(f"Monthly revenue at risk: ${features['monthly_revenue_at_risk'].sum():,.2f}")


if __name__ == "__main__":
    main()
