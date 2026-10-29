WITH
constants AS (
    SELECT statement_timestamp() AS audited_at
),
clock_schema AS (
    SELECT EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_schema = 'market'
                 AND table_name = 'book_snapshots'
                 AND column_name = 'reference_time'
           ) AS snapshots_reference_time_column,
           EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_schema = 'market'
                 AND table_name = 'book_deltas'
                 AND column_name = 'reference_time'
           ) AS deltas_reference_time_column
),
event_inventory AS (
    SELECT m.event_id,
           count(*) AS database_market_count,
           count(*) FILTER (WHERE m.status = 'open') AS open_market_count,
           count(*) FILTER (
               WHERE coalesce((m.raw -> 'state' ->> 'neg_risk')::boolean, false)
           ) AS neg_risk_market_count,
           count(*) FILTER (
               WHERE coalesce((m.raw -> 'state' ->> 'accepting_orders')::boolean, false)
           ) AS accepting_market_count,
           count(*) FILTER (
               WHERE o.outcome_token IS NOT NULL AND lower(o.label) = 'yes'
           ) AS mapped_yes_leg_count,
           count(*) FILTER (
               WHERE m.raw -> 'trading' ? 'fees_enabled'
                 AND m.raw -> 'trading' ? 'minimum_order_size'
                 AND m.raw -> 'trading' ? 'minimum_tick_size'
                 AND (
                     NOT coalesce(
                         (m.raw -> 'trading' ->> 'fees_enabled')::boolean, false
                     )
                     OR (
                         m.raw -> 'trading' -> 'fee_schedule' ? 'rate'
                         AND m.raw -> 'trading' -> 'fee_schedule' ? 'exponent'
                     )
                 )
           ) AS cost_metadata_count,
           array_agg(m.market_id ORDER BY m.market_id) AS market_ids
    FROM market.markets AS m
    LEFT JOIN market.market_outcomes AS o
      ON o.venue = m.venue
     AND o.market_id = m.market_id
     AND o.outcome_index = 0
    WHERE m.venue = 'polymarket'
      AND m.event_id IS NOT NULL
    GROUP BY m.event_id
),
semantic_candidates AS (
    SELECT *
    FROM event_inventory
    WHERE database_market_count >= 3
      AND open_market_count = database_market_count
      AND neg_risk_market_count = database_market_count
      AND accepting_market_count = database_market_count
      AND mapped_yes_leg_count = database_market_count
      AND cost_metadata_count = database_market_count
),
current_top_coverage AS (
    SELECT sc.event_id,
           sc.database_market_count AS total_yes_legs,
           count(t.market_id) AS current_top_yes_legs,
           min(t.ts) AS stalest_current_top_at,
           max(t.ts) AS newest_current_top_at,
           sc.market_ids,
           count(t.market_id) = sc.database_market_count AS full_current_top_coverage
    FROM semantic_candidates AS sc
    LEFT JOIN market.book_tops AS t
      ON t.venue = 'polymarket'
     AND t.outcome_index = 0
     AND t.market_id = ANY(sc.market_ids)
     AND t.bid IS NOT NULL
     AND t.ask IS NOT NULL
    GROUP BY sc.event_id, sc.database_market_count, sc.market_ids
),
summary AS (
    SELECT count(*) AS database_event_count,
           count(*) FILTER (
               WHERE database_market_count >= 3
                 AND neg_risk_market_count = database_market_count
           ) AS observed_negrisk_event_count,
           (SELECT count(*) FROM semantic_candidates) AS semantic_candidate_count,
           (SELECT count(*) FROM current_top_coverage WHERE full_current_top_coverage)
               AS full_current_top_event_count,
           (SELECT count(*) FROM market.book_tops
             WHERE venue = 'polymarket' AND bid IS NOT NULL AND ask IS NOT NULL)
               AS current_two_sided_top_leg_count,
           (SELECT max(ts) FROM market.book_tops WHERE venue = 'polymarket')
               AS newest_top_at
    FROM event_inventory
),
top_candidates AS (
    SELECT jsonb_agg(to_jsonb(ranked) ORDER BY full_current_top_coverage DESC,
                                              current_top_yes_legs DESC,
                                              total_yes_legs,
                                              event_id) AS rows
    FROM (
        SELECT event_id,
               total_yes_legs,
               current_top_yes_legs,
               stalest_current_top_at,
               newest_current_top_at,
               full_current_top_coverage,
               market_ids
        FROM current_top_coverage
        ORDER BY full_current_top_coverage DESC,
                 current_top_yes_legs DESC,
                 total_yes_legs,
                 event_id
        LIMIT 25
    ) AS ranked
)
SELECT jsonb_pretty(
    jsonb_build_object(
        'schema_version', 'polymarket-negrisk-coordination-readiness/v1',
        'audited_at', c.audited_at,
        'clock_schema', to_jsonb(cs),
        'summary', to_jsonb(s),
        'semantic_candidate_current_top_coverage', tc.rows,
        'decision', 'BLOCK_COMPLETE_SET_STRATEGY',
        'failed_gates', jsonb_build_array(
            'production market.book_snapshots lacks reference_time',
            'production market.book_deltas lacks reference_time',
            'no post-change dual-clock full-event history can be retained from this deployment'
        ),
        'deferred_because_clock_gate_failed', jsonb_build_array(
            'historical per-leg anchor and overlap scan',
            'exact Gamma event endpoint retention',
            'basket price, depth, fee, fill, and return calculation'
        ),
        'caveats', jsonb_build_array(
            'current book_tops coverage is descriptive collector state and not historical causal evidence',
            'market rows carry venue event_id and neg_risk flags but not retained event endpoint bytes proving exhaustive membership',
            'no price, size, fee amount, payout, question, or return value is emitted',
            'displayed state does not prove fills, atomicity, queue position, or failed-leg unwind cost'
        )
    )
)
FROM constants AS c
CROSS JOIN clock_schema AS cs
CROSS JOIN summary AS s
CROSS JOIN top_candidates AS tc;
