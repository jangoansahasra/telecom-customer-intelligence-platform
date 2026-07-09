"""Profile the raw IBM Telco Customer Churn dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = Path("data/raw/ibm_telco_customer_churn.csv")
DEFAULT_OUTPUT = Path("data/interim/source_profile.json")


def calculate_sha256(file_path: Path) -> str:
    """Return the SHA-256 checksum of a file."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_profile(file_path: Path) -> dict:
    """Create a reusable quality profile without modifying the raw file."""
    dataframe = pd.read_csv(file_path)

    blank_counts = {
        column: int(dataframe[column].astype("string").str.strip().eq("").sum())
        for column in dataframe.columns
    }

    total_charges_numeric = pd.to_numeric(dataframe["TotalCharges"], errors="coerce")

    return {
        "source_file": str(file_path),
        "sha256": calculate_sha256(file_path),
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": dataframe.columns.tolist(),
        "data_types": {
            column: str(dtype) for column, dtype in dataframe.dtypes.items()
        },
        "duplicate_row_count": int(dataframe.duplicated().sum()),
        "duplicate_customer_id_count": int(dataframe["customerID"].duplicated().sum()),
        "null_counts": {
            column: int(count) for column, count in dataframe.isna().sum().items()
        },
        "blank_string_counts": blank_counts,
        "unique_value_counts": {
            column: int(dataframe[column].nunique(dropna=True))
            for column in dataframe.columns
        },
        "churn_distribution": {
            str(label): int(count)
            for label, count in dataframe["Churn"].value_counts().items()
        },
        "total_charges_parse_failure_count": int(total_charges_numeric.isna().sum()),
        "tenure_range": {
            "minimum": int(dataframe["tenure"].min()),
            "maximum": int(dataframe["tenure"].max()),
        },
        "monthly_charges_range": {
            "minimum": float(dataframe["MonthlyCharges"].min()),
            "maximum": float(dataframe["MonthlyCharges"].max()),
        },
    }


def main() -> None:
    """Run source profiling and write a JSON report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    if not arguments.input.exists():
        raise FileNotFoundError(f"Source dataset not found: {arguments.input}")

    profile = build_profile(arguments.input)

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(profile, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(profile, indent=2))
    print(f"\nProfile written to {arguments.output}")


if __name__ == "__main__":
    main()
