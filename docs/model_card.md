# Model Card: Telecom Customer Churn Model

## Model overview

This project trains a churn classification model for a telecom B2C customer intelligence platform. The model estimates the probability that a customer is at risk of churn and supports retention prioritization.

The best-performing model in the current pipeline is selected by validation ROC AUC across:

- Logistic Regression
- Random Forest
- XGBoost

In the latest local run, XGBoost was selected as the best model.

## Intended use

The model is intended for portfolio/demo use cases such as:

- identifying customers with elevated churn risk
- estimating expected monthly revenue at risk
- prioritizing retention outreach
- explaining churn drivers using SHAP
- supporting customer intelligence dashboards

## Not intended use

This model should not be used for real customer decisions without:

- validation on genuine company data
- fairness and bias assessment
- monitoring for drift
- business approval of retention policies
- privacy, legal, and compliance review

## Data sources

The project uses the public IBM Telco Customer Churn dataset as the source foundation.

Synthetic extension tables are generated for:

- fixed broadband subscriptions
- mobile subscriptions
- BYOD devices
- monthly usage
- billing history
- network incidents
- support tickets
- retention campaigns

Synthetic records are clearly labeled and should not be presented as genuine company data.

## Target variable

The target variable is:

```text
churned
```
This is derived from the IBM Telco Customer Churn dataset.

## Feature groups
The model uses customer-level features from:

- customer demographics and account attributes
- contract and payment information
- fixed broadband subscription features
- mobile and BYOD features
- monthly usage summaries
- billing and late-payment behavior
- network incident summaries
- support-ticket behavior
- retention campaign summaries

## Leakage prevention
The feature monthly_revenue_at_risk is excluded from model training because it is derived using the churn label.
A unit test verifies that leakage-prone columns are excluded from the training feature matrix.

## Validation metrics
Latest local validation metrics for the selected model:
Metric	                 Value
ROC AUC	                0.9046
Average precision	    0.7821
Accuracy	            0.8446
Precision	            0.7370
Recall	                0.6444
F1	                    0.6876

## Explainability
SHAP is used to generate customer-level churn explanations.
The Streamlit Customer 360 page shows the top positive churn-risk factors for each customer.

## Limitations

- The dataset is a public sample dataset, not live telecom production data.
- Several domain tables are synthetic and generated for portfolio demonstration.
- Synthetic relationships may not fully represent real telecom customer behavior.
- Model performance may be optimistic compared with a real production environment.
- Complaint classifications are based on synthetic support-ticket text.
- Transformer complaint classification is precomputed and not run live in the deployed app.
- The model has not been evaluated for fairness across protected classes.

## Ethical considerations
Retention models can influence customer treatment. In a real business setting, model outputs should be reviewed for fairness, transparency, and customer impact. The model should support human decision-making, not fully automate customer treatment decisions.

## Deployment
The deployed Streamlit app uses committed demo data for public review. Full local generated data and model artifacts are not committed to the repository.
