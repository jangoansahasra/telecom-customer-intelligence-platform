import numpy as np
import pandas as pd

from telecom_intelligence.synthetic.generate_telecom_data import (
    RANDOM_SEED,
    generate_all,
    generate_byod_devices,
    generate_fixed_subscriptions,
    generate_mobile_subscriptions,
)


def sample_customers() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_id": "0001-AAAAA",
                "tenure_months": 12,
                "monthly_charges": 70.0,
                "total_charges": 840.0,
                "contract_type": "month_to_month",
                "internet_service": "fiber_optic",
                "phone_service": True,
                "churned": False,
            },
            {
                "customer_id": "0002-BBBBB",
                "tenure_months": 24,
                "monthly_charges": 45.0,
                "total_charges": 1080.0,
                "contract_type": "one_year",
                "internet_service": "dsl",
                "phone_service": True,
                "churned": True,
            },
            {
                "customer_id": "0003-CCCCC",
                "tenure_months": 3,
                "monthly_charges": 20.0,
                "total_charges": 60.0,
                "contract_type": "two_year",
                "internet_service": "no",
                "phone_service": False,
                "churned": False,
            },
        ]
    )


def test_fixed_subscriptions_have_one_row_per_customer() -> None:
    fixed = generate_fixed_subscriptions(sample_customers())

    assert len(fixed) == 3
    assert fixed["fixed_subscription_id"].is_unique
    assert fixed["customer_id"].is_unique
    assert fixed["is_synthetic"].eq(True).all()
    assert set(fixed["service_type"]) == {"fixed_broadband"}


def test_fixed_subscriptions_map_plans_from_internet_service() -> None:
    fixed = generate_fixed_subscriptions(sample_customers())

    assert fixed["plan_name"].tolist() == [
        "Fiber Max",
        "DSL Essential",
        "Voice Only",
    ]
    assert fixed["download_speed_mbps"].tolist() == [500, 100, 0]


def test_mobile_subscriptions_are_reproducible_with_seed() -> None:
    customers = sample_customers()

    first = generate_mobile_subscriptions(
        customers,
        np.random.default_rng(RANDOM_SEED),
    )
    second = generate_mobile_subscriptions(
        customers,
        np.random.default_rng(RANDOM_SEED),
    )

    pd.testing.assert_frame_equal(first, second)
    assert first["mobile_subscription_id"].is_unique
    assert first["is_synthetic"].eq(True).all()


def test_byod_devices_reference_mobile_subscriptions() -> None:
    mobile = generate_mobile_subscriptions(
        sample_customers(),
        np.random.default_rng(RANDOM_SEED),
    )
    byod = generate_byod_devices(mobile, np.random.default_rng(RANDOM_SEED))

    assert byod["device_id"].is_unique
    assert byod["mobile_subscription_id"].isin(mobile["mobile_subscription_id"]).all()
    assert byod["customer_id"].isin(mobile["customer_id"]).all()
    assert byod["is_synthetic"].eq(True).all()


def test_generate_all_writes_expected_table_collection(tmp_path) -> None:
    customers_path = tmp_path / "customers.parquet"
    sample_customers().to_parquet(customers_path, index=False)

    tables = generate_all(customers_path, tmp_path)

    assert set(tables) == {
        "fixed_subscriptions",
        "mobile_subscriptions",
        "byod_devices",
        "monthly_usage",
        "billing_history",
        "network_incidents",
        "support_tickets",
        "retention_campaigns",
    }
    assert len(tables["fixed_subscriptions"]) == 3
    assert len(tables["billing_history"]) == 36
    assert tables["billing_history"]["is_synthetic"].eq(True).all()
