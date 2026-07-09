"""Generate documented synthetic telecom domain tables.

The IBM Telco Customer Churn dataset is the real public source foundation.
The tables generated here are synthetic extensions used for portfolio-scale
analytics, modeling, and dashboard demos.

Synthetic records must always be labeled with is_synthetic = True.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_CUSTOMERS_INPUT = Path("data/processed/customers.parquet")
DEFAULT_OUTPUT_DIR = Path("data/processed")
RANDOM_SEED = 42


def load_customers(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing cleaned customer file: {path}. "
            "Run python -m telecom_intelligence.ingestion.clean_customers first."
        )

    customers = pd.read_parquet(path)

    required_columns = {
        "customer_id",
        "tenure_months",
        "monthly_charges",
        "total_charges",
        "contract_type",
        "internet_service",
        "phone_service",
        "churned",
    }
    missing_columns = required_columns - set(customers.columns)
    if missing_columns:
        raise ValueError(
            f"Customers file is missing columns: {sorted(missing_columns)}"
        )

    return customers


def choose_subscription_status(churned: pd.Series) -> np.ndarray:
    return np.where(churned, "cancelled", "active")


def generate_fixed_subscriptions(customers: pd.DataFrame) -> pd.DataFrame:
    fixed = customers[
        [
            "customer_id",
            "tenure_months",
            "monthly_charges",
            "contract_type",
            "internet_service",
            "churned",
        ]
    ].copy()

    fixed["fixed_subscription_id"] = [
        f"fix_{index:06d}" for index in range(1, len(fixed) + 1)
    ]
    fixed["service_type"] = "fixed_broadband"
    fixed["plan_name"] = np.select(
        [
            fixed["internet_service"].eq("fiber_optic"),
            fixed["internet_service"].eq("dsl"),
        ],
        ["Fiber Max", "DSL Essential"],
        default="Voice Only",
    )
    fixed["download_speed_mbps"] = np.select(
        [
            fixed["internet_service"].eq("fiber_optic"),
            fixed["internet_service"].eq("dsl"),
        ],
        [500, 100],
        default=0,
    )
    fixed["monthly_recurring_revenue"] = fixed["monthly_charges"].round(2)
    fixed["subscription_status"] = choose_subscription_status(fixed["churned"])
    fixed["is_synthetic"] = True

    return fixed[
        [
            "fixed_subscription_id",
            "customer_id",
            "service_type",
            "plan_name",
            "download_speed_mbps",
            "contract_type",
            "monthly_recurring_revenue",
            "subscription_status",
            "is_synthetic",
        ]
    ]


def generate_mobile_subscriptions(
    customers: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    mobile_probability = np.where(customers["phone_service"], 0.72, 0.38)
    has_mobile = rng.random(len(customers)) < mobile_probability
    mobile_customers = customers.loc[has_mobile].copy().reset_index(drop=True)

    plan_names = rng.choice(
        ["Mobile Starter", "Mobile Unlimited", "Family Share", "Premium 5G"],
        size=len(mobile_customers),
        p=[0.25, 0.35, 0.25, 0.15],
    )

    plan_mrr = {
        "Mobile Starter": 35.0,
        "Mobile Unlimited": 65.0,
        "Family Share": 95.0,
        "Premium 5G": 85.0,
    }

    mobile = pd.DataFrame(
        {
            "mobile_subscription_id": [
                f"mob_{index:06d}" for index in range(1, len(mobile_customers) + 1)
            ],
            "customer_id": mobile_customers["customer_id"],
            "service_type": "mobile",
            "plan_name": plan_names,
            "line_count": rng.choice(
                [1, 2, 3, 4],
                size=len(mobile_customers),
                p=[0.55, 0.25, 0.12, 0.08],
            ),
            "is_5g_enabled": rng.random(len(mobile_customers)) < 0.64,
            "monthly_recurring_revenue": [plan_mrr[name] for name in plan_names],
            "subscription_status": choose_subscription_status(
                mobile_customers["churned"]
            ),
            "is_synthetic": True,
        }
    )

    return mobile


def generate_byod_devices(
    mobile_subscriptions: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    has_byod = rng.random(len(mobile_subscriptions)) < 0.58
    byod_base = mobile_subscriptions.loc[has_byod].copy().reset_index(drop=True)

    device = pd.DataFrame(
        {
            "device_id": [f"dev_{index:06d}" for index in range(1, len(byod_base) + 1)],
            "customer_id": byod_base["customer_id"],
            "mobile_subscription_id": byod_base["mobile_subscription_id"],
            "device_ownership": "byod",
            "device_os": rng.choice(
                ["ios", "android"],
                size=len(byod_base),
                p=[0.52, 0.48],
            ),
            "device_age_months": rng.integers(1, 49, size=len(byod_base)),
            "is_synthetic": True,
        }
    )

    return device


def generate_monthly_usage(
    customers: pd.DataFrame,
    fixed_subscriptions: pd.DataFrame,
    mobile_subscriptions: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    months = pd.period_range("2024-01", "2024-12", freq="M").astype(str)
    usage_records = []

    fixed_lookup = fixed_subscriptions.set_index("customer_id")
    mobile_lookup = mobile_subscriptions.set_index("customer_id")

    for customer in customers.itertuples(index=False):
        for month in months:
            if customer.customer_id in fixed_lookup.index:
                fixed_row = fixed_lookup.loc[customer.customer_id]
                usage_records.append(
                    {
                        "usage_id": f"use_{len(usage_records) + 1:08d}",
                        "customer_id": customer.customer_id,
                        "subscription_id": fixed_row.fixed_subscription_id,
                        "service_type": "fixed_broadband",
                        "usage_month": month,
                        "data_gb": round(
                            float(np.clip(rng.normal(420, 140), 25, 1200)), 2
                        ),
                        "voice_minutes": 0,
                        "sms_count": 0,
                        "is_synthetic": True,
                    }
                )

            if customer.customer_id in mobile_lookup.index:
                mobile_row = mobile_lookup.loc[customer.customer_id]
                usage_records.append(
                    {
                        "usage_id": f"use_{len(usage_records) + 1:08d}",
                        "customer_id": customer.customer_id,
                        "subscription_id": mobile_row.mobile_subscription_id,
                        "service_type": "mobile",
                        "usage_month": month,
                        "data_gb": round(float(np.clip(rng.normal(18, 8), 1, 80)), 2),
                        "voice_minutes": int(np.clip(rng.normal(420, 160), 0, 1500)),
                        "sms_count": int(np.clip(rng.normal(85, 45), 0, 500)),
                        "is_synthetic": True,
                    }
                )

    return pd.DataFrame(usage_records)


def generate_billing_history(
    customers: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    months = pd.period_range("2024-01", "2024-12", freq="M").astype(str)
    records = []

    for customer in customers.itertuples(index=False):
        for month in months:
            late_payment = rng.random() < (0.18 if customer.churned else 0.08)
            records.append(
                {
                    "invoice_id": f"inv_{len(records) + 1:08d}",
                    "customer_id": customer.customer_id,
                    "billing_month": month,
                    "invoice_amount": round(
                        float(customer.monthly_charges + rng.normal(0, 6)),
                        2,
                    ),
                    "payment_status": "late" if late_payment else "paid",
                    "days_late": int(rng.integers(1, 31)) if late_payment else 0,
                    "is_synthetic": True,
                }
            )

    return pd.DataFrame(records)


def generate_network_incidents(
    customers: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    incident_customers = customers.sample(
        frac=0.32,
        random_state=RANDOM_SEED,
    ).reset_index(drop=True)
    records = []

    for customer in incident_customers.itertuples(index=False):
        incident_count = int(rng.choice([1, 2, 3], p=[0.72, 0.22, 0.06]))
        for _ in range(incident_count):
            records.append(
                {
                    "incident_id": f"net_{len(records) + 1:07d}",
                    "customer_id": customer.customer_id,
                    "incident_month": str(
                        rng.choice(
                            pd.period_range("2024-01", "2024-12", freq="M").astype(str)
                        )
                    ),
                    "incident_type": rng.choice(
                        ["outage", "slow_speed", "packet_loss", "maintenance"],
                        p=[0.28, 0.38, 0.18, 0.16],
                    ),
                    "duration_minutes": int(
                        np.clip(rng.gamma(shape=2.0, scale=45.0), 5, 720)
                    ),
                    "service_affected": rng.choice(
                        ["fixed_broadband", "mobile"],
                        p=[0.72, 0.28],
                    ),
                    "is_synthetic": True,
                }
            )

    return pd.DataFrame(records)


def generate_support_tickets(
    customers: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    category_templates = {
        "billing": (
            "Customer says the bill is higher than expected and asks for an "
            "explanation."
        ),
        "network_outage": (
            "Customer reports service is unavailable after an outage in the area."
        ),
        "slow_internet": (
            "Customer complains that internet speed is much slower than promised."
        ),
        "device_problem": (
            "Customer says their device is not connecting correctly to the network."
        ),
        "activation_issue": (
            "Customer reports that the new service activation is delayed."
        ),
        "pricing_complaint": ("Customer says the current plan price is too expensive."),
        "cancellation_request": (
            "Customer asks how to cancel service because they are unhappy."
        ),
    }

    records = []
    for customer in customers.itertuples(index=False):
        ticket_probability = 0.48 if customer.churned else 0.24
        if rng.random() >= ticket_probability:
            continue

        ticket_count = int(rng.choice([1, 2, 3], p=[0.76, 0.19, 0.05]))
        for _ in range(ticket_count):
            category = str(
                rng.choice(
                    list(category_templates),
                    p=[0.18, 0.14, 0.2, 0.11, 0.09, 0.13, 0.15],
                )
            )
            records.append(
                {
                    "ticket_id": f"tic_{len(records) + 1:07d}",
                    "customer_id": customer.customer_id,
                    "ticket_month": str(
                        rng.choice(
                            pd.period_range("2024-01", "2024-12", freq="M").astype(str)
                        )
                    ),
                    "complaint_category_seed": category,
                    "ticket_text": category_templates[category],
                    "priority": rng.choice(
                        ["low", "medium", "high"],
                        p=[0.42, 0.43, 0.15],
                    ),
                    "resolution_hours": round(
                        float(np.clip(rng.gamma(shape=2.2, scale=9.0), 1, 168)),
                        2,
                    ),
                    "is_synthetic": True,
                }
            )

    return pd.DataFrame(records)


def generate_retention_campaigns(
    customers: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    eligible = customers.loc[
        (customers["churned"]) | (customers["contract_type"].eq("month_to_month"))
    ].copy()

    targeted = eligible.sample(frac=0.45, random_state=RANDOM_SEED).reset_index(
        drop=True
    )
    offer_types = rng.choice(
        [
            "discount_10_percent",
            "free_speed_upgrade",
            "device_credit",
            "contract_bonus",
        ],
        size=len(targeted),
        p=[0.38, 0.25, 0.22, 0.15],
    )

    accepted = rng.random(len(targeted)) < np.where(targeted["churned"], 0.18, 0.34)

    return pd.DataFrame(
        {
            "campaign_id": [
                f"ret_{index:07d}" for index in range(1, len(targeted) + 1)
            ],
            "customer_id": targeted["customer_id"],
            "campaign_month": rng.choice(
                pd.period_range("2024-01", "2024-12", freq="M").astype(str),
                size=len(targeted),
            ),
            "offer_type": offer_types,
            "offer_value": rng.choice([10, 15, 20, 25, 30], size=len(targeted)),
            "accepted_offer": accepted,
            "is_synthetic": True,
        }
    )


def write_table(dataframe: pd.DataFrame, output_dir: Path, table_name: str) -> Path:
    output_path = output_dir / f"{table_name}.parquet"
    dataframe.to_parquet(output_path, index=False)
    return output_path


def generate_all(customers_path: Path, output_dir: Path) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(RANDOM_SEED)
    customers = load_customers(customers_path)

    fixed_subscriptions = generate_fixed_subscriptions(customers)
    mobile_subscriptions = generate_mobile_subscriptions(customers, rng)
    byod_devices = generate_byod_devices(mobile_subscriptions, rng)
    monthly_usage = generate_monthly_usage(
        customers,
        fixed_subscriptions,
        mobile_subscriptions,
        rng,
    )
    billing_history = generate_billing_history(customers, rng)
    network_incidents = generate_network_incidents(customers, rng)
    support_tickets = generate_support_tickets(customers, rng)
    retention_campaigns = generate_retention_campaigns(customers, rng)

    return {
        "fixed_subscriptions": fixed_subscriptions,
        "mobile_subscriptions": mobile_subscriptions,
        "byod_devices": byod_devices,
        "monthly_usage": monthly_usage,
        "billing_history": billing_history,
        "network_incidents": network_incidents,
        "support_tickets": support_tickets,
        "retention_campaigns": retention_campaigns,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers-path", type=Path, default=DEFAULT_CUSTOMERS_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    tables = generate_all(args.customers_path, args.output_dir)

    for table_name, dataframe in tables.items():
        output_path = write_table(dataframe, args.output_dir, table_name)
        print(f"{table_name}: {len(dataframe):,} rows -> {output_path}")


if __name__ == "__main__":
    main()
