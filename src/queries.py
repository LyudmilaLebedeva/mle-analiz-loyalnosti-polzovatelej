query = """
WITH set_config_precode AS (
    SELECT set_config('synchronize_seqscans', 'off', true)
)
SELECT
    user_id,
    device_type_canonical,
    order_id,
    created_dt_msk,
    created_ts_msk,
    currency_code,
    revenue,
    tickets_count,
    event_type_main,
    region_name,
    (p.created_dt_msk::date
        - LAG(p.created_dt_msk::date) OVER (
               PARTITION BY p.user_id
               ORDER BY p.created_ts_msk
        )
    ) AS days_since_prev
FROM afisha.purchases AS p
    INNER JOIN afisha.events USING (event_id)
    INNER JOIN afisha.city USING (city_id)
    INNER JOIN afisha.regions USING (region_id)
WHERE device_type_canonical IN ('mobile', 'desktop') AND event_type_main != 'фильм'
"""