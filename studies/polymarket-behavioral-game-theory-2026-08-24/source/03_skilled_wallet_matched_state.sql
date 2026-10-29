WITH constants AS (
    SELECT timestamptz '2026-08-24 09:13:44.071211+00' AS analysis_as_of
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
           lm.event_id,
           lm.event_ordinal,
           lm.event_count,
           f.side,
           f.price,
           floor(f.price * 20)::int AS price_band,
           CASE
               WHEN lm.resolved_time - f.fill_time <= interval '24 hours' THEN 'LE_24H'
               WHEN lm.resolved_time - f.fill_time <= interval '72 hours' THEN '24_72H'
               WHEN lm.resolved_time - f.fill_time <= interval '168 hours' THEN '72_168H'
               ELSE 'GT_168H'
           END AS resolution_horizon,
           CASE f.side
               WHEN 'BUY' THEN lm.payouts[f.outcome_index + 1] - f.price
               ELSE f.price - lm.payouts[f.outcome_index + 1]
           END AS signed_settlement_edge,
           CASE
               WHEN ws.training_market_count >= 5 AND ws.shrunk_edge >= 0.02
                   THEN 'HIGH_SKILL'
               ELSE 'NON_HIGH'
           END AS cohort
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
cell_results AS (
    SELECT event_id,
           event_ordinal,
           event_count,
           side,
           price_band,
           resolution_horizon,
           count(*) FILTER (WHERE cohort = 'HIGH_SKILL') AS high_fill_count,
           count(*) FILTER (WHERE cohort = 'NON_HIGH') AS non_high_fill_count,
           avg(signed_settlement_edge) FILTER (WHERE cohort = 'HIGH_SKILL') AS high_edge,
           avg(signed_settlement_edge) FILTER (WHERE cohort = 'NON_HIGH') AS non_high_edge
    FROM development_fills
    GROUP BY event_id, event_ordinal, event_count, side, price_band, resolution_horizon
),
matched_cells AS (
    SELECT *,
           high_edge - non_high_edge AS high_minus_non_high_edge
    FROM cell_results
    WHERE high_fill_count >= 5
      AND non_high_fill_count >= 5
),
event_results AS (
    SELECT event_id,
           event_ordinal,
           event_count,
           count(*) AS matched_cell_count,
           sum(high_fill_count) AS high_fill_count,
           sum(non_high_fill_count) AS non_high_fill_count,
           avg(high_edge) AS high_cell_macro_edge,
           avg(non_high_edge) AS non_high_cell_macro_edge,
           avg(high_minus_non_high_edge) AS high_minus_non_high_edge
    FROM matched_cells
    GROUP BY event_id, event_ordinal, event_count
),
overall_result AS (
    SELECT count(*) AS matched_event_count,
           sum(matched_cell_count) AS matched_cell_count,
           sum(high_fill_count) AS high_fill_count,
           sum(non_high_fill_count) AS non_high_fill_count,
           avg(high_cell_macro_edge) AS high_event_macro_edge,
           avg(non_high_cell_macro_edge) AS non_high_event_macro_edge,
           avg(high_minus_non_high_edge) AS high_minus_non_high_event_macro_edge,
           avg(high_minus_non_high_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_high_minus_non_high_edge,
           avg(high_minus_non_high_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_high_minus_non_high_edge,
           avg((high_minus_non_high_edge > 0)::int::numeric) AS positive_event_share
    FROM event_results
),
coverage AS (
    SELECT count(*) AS evaluation_fill_count,
           count(*) FILTER (WHERE cohort = 'HIGH_SKILL') AS high_skill_fill_count,
           count(DISTINCT event_id) AS evaluation_event_count,
           count(DISTINCT event_id) FILTER (WHERE cohort = 'HIGH_SKILL') AS high_skill_event_count,
           count(*) FILTER (WHERE cohort = 'HIGH_SKILL')::numeric
               / nullif(count(*), 0) AS high_skill_fill_share
    FROM development_fills
)
SELECT jsonb_build_object(
    'schema_version', 'polymarket-skilled-wallet-matched-state/v1',
    'analysis_as_of', (SELECT analysis_as_of FROM constants),
    'partition', (SELECT to_jsonb(partition_summary) FROM partition_summary),
    'coverage', (SELECT to_jsonb(coverage) FROM coverage),
    'matched_result', (SELECT to_jsonb(overall_result) FROM overall_result),
    'decision_rule', jsonb_build_object(
        'minimum_events', 30,
        'minimum_cells', 100,
        'minimum_event_macro_difference', 0.010,
        'chronological_halves_must_be_non_negative', true,
        'minimum_fills_per_cohort_per_cell', 5,
        'price_band_width', 0.05
    ),
    'warnings', jsonb_build_array(
        'Development selection evidence only; the final event block is excluded from label joins.',
        'Matching controls event, aggressor side, five-point fill-price band, and time to resolution.',
        'The matched-state test still uses recorded fill prices and is not an executable-entry test.',
        'The production database is mutable; the fixed as-of ceiling excludes later timestamps but not later backfills.'
    )
) AS result;
