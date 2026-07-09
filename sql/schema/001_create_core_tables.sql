-- Core PostgreSQL schema for the Telecom B2C Customer Intelligence Platform.
-- Real source foundation: IBM Telco Customer Churn sample.
-- Synthetic extension tables are clearly labeled with is_synthetic.

create schema if not exists telecom;

create table if not exists telecom.customers (
    customer_id text primary key,
    gender text not null,
    senior_citizen boolean not null,
    has_partner boolean not null,
    has_dependents boolean not null,
    tenure_months integer not null check (tenure_months >= 0),
    phone_service boolean not null,
    multiple_lines text not null,
    internet_service text not null,
    online_security text not null,
    online_backup text not null,
    device_protection text not null,
    tech_support text not null,
    streaming_tv text not null,
    streaming_movies text not null,
    contract_type text not null,
    paperless_billing boolean not null,
    payment_method text not null,
    monthly_charges numeric(10, 2) not null check (monthly_charges >= 0),
    total_charges numeric(12, 2) not null check (total_charges >= 0),
    churned boolean not null,
    source_system text not null,
    is_synthetic boolean not null default false
);

create table if not exists telecom.fixed_subscriptions (
    fixed_subscription_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    service_type text not null,
    plan_name text not null,
    download_speed_mbps integer not null check (download_speed_mbps >= 0),
    contract_type text not null,
    monthly_recurring_revenue numeric(10, 2) not null check (monthly_recurring_revenue >= 0),
    subscription_status text not null,
    is_synthetic boolean not null default true
);

create table if not exists telecom.mobile_subscriptions (
    mobile_subscription_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    service_type text not null,
    plan_name text not null,
    line_count integer not null check (line_count >= 1),
    is_5g_enabled boolean not null,
    monthly_recurring_revenue numeric(10, 2) not null check (monthly_recurring_revenue >= 0),
    subscription_status text not null,
    is_synthetic boolean not null default true
);

create table if not exists telecom.byod_devices (
    device_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    mobile_subscription_id text not null references telecom.mobile_subscriptions(mobile_subscription_id),
    device_ownership text not null,
    device_os text not null,
    device_age_months integer not null check (device_age_months >= 0),
    is_synthetic boolean not null default true
);

create table if not exists telecom.monthly_usage (
    usage_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    subscription_id text not null,
    service_type text not null,
    usage_month text not null,
    data_gb numeric(10, 2) not null check (data_gb >= 0),
    voice_minutes integer not null check (voice_minutes >= 0),
    sms_count integer not null check (sms_count >= 0),
    is_synthetic boolean not null default true
);

create table if not exists telecom.billing_history (
    invoice_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    billing_month text not null,
    invoice_amount numeric(10, 2) not null check (invoice_amount >= 0),
    payment_status text not null,
    days_late integer not null check (days_late >= 0),
    is_synthetic boolean not null default true
);

create table if not exists telecom.network_incidents (
    incident_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    incident_month text not null,
    incident_type text not null,
    duration_minutes integer not null check (duration_minutes >= 0),
    service_affected text not null,
    is_synthetic boolean not null default true
);

create table if not exists telecom.support_tickets (
    ticket_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    ticket_month text not null,
    complaint_category_seed text not null,
    ticket_text text not null,
    priority text not null,
    resolution_hours numeric(10, 2) not null check (resolution_hours >= 0),
    is_synthetic boolean not null default true
);

create table if not exists telecom.retention_campaigns (
    campaign_id text primary key,
    customer_id text not null references telecom.customers(customer_id),
    campaign_month text not null,
    offer_type text not null,
    offer_value numeric(10, 2) not null check (offer_value >= 0),
    accepted_offer boolean not null,
    is_synthetic boolean not null default true
);