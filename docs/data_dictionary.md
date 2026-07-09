> Status: Initial design. Field definitions may change after source-data profiling and implementation.

# Data Dictionary

## Conventions

- Identifiers use `VARCHAR` values such as `CUS-000001`.
- Monetary values use `NUMERIC(12,2)`.
- Rates and probabilities use values from `0.0` to `1.0`.
- Timestamps are stored in UTC.
- Synthetic tables include `is_synthetic = TRUE`.
- `created_at` records when a row was generated or loaded.

## customers

One row per customer.

| Column | Type | Required | Description |
|---|---|---:|---|
| customer_id | VARCHAR(20) | Yes | Unique customer identifier |
| gender | VARCHAR(20) | No | Customer gender from source data |
| senior_citizen | BOOLEAN | Yes | Whether the customer is a senior citizen |
| has_partner | BOOLEAN | Yes | Whether the customer has a partner |
| has_dependents | BOOLEAN | Yes | Whether the customer has dependents |
| tenure_months | INTEGER | Yes | Months since the customer joined |
| contract_type | VARCHAR(30) | Yes | Month-to-month, one-year, or two-year |
| paperless_billing | BOOLEAN | Yes | Whether paperless billing is enabled |
| preferred_payment_method | VARCHAR(50) | No | Customer’s usual payment method |
| monthly_charges | NUMERIC(12,2) | Yes | Current monthly recurring charge |
| total_charges | NUMERIC(12,2) | No | Historical charges from the source dataset |
| churned | BOOLEAN | Yes | Source churn outcome |
| churn_date | DATE | No | Synthetic cancellation date when applicable |
| source_system | VARCHAR(50) | Yes | Origin of the customer record |
| is_synthetic | BOOLEAN | Yes | Whether the record was generated |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## subscriptions

One row per mobile or fixed broadband subscription.

| Column | Type | Required | Description |
|---|---|---:|---|
| subscription_id | VARCHAR(20) | Yes | Unique subscription identifier |
| customer_id | VARCHAR(20) | Yes | Owning customer |
| service_type | VARCHAR(30) | Yes | `mobile` or `fixed_broadband` |
| plan_name | VARCHAR(100) | Yes | Commercial plan name |
| plan_tier | VARCHAR(30) | Yes | Basic, standard, premium, or unlimited |
| start_date | DATE | Yes | Service activation date |
| end_date | DATE | No | Service termination date |
| status | VARCHAR(20) | Yes | Active, suspended, or cancelled |
| monthly_price | NUMERIC(12,2) | Yes | Recurring plan price |
| download_speed_mbps | INTEGER | No | Fixed broadband download speed |
| data_allowance_gb | NUMERIC(10,2) | No | Mobile monthly data allowance |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## devices

One row per device attached to a subscription.

| Column | Type | Required | Description |
|---|---|---:|---|
| device_id | VARCHAR(20) | Yes | Unique device identifier |
| subscription_id | VARCHAR(20) | Yes | Associated subscription |
| device_type | VARCHAR(30) | Yes | Smartphone, router, modem, or hotspot |
| manufacturer | VARCHAR(50) | No | Device manufacturer |
| model_name | VARCHAR(100) | No | Device model |
| operating_system | VARCHAR(50) | No | Device operating system |
| is_byod | BOOLEAN | Yes | Whether the customer supplied the device |
| activation_date | DATE | Yes | Date registered on the network |
| device_age_months | INTEGER | Yes | Device age at the latest observation |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## monthly_usage

One row per subscription per calendar month.

| Column | Type | Required | Description |
|---|---|---:|---|
| usage_id | VARCHAR(30) | Yes | Unique usage record |
| subscription_id | VARCHAR(20) | Yes | Associated subscription |
| snapshot_month | DATE | Yes | First day of the usage month |
| data_used_gb | NUMERIC(12,2) | Yes | Data consumed in gigabytes |
| voice_minutes | INTEGER | Yes | Mobile voice minutes |
| sms_count | INTEGER | Yes | Mobile SMS messages |
| peak_download_mbps | NUMERIC(10,2) | No | Measured fixed-service peak speed |
| overage_charges | NUMERIC(12,2) | Yes | Charges beyond plan allowance |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## invoices

One row per customer invoice.

| Column | Type | Required | Description |
|---|---|---:|---|
| invoice_id | VARCHAR(20) | Yes | Unique invoice identifier |
| customer_id | VARCHAR(20) | Yes | Billed customer |
| billing_month | DATE | Yes | First day of billing month |
| invoice_date | DATE | Yes | Invoice issue date |
| due_date | DATE | Yes | Payment due date |
| recurring_amount | NUMERIC(12,2) | Yes | Subscription charges |
| usage_amount | NUMERIC(12,2) | Yes | Variable usage charges |
| discount_amount | NUMERIC(12,2) | Yes | Discounts applied |
| tax_amount | NUMERIC(12,2) | Yes | Taxes charged |
| total_amount | NUMERIC(12,2) | Yes | Final invoice amount |
| balance_due | NUMERIC(12,2) | Yes | Outstanding balance |
| invoice_status | VARCHAR(20) | Yes | Open, paid, overdue, or written-off |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## payments

One row per payment attempt.

| Column | Type | Required | Description |
|---|---|---:|---|
| payment_id | VARCHAR(20) | Yes | Unique payment identifier |
| invoice_id | VARCHAR(20) | Yes | Related invoice |
| customer_id | VARCHAR(20) | Yes | Paying customer |
| payment_date | DATE | No | Successful or attempted payment date |
| payment_method | VARCHAR(50) | Yes | Card, bank transfer, check, or electronic check |
| amount_paid | NUMERIC(12,2) | Yes | Amount successfully collected |
| payment_status | VARCHAR(20) | Yes | Successful, failed, pending, or refunded |
| days_late | INTEGER | Yes | Days after due date; zero when on time |
| is_autopay | BOOLEAN | Yes | Whether automatic payment was used |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## network_incidents

