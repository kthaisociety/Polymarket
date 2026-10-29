WITH constants AS (
    SELECT timestamptz '2026-08-24 09:13:44.071211+00' AS analysis_as_of,
           numeric '0.010' AS adverse_execution_hurdle
),
resolved_metadata AS (
    SELECT m.market_id,
           m.event_id,
           r.resolved_time
    FROM market.markets AS m
    JOIN market.resolutions AS r USING (venue, market_id)
    CROSS JOIN constants AS c
    WHERE m.venue = 'polymarket'
      AND m.market_type = 'binary'
      AND m.event_id IS NOT NULL
      AND cardinality(r.payouts) = 2
      AND r.resolved_time <= c.analysis_as_of
),
resolved_events AS (
    SELECT event_id,
           max(resolved_time) AS event_resolved_time
    FROM resolved_metadata
    GROUP BY event_id
),
ordered_events AS (
    SELECT event_id,
           event_resolved_time,
           row_number() OVER (ORDER BY event_resolved_time, event_id) AS event_ordinal,
           count(*) OVER () AS event_count
    FROM resolved_events
),
partitioned_events AS (
    SELECT event_id,
           event_resolved_time,
           event_ordinal,
           event_count,
           CASE
               WHEN event_ordinal * 5 <= event_count * 3 THEN 'TRAIN'
               WHEN event_ordinal * 5 <= event_count * 4 THEN 'DEVELOPMENT'
               ELSE 'EMBARGO'
           END AS partition
    FROM ordered_events
),
partition_summary AS (
    SELECT count(*) FILTER (WHERE partition = 'TRAIN') AS training_event_count,
           count(*) FILTER (WHERE partition = 'DEVELOPMENT') AS development_event_count,
           count(*) FILTER (WHERE partition = 'EMBARGO') AS embargoed_event_count,
           max(event_resolved_time) FILTER (WHERE partition = 'TRAIN') AS training_cutoff
    FROM partitioned_events
),
labeled_train_development AS (
    SELECT rm.market_id,
           rm.event_id,
           rm.resolved_time,
           pe.event_ordinal,
           pe.event_count,
           pe.partition,
           r.payouts
    FROM resolved_metadata AS rm
    JOIN partitioned_events AS pe USING (event_id)
    JOIN market.resolutions AS r
      ON r.venue = 'polymarket'
     AND r.market_id = rm.market_id
    WHERE pe.partition IN ('TRAIN', 'DEVELOPMENT')
),
training_wallet_market AS (
    SELECT f.account,
           f.market_id,
           avg(
               CASE f.side
                   WHEN 'BUY' THEN lm.payouts[f.outcome_index + 1] - f.price
                   ELSE f.price - lm.payouts[f.outcome_index + 1]
               END
           ) AS signed_settlement_edge
    FROM market.fills AS f
    JOIN labeled_train_development AS lm USING (market_id)
    CROSS JOIN constants AS c
    WHERE f.venue = 'polymarket'
      AND lm.partition = 'TRAIN'
      AND f.fill_time <= c.analysis_as_of
      AND f.fill_time < lm.resolved_time
      AND f.price BETWEEN 0.05 AND 0.95
      AND lower('0x' || right(f.raw->'topics'->>3, 40)) = lower(f.raw->>'address')
    GROUP BY f.account, f.market_id
),
wallet_skill AS (
    SELECT account,
           count(*) AS training_market_count,
           count(*)::numeric / (count(*) + 10) * avg(signed_settlement_edge) AS shrunk_edge
    FROM training_wallet_market
    GROUP BY account
),
development_fills AS (
    SELECT f.account,
           f.market_id,
           f.fill_time,
           f.fill_uid,
           lm.event_id,
           lm.event_ordinal,
           lm.event_count,
           lm.resolved_time,
           lm.payouts[1] AS outcome_zero_payout,
           date_trunc('hour', f.fill_time) AS signal_hour,
           CASE
               WHEN (f.outcome_index = 0 AND f.side = 'BUY')
                 OR (f.outcome_index = 1 AND f.side = 'SELL') THEN 1
               ELSE -1
           END AS canonical_direction,
           CASE
               WHEN ws.training_market_count >= 5 AND ws.shrunk_edge >= 0.02
                   THEN 'HIGH_SKILL'
               ELSE 'NON_HIGH'
           END AS skill_cohort
    FROM market.fills AS f
    JOIN labeled_train_development AS lm USING (market_id)
    CROSS JOIN partition_summary AS ps
    CROSS JOIN constants AS c
    LEFT JOIN wallet_skill AS ws USING (account)
    WHERE f.venue = 'polymarket'
      AND lm.partition = 'DEVELOPMENT'
      AND f.fill_time > ps.training_cutoff
      AND f.fill_time <= c.analysis_as_of
      AND f.fill_time < lm.resolved_time
      AND f.price BETWEEN 0.05 AND 0.95
      AND lower('0x' || right(f.raw->'topics'->>3, 40)) = lower(f.raw->>'address')
),
wallet_hour_votes AS (
    SELECT DISTINCT ON (account, market_id, signal_hour)
           account,
           market_id,
           event_id,
           event_ordinal,
           event_count,
           resolved_time,
           outcome_zero_payout,
           signal_hour,
           fill_time AS signal_time,
           canonical_direction,
           skill_cohort
    FROM development_fills
    ORDER BY account, market_id, signal_hour, fill_time DESC, fill_uid DESC
),
market_hour_activity AS (
    SELECT market_id,
           signal_hour,
           count(*) AS distinct_wallet_count,
           CASE
               WHEN count(*) = 1 THEN 'ACTIVITY_1'
               WHEN count(*) <= 4 THEN 'ACTIVITY_2_4'
               WHEN count(*) <= 9 THEN 'ACTIVITY_5_9'
               ELSE 'ACTIVITY_10_PLUS'
           END AS activity_band
    FROM wallet_hour_votes
    GROUP BY market_id, signal_hour
),
signals_with_marks AS (
    SELECT v.*,
           a.distinct_wallet_count,
           a.activity_band,
           prior.ts AS prior_price_time,
           prior.price AS prior_price,
           delayed.ts AS delayed_price_time,
           delayed.price AS delayed_price
    FROM wallet_hour_votes AS v
    JOIN market_hour_activity AS a USING (market_id, signal_hour)
    CROSS JOIN constants AS c
    LEFT JOIN LATERAL (
        SELECT p.ts,
               p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = v.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= v.signal_time - interval '2 hours'
          AND p.ts <= v.signal_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts DESC
        LIMIT 1
    ) AS prior ON true
    LEFT JOIN LATERAL (
        SELECT p.ts,
               p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = v.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= v.signal_time + interval '1 hour'
          AND p.ts <= v.signal_time + interval '2 hours'
          AND p.ts < v.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts
        LIMIT 1
    ) AS delayed ON true
),
eligible_signals AS (
    SELECT *,
           floor(delayed_price * 20)::int AS delayed_price_band,
           CASE
               WHEN resolved_time - delayed_price_time <= interval '24 hours' THEN 'LE_24H'
               WHEN resolved_time - delayed_price_time <= interval '72 hours' THEN '24_72H'
               WHEN resolved_time - delayed_price_time <= interval '168 hours' THEN '72_168H'
               ELSE 'GT_168H'
           END AS resolution_horizon,
           CASE
               WHEN delayed_price - prior_price <= -0.02 THEN 'DOWN'
               WHEN delayed_price - prior_price >= 0.02 THEN 'UP'
               ELSE 'FLAT'
           END AS momentum_state,
           canonical_direction * (outcome_zero_payout - delayed_price)
               - (SELECT adverse_execution_hurdle FROM constants) AS net_edge
    FROM signals_with_marks
    WHERE prior_price IS NOT NULL
      AND delayed_price IS NOT NULL
),
coverage AS (
    SELECT skill_cohort,
           count(*) AS signal_count,
           count(*) FILTER (WHERE prior_price IS NOT NULL) AS prior_mark_count,
           count(*) FILTER (WHERE delayed_price IS NOT NULL) AS delayed_mark_count,
           count(*) FILTER (WHERE prior_price IS NOT NULL AND delayed_price IS NOT NULL)
               AS state_eligible_signal_count,
           count(DISTINCT event_id) FILTER (
               WHERE prior_price IS NOT NULL AND delayed_price IS NOT NULL
           ) AS state_eligible_event_count,
           avg((prior_price IS NOT NULL AND delayed_price IS NOT NULL)::int::numeric)
               AS state_coverage_share
    FROM signals_with_marks
    GROUP BY skill_cohort
),
cell_results AS (
    SELECT event_id,
           event_ordinal,
           event_count,
           canonical_direction,
           delayed_price_band,
           resolution_horizon,
           momentum_state,
           activity_band,
           count(*) FILTER (WHERE skill_cohort = 'HIGH_SKILL') AS high_signal_count,
           count(*) FILTER (WHERE skill_cohort = 'NON_HIGH') AS non_high_signal_count,
           avg(net_edge) FILTER (WHERE skill_cohort = 'HIGH_SKILL') AS high_net_edge,
           avg(net_edge) FILTER (WHERE skill_cohort = 'NON_HIGH') AS non_high_net_edge
    FROM eligible_signals
    GROUP BY event_id, event_ordinal, event_count, canonical_direction, delayed_price_band,
             resolution_horizon, momentum_state, activity_band
),
matched_cells AS (
    SELECT *,
           high_net_edge - non_high_net_edge AS high_minus_non_high_net_edge
    FROM cell_results
    WHERE high_signal_count >= 3
      AND non_high_signal_count >= 3
),
event_results AS (
    SELECT event_id,
           event_ordinal,
           event_count,
           count(*) AS matched_cell_count,
           sum(high_signal_count) AS high_signal_count,
           sum(non_high_signal_count) AS non_high_signal_count,
           avg(high_net_edge) AS high_cell_macro_net_edge,
           avg(non_high_net_edge) AS non_high_cell_macro_net_edge,
           avg(high_minus_non_high_net_edge) AS high_minus_non_high_net_edge
    FROM matched_cells
    GROUP BY event_id, event_ordinal, event_count
),
overall_result AS (
    SELECT count(*) AS matched_event_count,
           sum(matched_cell_count) AS matched_cell_count,
           sum(high_signal_count) AS high_signal_count,
           sum(non_high_signal_count) AS non_high_signal_count,
           avg(high_cell_macro_net_edge) AS high_event_macro_net_edge,
           avg(non_high_cell_macro_net_edge) AS non_high_event_macro_net_edge,
           avg(high_minus_non_high_net_edge) AS high_minus_non_high_event_macro_net_edge,
           avg(high_cell_macro_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_high_event_macro_net_edge,
           avg(high_cell_macro_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_high_event_macro_net_edge,
           avg(high_minus_non_high_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_high_minus_non_high_net_edge,
           avg(high_minus_non_high_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_high_minus_non_high_net_edge,
           avg((high_minus_non_high_net_edge > 0)::int::numeric) AS positive_event_share
    FROM event_results
)
SELECT jsonb_build_object(
    'schema_version', 'polymarket-delayed-wallet-state-activity-match/v1',
    'analysis_as_of', (SELECT analysis_as_of FROM constants),
    'adverse_execution_hurdle', (SELECT adverse_execution_hurdle FROM constants),
    'partition', (SELECT to_jsonb(partition_summary) FROM partition_summary),
    'coverage', (SELECT jsonb_agg(to_jsonb(coverage) ORDER BY skill_cohort) FROM coverage),
    'matched_result', (SELECT to_jsonb(overall_result) FROM overall_result),
    'decision_rule', jsonb_build_object(
        'minimum_events', 25,
        'minimum_cells', 75,
        'minimum_signals_per_cohort_per_cell', 3,
        'minimum_event_macro_difference', 0.010,
        'difference_halves_must_be_non_negative', true,
        'high_skill_halves_must_be_positive', true,
        'price_band_width', 0.05,
        'momentum_threshold', 0.02,
        'activity_bands', jsonb_build_array('1', '2-4', '5-9', '10+')
    ),
    'warnings', jsonb_build_array(
        'Development selection evidence only; the final event block is excluded from label joins.',
        'Matching controls event, direction, delayed price, resolution horizon, entry-time momentum, and wallet activity.',
        'Hourly prices are sampled public-state proxies, not executable quotes.',
        'The fixed one-cent hurdle is an adverse-execution stress rather than a complete cost model.',
        'The production database is mutable; the fixed as-of ceiling excludes later timestamps but not later backfills.'
    )
) AS result;
