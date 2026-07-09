-- Customer 360 analytical view.
-- Combines source customer attributes with synthetic telecom domain summaries.

create or replace view telecom.customer_360 as
with fixed_summary as (
    select
        customer_id,
        count(*) as fixed_subscription_count,
        sum(monthly_recurring_revenue) as fixed_mrr,
        max(download_speed_mbps) as max_download_speed_mbps
    from telecom.fixed_subscriptions
    group by customer_id
),

mobile_summary as (
    select
        customer_id,
        count(*) as mobile_subscription_count,
        sum(line_count) as mobile_line_count,
        sum(monthly_recurring_revenue) as mobile_mrr,
        bool_or(is_5g_enabled) as has_5g
    from telecom.mobile_subscriptions
    group by customer_id
),

byod_summary as (
    select
        customer_id,
        count(*) as byod_device_count,
        avg(device_age_months) as avg_byod_device_age_months
    from telecom.byod_devices
    group by customer_id
),

usage_summary as (
    select
        customer_id,
        sum(data_gb) as total_data_gb,
        sum(voice_minutes) as total_voice_minutes,
        sum(sms_count) as total_sms_count
    from telecom.monthly_usage
    group by customer_id
),

billing_summary as (
    select
        customer_id,
        count(*) as invoice_count,
        sum(invoice_amount) as total_invoice_amount,
        sum(case when payment_status = 'late' then 1 else 0 end) as late_payment_count,
        avg(days_late) as avg_days_late
    from telecom.billing_history
    group by customer_id
),

network_summary as (
    select
        customer_id,
        count(*) as network_incident_count,
        sum(duration_minutes) as total_incident_minutes
    from telecom.network_incidents
    group by customer_id
),

support_summary as (
    select
        customer_id,
        count(*) as support_ticket_count,
        avg(resolution_hours) as avg_resolution_hours,
        sum(case when complaint_category_seed = 'cancellation_request' then 1 else 0 end)
            as cancellation_request_count
    from telecom.support_tickets
    group by customer_id
),

retention_summary as (
    select
        customer_id,
        count(*) as retention_offer_count,
        sum(case when accepted_offer then 1 else 0 end) as accepted_offer_count
    from telecom.retention_campaigns
    group by customer_id
)

select
    c.customer_id,
    c.gender,
    c.senior_citizen,
    c.has_partner,
    c.has_dependents,
    c.tenure_months,
    c.contract_type,
    c.internet_service,
    c.payment_method,
    c.monthly_charges,
    c.total_charges,
    c.churned,

    coalesce(fs.fixed_subscription_count, 0) as fixed_subscription_count,
    coalesce(fs.fixed_mrr, 0) as fixed_mrr,
    coalesce(fs.max_download_speed_mbps, 0) as max_download_speed_mbps,

    coalesce(ms.mobile_subscription_count, 0) as mobile_subscription_count,
    coalesce(ms.mobile_line_count, 0) as mobile_line_count,
    coalesce(ms.mobile_mrr, 0) as mobile_mrr,
    coalesce(ms.has_5g, false) as has_5g,

    coalesce(bs.byod_device_count, 0) as byod_device_count,
    bs.avg_byod_device_age_months,

    coalesce(us.total_data_gb, 0) as total_data_gb,
    coalesce(us.total_voice_minutes, 0) as total_voice_minutes,
    coalesce(us.total_sms_count, 0) as total_sms_count,

    coalesce(bis.invoice_count, 0) as invoice_count,
    coalesce(bis.total_invoice_amount, 0) as total_invoice_amount,
    coalesce(bis.late_payment_count, 0) as late_payment_count,
    bis.avg_days_late,

    coalesce(ns.network_incident_count, 0) as network_incident_count,
    coalesce(ns.total_incident_minutes, 0) as total_incident_minutes,

    coalesce(ss.support_ticket_count, 0) as support_ticket_count,
    ss.avg_resolution_hours,
    coalesce(ss.cancellation_request_count, 0) as cancellation_request_count,

    coalesce(rs.retention_offer_count, 0) as retention_offer_count,
    coalesce(rs.accepted_offer_count, 0) as accepted_offer_count,

    (
        coalesce(fs.fixed_mrr, 0)
        + coalesce(ms.mobile_mrr, 0)
    ) as total_mrr,

    case
        when c.churned then (
            coalesce(fs.fixed_mrr, 0)
            + coalesce(ms.mobile_mrr, 0)
        )
        else 0
    end as monthly_revenue_at_risk

from telecom.customers c
left join fixed_summary fs on c.customer_id = fs.customer_id
left join mobile_summary ms on c.customer_id = ms.customer_id
left join byod_summary bs on c.customer_id = bs.customer_id
left join usage_summary us on c.customer_id = us.customer_id
left join billing_summary bis on c.customer_id = bis.customer_id
left join network_summary ns on c.customer_id = ns.customer_id
left join support_summary ss on c.customer_id = ss.customer_id
left join retention_summary rs on c.customer_id = rs.customer_id;