One row per network incident.

| Column | Type | Required | Description |
|---|---|---:|---|
| incident_id | VARCHAR(20) | Yes | Unique incident identifier |
| service_type | VARCHAR(30) | Yes | Mobile or fixed broadband |
| incident_type | VARCHAR(50) | Yes | Outage, congestion, latency, or packet loss |
| region | VARCHAR(50) | Yes | Affected synthetic service region |
| started_at | TIMESTAMP | Yes | Incident start |
| resolved_at | TIMESTAMP | No | Incident resolution |
| duration_minutes | INTEGER | Yes | Total incident duration |
| severity | VARCHAR(20) | Yes | Low, medium, high, or critical |
| affected_customer_count | INTEGER | Yes | Number of affected customers |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## incident_impacts

One row per affected subscription per incident.

| Column | Type | Required | Description |
|---|---|---:|---|
| impact_id | VARCHAR(30) | Yes | Unique impact identifier |
| incident_id | VARCHAR(20) | Yes | Related incident |
| subscription_id | VARCHAR(20) | Yes | Affected subscription |
| impact_minutes | INTEGER | Yes | Customer-level impact duration |
| service_unavailable | BOOLEAN | Yes | Whether service was completely unavailable |
| compensation_amount | NUMERIC(12,2) | Yes | Customer credit issued |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## support_tickets

One row per customer support case.

| Column | Type | Required | Description |
|---|---|---:|---|
| ticket_id | VARCHAR(20) | Yes | Unique ticket identifier |
| customer_id | VARCHAR(20) | Yes | Customer opening the case |
| subscription_id | VARCHAR(20) | No | Related service when known |
| opened_at | TIMESTAMP | Yes | Ticket creation time |
| resolved_at | TIMESTAMP | No | Ticket resolution time |
| channel | VARCHAR(30) | Yes | Phone, chat, email, web, or store |
| ticket_text | TEXT | Yes | Synthetic complaint narrative |
| source_category | VARCHAR(50) | Yes | Generated complaint label |
| priority | VARCHAR(20) | Yes | Low, medium, high, or urgent |
| status | VARCHAR(20) | Yes | Open, pending, resolved, or closed |
| first_contact_resolution | BOOLEAN | Yes | Whether solved during first contact |
| satisfaction_score | INTEGER | No | Post-case score from 1 to 5 |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## complaint_predictions

One row per classified support ticket.

| Column | Type | Required | Description |
|---|---|---:|---|
| ticket_id | VARCHAR(20) | Yes | Classified support ticket |
| predicted_category | VARCHAR(50) | Yes | NLP-generated complaint category |
| category_confidence | NUMERIC(6,5) | Yes | Classification confidence |
| predicted_sentiment | VARCHAR(20) | No | Positive, neutral, or negative |
| sentiment_confidence | NUMERIC(6,5) | No | Sentiment confidence |
| model_name | VARCHAR(100) | Yes | NLP model identifier |
| model_version | VARCHAR(50) | Yes | Version of the deployed model |
| predicted_at | TIMESTAMP | Yes | Classification timestamp |

## retention_campaigns

One row per retention campaign.

| Column | Type | Required | Description |
|---|---|---:|---|
| campaign_id | VARCHAR(20) | Yes | Unique campaign identifier |
| campaign_name | VARCHAR(100) | Yes | Campaign name |
| offer_type | VARCHAR(50) | Yes | Discount, upgrade, credit, or contract incentive |
| offer_value | NUMERIC(12,2) | Yes | Monetary value of the offer |
| start_date | DATE | Yes | Campaign start |
| end_date | DATE | Yes | Campaign end |
| target_segment | VARCHAR(100) | Yes | Intended risk or customer segment |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## retention_contacts

One row per customer contacted by a campaign.

| Column | Type | Required | Description |
|---|---|---:|---|
| contact_id | VARCHAR(20) | Yes | Unique campaign-contact identifier |
| campaign_id | VARCHAR(20) | Yes | Associated campaign |
| customer_id | VARCHAR(20) | Yes | Contacted customer |
| contact_date | DATE | Yes | Contact date |
| channel | VARCHAR(30) | Yes | Email, SMS, phone, app, or store |
| offer_accepted | BOOLEAN | No | Whether the offer was accepted |
| response_date | DATE | No | Customer response date |
| retained_90_days | BOOLEAN | No | Whether customer remained after 90 days |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

## churn_snapshots

One row per customer per model observation date.

| Column | Type | Required | Description |
|---|---|---:|---|
| snapshot_id | VARCHAR(30) | Yes | Unique snapshot identifier |
| customer_id | VARCHAR(20) | Yes | Evaluated customer |
| observation_date | DATE | Yes | Date at which features become available |
| lookback_months | INTEGER | Yes | Historical feature window |
| label_window_days | INTEGER | Yes | Future churn-label window |
| churned_in_window | BOOLEAN | No | Actual future churn result |
| churn_probability | NUMERIC(6,5) | No | Model-estimated churn probability |
| risk_category | VARCHAR(20) | No | Low, medium, or high |
| monthly_revenue_at_risk | NUMERIC(12,2) | No | Current recurring revenue exposed |
| retention_priority | NUMERIC(12,4) | No | Customer retention ranking score |
| model_version | VARCHAR(50) | No | Churn model version |
| scored_at | TIMESTAMP | No | Prediction timestamp |
| is_synthetic | BOOLEAN | Yes | Synthetic-data indicator |
| created_at | TIMESTAMP | Yes | Record creation timestamp |