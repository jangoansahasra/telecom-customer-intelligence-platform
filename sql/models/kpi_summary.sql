-- Executive KPI summary view.

create or replace view telecom.kpi_summary as
select
    count(*) as customer_count,
    sum(case when churned then 1 else 0 end) as churned_customer_count,
    round(
        sum(case when churned then 1 else 0 end)::numeric / nullif(count(*), 0),
        4
    ) as customer_churn_rate,
    sum(total_mrr) as total_mrr,
    avg(total_mrr) as arpu,
    sum(monthly_revenue_at_risk) as monthly_revenue_at_risk,
    sum(case when byod_device_count > 0 then 1 else 0 end) as byod_customer_count,
    round(
        sum(case when byod_device_count > 0 then 1 else 0 end)::numeric / nullif(count(*), 0),
        4
    ) as byod_adoption_rate,
    sum(support_ticket_count) as support_ticket_count,
    sum(network_incident_count) as network_incident_count,
    sum(retention_offer_count) as retention_offer_count,
    sum(accepted_offer_count) as accepted_offer_count
from telecom.customer_360;