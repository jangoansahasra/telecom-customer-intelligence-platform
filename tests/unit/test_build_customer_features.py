import pandas as pd

from telecom_intelligence.features.build_customer_features import (
    build_customer_features,
)


def write_table(input_dir, table_name: str, dataframe: pd.DataFrame) -> None:
    dataframe.to_parquet(input_dir / f"{table_name}.parquet", index=False)


def test_build_customer_features_combines_domain_summaries(tmp_path) -> None:
    write_table(
        tmp_path,
        "customers",
        pd.DataFrame(
            [
                {
                    "customer_id": "cust_1",
                    "gender": "female",
                    "senior_citizen": False,
                    "has_partner": True,
                    "has_dependents": False,
                    "tenure_months": 12,
                    "phone_service": True,
                    "multiple_lines": "no",
                    "internet_service": "fiber_optic",
                    "online_security": "yes",
                    "online_backup": "no",
                    "device_protection": "yes",
                    "tech_support": "no",
                    "streaming_tv": "yes",
                    "streaming_movies": "no",
                    "contract_type": "month_to_month",
                    "paperless_billing": True,
                    "payment_method": "electronic_check",
                    "monthly_charges": 80.0,
                    "total_charges": 960.0,
                    "churned": True,
                    "source_system": "unit_test",
                    "is_synthetic": False,
                },
                {
                    "customer_id": "cust_2",
                    "gender": "male",
                    "senior_citizen": False,
                    "has_partner": False,
                    "has_dependents": True,
                    "tenure_months": 24,
                    "phone_service": True,
                    "multiple_lines": "yes",
                    "internet_service": "dsl",
                    "online_security": "no",
                    "online_backup": "yes",
                    "device_protection": "no",
                    "tech_support": "yes",
                    "streaming_tv": "no",
                    "streaming_movies": "yes",
                    "contract_type": "one_year",
                    "paperless_billing": False,
                    "payment_method": "mailed_check",
                    "monthly_charges": 50.0,
                    "total_charges": 1200.0,
                    "churned": False,
                    "source_system": "unit_test",
                    "is_synthetic": False,
                },
            ]
        ),
    )

    write_table(
        tmp_path,
        "fixed_subscriptions",
        pd.DataFrame(
            [
                {
                    "fixed_subscription_id": "fix_1",
                    "customer_id": "cust_1",
                    "monthly_recurring_revenue": 80.0,
                    "download_speed_mbps": 500,
                },
                {
                    "fixed_subscription_id": "fix_2",
                    "customer_id": "cust_2",
                    "monthly_recurring_revenue": 50.0,
                    "download_speed_mbps": 100,
                },
            ]
        ),
    )

    write_table(
        tmp_path,
        "mobile_subscriptions",
        pd.DataFrame(
            [
                {
                    "mobile_subscription_id": "mob_1",
                    "customer_id": "cust_1",
                    "line_count": 2,
                    "monthly_recurring_revenue": 65.0,
                    "is_5g_enabled": True,
                }
            ]
        ),
    )

    write_table(
        tmp_path,
        "byod_devices",
        pd.DataFrame(
            [
                {
                    "device_id": "dev_1",
                    "customer_id": "cust_1",
                    "device_age_months": 10,
                }
            ]
        ),
    )

    write_table(
        tmp_path,
        "monthly_usage",
        pd.DataFrame(
            [
                {
                    "customer_id": "cust_1",
                    "data_gb": 100.0,
                    "voice_minutes": 200,
                    "sms_count": 50,
                },
                {
                    "customer_id": "cust_1",
                    "data_gb": 200.0,
                    "voice_minutes": 300,
                    "sms_count": 60,
                },
                {
                    "customer_id": "cust_2",
                    "data_gb": 50.0,
                    "voice_minutes": 100,
                    "sms_count": 10,
                },
            ]
        ),
    )

    write_table(
        tmp_path,
        "billing_history",
        pd.DataFrame(
            [
                {
                    "invoice_id": "inv_1",
                    "customer_id": "cust_1",
                    "invoice_amount": 80.0,
                    "payment_status": "late",
                    "days_late": 5,
                },
                {
                    "invoice_id": "inv_2",
                    "customer_id": "cust_1",
                    "invoice_amount": 80.0,
                    "payment_status": "paid",
                    "days_late": 0,
                },
                {
                    "invoice_id": "inv_3",
                    "customer_id": "cust_2",
                    "invoice_amount": 50.0,
                    "payment_status": "paid",
                    "days_late": 0,
                },
            ]
        ),
    )

    write_table(
        tmp_path,
        "network_incidents",
        pd.DataFrame(
            [
                {
                    "incident_id": "net_1",
                    "customer_id": "cust_1",
                    "duration_minutes": 30,
                }
            ]
        ),
    )

    write_table(
        tmp_path,
        "support_tickets",
        pd.DataFrame(
            [
                {
                    "ticket_id": "tic_1",
                    "customer_id": "cust_1",
                    "complaint_category_seed": "cancellation_request",
                    "resolution_hours": 12.0,
                },
                {
                    "ticket_id": "tic_2",
                    "customer_id": "cust_1",
                    "complaint_category_seed": "network_outage",
                    "resolution_hours": 24.0,
                },
            ]
        ),
    )

    write_table(
        tmp_path,
        "retention_campaigns",
        pd.DataFrame(
            [
                {
                    "campaign_id": "ret_1",
                    "customer_id": "cust_1",
                    "accepted_offer": True,
                    "offer_value": 20.0,
                }
            ]
        ),
    )

    features = (
        build_customer_features(tmp_path)
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    cust_1 = features.loc[features["customer_id"].eq("cust_1")].iloc[0]
    cust_2 = features.loc[features["customer_id"].eq("cust_2")].iloc[0]

    assert features.shape[0] == 2

    assert cust_1["fixed_mrr"] == 80.0
    assert cust_1["mobile_mrr"] == 65.0
    assert cust_1["total_mrr"] == 145.0
    assert cust_1["monthly_revenue_at_risk"] == 145.0
    assert bool(cust_1["has_mobile"]) is True
    assert bool(cust_1["has_byod"]) is True
    assert cust_1["late_payment_count"] == 1
    assert cust_1["late_payment_rate"] == 0.5
    assert cust_1["support_ticket_count"] == 2
    assert cust_1["cancellation_request_count"] == 1
    assert cust_1["network_complaint_count"] == 1
    assert cust_1["retention_acceptance_rate"] == 1.0

    assert cust_2["mobile_mrr"] == 0
    assert cust_2["monthly_revenue_at_risk"] == 0
    assert bool(cust_2["has_mobile"]) is False
    assert bool(cust_2["has_byod"]) is False
    assert cust_2["late_payment_rate"] == 0
