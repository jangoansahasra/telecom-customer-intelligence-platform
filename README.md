# telecom-customer-intelligence-platform
End-to-end telecom Customer 360, churn, complaint intelligence, and retention analytics platform.

## Live application

The deployed Streamlit application is available here:

[Telecom Customer Intelligence Platform](https://telecom-customer-intelligence-platformbranchmain-eat8m2wbwfv9c.streamlit.app/)

## Streamlit application

The project includes a Streamlit app for customer intelligence, churn-risk review, and retention prioritization.

Run locally:

```bash
streamlit run app/Home.py
```

The app uses full local processed data when available. If generated local data is missing, it falls back to the committed demo dataset in data/demo/, so the deployed app can still run.

Main app entrypoint:
```text
app/Home.py
```
Deployment notes are available in:
```text
docs/deployment.md
```