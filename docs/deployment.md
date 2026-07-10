# Deployment guide

This project includes a Streamlit application that can run locally or from a hosted deployment.

## Recommended hosting option

Use Streamlit Community Cloud for the first public deployment because it can deploy directly from GitHub and supports Streamlit apps with minimal configuration.

## App entrypoint

```text
app/Home.py
```
## Data mode

The application checks for full local processed files first:
```text
data/processed/customer_features.parquet
data/processed/customer_risk_scores.parquet
```

These files are ignored by Git because they are generated pipeline outputs.
If those files are unavailable, the app falls back to committed demo 
data:
```text
data/demo/customer_features_demo.parquet
data/demo/customer_risk_scores_demo.parquet
```
This allows the deployed app to run without committing the full processed dataset.

## Streamlit Community Cloud steps

1. Push the latest main branch to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Select the repository.
5. Set the branch to main.
6. Set the main file path to:
```text
app/Home.py
```
7. Deploy the app.
8. Confirm the app shows Data mode: committed demo dataset.
## Local run
From the project root:
```text
streamlit run app/Home.py
```
## Local pipeline refresh
To rebuild local data before running the app:
```text
python -m telecom_intelligence.ingestion.clean_customers
python -m telecom_intelligence.synthetic.generate_telecom_data
python -m telecom_intelligence.features.build_customer_features
python -m telecom_intelligence.ml.train_churn_models
python -m telecom_intelligence.ml.score_customers
python scripts/build_demo_data.py
```
## Notes
- Raw source data is not committed.
- Full processed data is not committed.
- Model artifacts are not committed.
- Demo data is committed for deployment and portfolio review.