import pandas as pd
import pytest

from telecom_intelligence.ingestion.clean_customers import clean_customer_data


def sample_source_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customerID": "0001-AAAAA",
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "tenure": 0,
                "PhoneService": "No",
                "MultipleLines": "No phone service",
                "InternetService": "DSL",
                "OnlineSecurity": "No",
                "OnlineBackup": "Yes",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "No",
                "StreamingMovies": "No",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 29.85,
                "TotalCharges": " ",
                "Churn": "No",
            },
            {
                "customerID": "0002-BBBBB",
                "gender": "Male",
                "SeniorCitizen": 1,
                "Partner": "No",
                "Dependents": "Yes",
                "tenure": 12,
                "PhoneService": "Yes",
                "MultipleLines": "Yes",
                "InternetService": "Fiber optic",
                "OnlineSecurity": "No internet service",
                "OnlineBackup": "No",
                "DeviceProtection": "Yes",
                "TechSupport": "No",
                "StreamingTV": "Yes",
                "StreamingMovies": "Yes",
                "Contract": "One year",
                "PaperlessBilling": "No",
                "PaymentMethod": "Bank transfer (automatic)",
                "MonthlyCharges": 70.25,
                "TotalCharges": "843.00",
                "Churn": "Yes",
            },
        ]
    )


def test_clean_customer_data_standardizes_columns_and_values() -> None:
    cleaned = clean_customer_data(sample_source_df())

    assert cleaned.shape == (2, 23)
    assert cleaned["customer_id"].tolist() == ["0001-AAAAA", "0002-BBBBB"]
    assert cleaned["contract_type"].tolist() == ["month_to_month", "one_year"]
    assert cleaned["payment_method"].tolist() == [
        "electronic_check",
        "bank_transfer_automatic",
    ]
    assert cleaned["source_system"].unique().tolist() == ["ibm_telco_sample"]
    assert cleaned["is_synthetic"].unique().tolist() == [False]


def test_blank_total_charges_with_zero_tenure_becomes_zero() -> None:
    cleaned = clean_customer_data(sample_source_df())

    assert cleaned.loc[0, "tenure_months"] == 0
    assert cleaned.loc[0, "total_charges"] == 0.0


def test_invalid_total_charges_with_nonzero_tenure_raises() -> None:
    source = sample_source_df()
    source.loc[1, "TotalCharges"] = "not-a-number"

    with pytest.raises(ValueError, match="invalid TotalCharges"):
        clean_customer_data(source)


def test_duplicate_customer_ids_raise() -> None:
    source = sample_source_df()
    source.loc[1, "customerID"] = source.loc[0, "customerID"]

    with pytest.raises(ValueError, match="duplicate"):
        clean_customer_data(source)


def test_unexpected_yes_no_value_raises() -> None:
    source = sample_source_df()
    source.loc[0, "Partner"] = "Maybe"

    with pytest.raises(ValueError, match="unexpected values"):
        clean_customer_data(source)
