"""Clean and standardize the IBM Telco Customer Churn dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = Path("data/raw/ibm_telco_customer_churn.csv")
DEFAULT_OUTPUT = Path("data/processed/customers.parquet")

EXPECTED_COLUMNS = {
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
}


def normalize_category(series: pd.Series) -> pd.Series:
    """Convert category labels to lowercase snake-case strings."""
    return (
        series.astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )


def yes_no_to_boolean(series: pd.Series, column_name: str) -> pd.Series:
    """Convert strict Yes/No values to booleans."""
    unexpected = set(series.dropna().unique()) - {"Yes", "No"}

    if unexpected:
        raise ValueError(
            f"{column_name} contains unexpected values: {sorted(unexpected)}"
        )

    return series.map({"Yes": True, "No": False}).astype("boolean")


def validate_source(dataframe: pd.DataFrame) -> None:
    """Validate the source schema and customer identifiers."""
    missing_columns = EXPECTED_COLUMNS - set(dataframe.columns)
    unexpected_columns = set(dataframe.columns) - EXPECTED_COLUMNS

    if missing_columns or unexpected_columns:
        raise ValueError(
            "Source schema mismatch. "
            f"Missing: {sorted(missing_columns)}; "
            f"Unexpected: {sorted(unexpected_columns)}"
        )

    if dataframe["customerID"].isna().any():
        raise ValueError("customerID contains missing values")

    if dataframe["customerID"].duplicated().any():
        raise ValueError("customerID contains duplicate values")


def clean_customer_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a validated, standardized customer dataset."""
    validate_source(dataframe)

    cleaned = dataframe.copy()

    raw_total_charges = cleaned["TotalCharges"].astype("string").str.strip()
    numeric_total_charges = pd.to_numeric(raw_total_charges, errors="coerce")

    invalid_total_charges = numeric_total_charges.isna() & cleaned["tenure"].ne(0)

    if invalid_total_charges.any():
        invalid_count = int(invalid_total_charges.sum())
        raise ValueError(
            f"Found {invalid_count} invalid TotalCharges values "
            "for customers with nonzero tenure"
        )

    numeric_total_charges = numeric_total_charges.fillna(0.0)

    result = pd.DataFrame(
        {
            "customer_id": cleaned["customerID"].astype("string").str.strip(),
            "gender": normalize_category(cleaned["gender"]),
            "senior_citizen": cleaned["SeniorCitizen"].astype("boolean"),
            "has_partner": yes_no_to_boolean(cleaned["Partner"], "Partner"),
            "has_dependents": yes_no_to_boolean(cleaned["Dependents"], "Dependents"),
            "tenure_months": cleaned["tenure"].astype("int64"),
            "phone_service": yes_no_to_boolean(cleaned["PhoneService"], "PhoneService"),
            "multiple_lines": normalize_category(cleaned["MultipleLines"]),
            "internet_service": normalize_category(cleaned["InternetService"]),
            "online_security": normalize_category(cleaned["OnlineSecurity"]),
            "online_backup": normalize_category(cleaned["OnlineBackup"]),
            "device_protection": normalize_category(cleaned["DeviceProtection"]),
            "tech_support": normalize_category(cleaned["TechSupport"]),
            "streaming_tv": normalize_category(cleaned["StreamingTV"]),
            "streaming_movies": normalize_category(cleaned["StreamingMovies"]),
            "contract_type": normalize_category(cleaned["Contract"]),
            "paperless_billing": yes_no_to_boolean(
                cleaned["PaperlessBilling"], "PaperlessBilling"
            ),
            "payment_method": normalize_category(cleaned["PaymentMethod"]),
            "monthly_charges": cleaned["MonthlyCharges"].astype("float64"),
            "total_charges": numeric_total_charges.astype("float64"),
            "churned": yes_no_to_boolean(cleaned["Churn"], "Churn"),
            "source_system": "ibm_telco_sample",
            "is_synthetic": False,
        }
    )

    if result["customer_id"].duplicated().any():
        raise ValueError("Cleaned output contains duplicate customer IDs")

    return result


def main() -> None:
    """Clean the source CSV and write a Parquet dataset."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    if not arguments.input.exists():
        raise FileNotFoundError(f"Source dataset not found: {arguments.input}")

    source = pd.read_csv(arguments.input)
    cleaned = clean_customer_data(source)

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(arguments.output, index=False)

    print(f"Cleaned {len(cleaned):,} customer records")
    print(f"Output: {arguments.output}")
    print(f"Columns: {len(cleaned.columns)}")
    print(f"Churn rate: {cleaned['churned'].mean():.2%}")


if __name__ == "__main__":
    main()
