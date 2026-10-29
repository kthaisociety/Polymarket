WITH
constants AS (
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
development_markets AS (
    SELECT rm.market_id,
           rm.event_id,
           pe.event_ordinal,
           pe.event_count,
           rm.resolved_time,
           r.payouts[1] AS outcome_zero_payout
    FROM resolved_metadata AS rm
    JOIN partitioned_events AS pe USING (event_id)
    JOIN market.resolutions AS r
      ON r.venue = 'polymarket' AND r.market_id = rm.market_id
    WHERE pe.partition = 'DEVELOPMENT'
      AND NOT EXISTS (
          SELECT 1
          FROM ops.scope_repairs AS sr
          WHERE sr.venue = 'polymarket'
            AND sr.market_id = rm.market_id
            AND sr.state = 'pending'
      )
),
development_fills AS (
    SELECT f.account,
           f.market_id,
           f.fill_time,
           f.fill_uid,
           dm.event_id,
           dm.event_ordinal,
           dm.event_count,
           dm.resolved_time,
           dm.outcome_zero_payout,
           date_trunc('hour', f.fill_time) AS signal_hour,
           CASE
               WHEN (f.outcome_index = 0 AND f.side = 'BUY')
                 OR (f.outcome_index = 1 AND f.side = 'SELL') THEN 1
               ELSE -1
           END AS canonical_direction
    FROM market.fills AS f
    JOIN development_markets AS dm USING (market_id)
    CROSS JOIN partition_summary AS ps
    CROSS JOIN constants AS c
    WHERE f.venue = 'polymarket'
      AND f.fill_time > ps.training_cutoff
      AND f.fill_time <= c.analysis_as_of
      AND f.fill_time < dm.resolved_time
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
           fill_time AS final_vote_time,
           canonical_direction
    FROM development_fills
    ORDER BY account, market_id, signal_hour, fill_time DESC, fill_uid DESC
),
vote_groups AS (
    SELECT market_id,
           event_id,
           event_ordinal,
           event_count,
           resolved_time,
           outcome_zero_payout,
           signal_hour,
           signal_hour + interval '1 hour' AS decision_time,
           max(final_vote_time) AS final_vote_time,
           count(*) AS wallet_count,
           count(*) FILTER (WHERE canonical_direction = 1) AS positive_wallet_count,
           count(*) FILTER (WHERE canonical_direction = -1) AS negative_wallet_count,
           CASE
               WHEN count(*) FILTER (WHERE canonical_direction = 1)
                  > count(*) FILTER (WHERE canonical_direction = -1) THEN 1
               ELSE -1
           END AS consensus_direction,
           greatest(
               count(*) FILTER (WHERE canonical_direction = 1),
               count(*) FILTER (WHERE canonical_direction = -1)
           )::numeric / count(*) AS agreement_share
    FROM wallet_hour_votes
    GROUP BY market_id, event_id, event_ordinal, event_count, resolved_time,
             outcome_zero_payout, signal_hour
    HAVING count(*) FILTER (WHERE canonical_direction = 1)
        <> count(*) FILTER (WHERE canonical_direction = -1)
),
groups_with_state AS (
    SELECT g.*,
           current_mark.ts AS decision_price_time,
           current_mark.price AS decision_price,
           prior_mark.ts AS prior_price_time,
           prior_mark.price AS prior_price,
           entry_mark.ts AS entry_price_time,
           entry_mark.price AS entry_price
    FROM vote_groups AS g
    CROSS JOIN constants AS c
    LEFT JOIN LATERAL (
        SELECT p.ts, p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = g.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= g.decision_time - interval '2 hours'
          AND p.ts <= g.decision_time
          AND p.ts < g.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts DESC
        LIMIT 1
    ) AS current_mark ON true
    LEFT JOIN LATERAL (
        SELECT p.ts, p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = g.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= g.decision_time - interval '8 hours'
          AND p.ts <= g.decision_time - interval '6 hours'
          AND p.ts < g.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts DESC
        LIMIT 1
    ) AS prior_mark ON true
    LEFT JOIN LATERAL (
        SELECT p.ts, p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = g.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= g.decision_time + interval '1 hour'
          AND p.ts <= g.decision_time + interval '2 hours'
          AND p.ts < g.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts
        LIMIT 1
    ) AS entry_mark ON true
),
classified AS (
    SELECT *,
           decision_price - prior_price AS prior_move,
           CASE
               WHEN wallet_count >= 5
                AND agreement_share >= 0.75
                AND consensus_direction * (decision_price - prior_price) >= 0.05
                   THEN 'CROWDED_CHASE'
               WHEN wallet_count >= 5
                AND agreement_share >= 0.75
                AND abs(decision_price - prior_price) < 0.02
                   THEN 'CROWDED_FLAT'
               WHEN wallet_count BETWEEN 1 AND 2
                AND agreement_share = 1
                AND consensus_direction * (decision_price - prior_price) >= 0.05
                   THEN 'THIN_CHASE'
           END AS cohort
    FROM groups_with_state
    WHERE decision_price IS NOT NULL
      AND prior_price IS NOT NULL
),
daily_signals AS (
    SELECT DISTINCT ON (cohort, market_id, signal_hour::date)
           cohort,
           market_id,
           event_id,
           event_ordinal,
           event_count,
           resolved_time,
           outcome_zero_payout,
           signal_hour,
           decision_time,
           wallet_count,
           agreement_share,
           consensus_direction,
           prior_move,
           entry_price_time,
           entry_price
    FROM classified
    WHERE cohort IS NOT NULL
    ORDER BY cohort, market_id, signal_hour::date, signal_hour
),
signals_with_exits AS (
    SELECT s.*,
           exit_6h.ts AS exit_6h_time,
           exit_6h.price AS exit_6h_price,
           exit_24h.ts AS exit_24h_time,
           exit_24h.price AS exit_24h_price
    FROM daily_signals AS s
    CROSS JOIN constants AS c
    LEFT JOIN LATERAL (
        SELECT p.ts, p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = s.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= s.entry_price_time + interval '6 hours'
          AND p.ts <= s.entry_price_time + interval '8 hours'
          AND p.ts < s.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts
        LIMIT 1
    ) AS exit_6h ON true
    LEFT JOIN LATERAL (
        SELECT p.ts, p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = s.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= s.entry_price_time + interval '24 hours'
          AND p.ts <= s.entry_price_time + interval '28 hours'
          AND p.ts < s.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts
        LIMIT 1
    ) AS exit_24h ON true
),
evaluated AS (
    SELECT *,
           -consensus_direction * (outcome_zero_payout - entry_price)
               - (SELECT adverse_execution_hurdle FROM constants) AS settlement_net_edge,
           -consensus_direction * (exit_6h_price - entry_price) AS fade_return_6h,
           -consensus_direction * (exit_24h_price - entry_price) AS fade_return_24h,
           floor(entry_price * 20)::int AS entry_price_band,
           CASE
               WHEN resolved_time - entry_price_time <= interval '24 hours' THEN 'LE_24H'
               WHEN resolved_time - entry_price_time <= interval '72 hours' THEN '24_72H'
               WHEN resolved_time - entry_price_time <= interval '168 hours' THEN '72_168H'
               ELSE 'GT_168H'
           END AS resolution_horizon
    FROM signals_with_exits
    WHERE entry_price IS NOT NULL
),
coverage AS (
    SELECT cohort,
           count(*) AS covered_signal_count,
           count(DISTINCT event_id) AS covered_event_count,
           count(*) FILTER (WHERE exit_6h_price IS NOT NULL) AS exit_6h_count,
           count(*) FILTER (WHERE exit_24h_price IS NOT NULL) AS exit_24h_count,
           avg(wallet_count) AS mean_wallet_count,
           avg(agreement_share) AS mean_agreement_share,
           avg(abs(prior_move)) AS mean_absolute_prior_move
    FROM evaluated
    GROUP BY cohort
),
market_results AS (
    SELECT cohort,
           event_id,
           event_ordinal,
           event_count,
           market_id,
           count(*) AS signal_count,
           avg(settlement_net_edge) AS market_settlement_net_edge,
           avg(fade_return_6h) AS market_fade_return_6h,
           avg(fade_return_24h) AS market_fade_return_24h
    FROM evaluated
    GROUP BY cohort, event_id, event_ordinal, event_count, market_id
),
event_results AS (
    SELECT cohort,
           event_id,
           event_ordinal,
           event_count,
           sum(signal_count) AS signal_count,
           avg(market_settlement_net_edge) AS event_settlement_net_edge,
           avg(market_fade_return_6h) AS event_fade_return_6h,
           avg(market_fade_return_24h) AS event_fade_return_24h
    FROM market_results
    GROUP BY cohort, event_id, event_ordinal, event_count
),
cohort_results AS (
    SELECT cohort,
           sum(signal_count) AS covered_signal_count,
           count(*) AS event_count,
           avg(event_settlement_net_edge) AS event_macro_settlement_net_edge,
           avg(event_fade_return_6h) AS event_macro_fade_return_6h,
           avg(event_fade_return_24h) AS event_macro_fade_return_24h,
           avg(event_settlement_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_event_macro_settlement_net_edge,
           avg(event_settlement_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_event_macro_settlement_net_edge,
           avg((event_settlement_net_edge > 0)::int::numeric) AS positive_event_share
    FROM event_results
    GROUP BY cohort
),
cell_results AS (
    SELECT event_id,
           min(event_ordinal) AS event_ordinal,
           min(event_count) AS event_count,
           consensus_direction,
           entry_price_band,
           resolution_horizon,
           count(*) FILTER (WHERE cohort = 'CROWDED_CHASE') AS candidate_count,
           avg(settlement_net_edge) FILTER (WHERE cohort = 'CROWDED_CHASE')
               AS candidate_net_edge,
           count(*) FILTER (WHERE cohort = 'THIN_CHASE') AS thin_count,
           avg(settlement_net_edge) FILTER (WHERE cohort = 'THIN_CHASE') AS thin_net_edge,
           count(*) FILTER (WHERE cohort = 'CROWDED_FLAT') AS flat_count,
           avg(settlement_net_edge) FILTER (WHERE cohort = 'CROWDED_FLAT') AS flat_net_edge
    FROM evaluated
    GROUP BY event_id, consensus_direction, entry_price_band, resolution_horizon
),
matched_cells AS (
    SELECT 'THIN_CHASE' AS rival,
           event_id,
           event_ordinal,
           event_count,
           candidate_net_edge - thin_net_edge AS candidate_minus_rival_net_edge
    FROM cell_results
    WHERE candidate_count >= 2 AND thin_count >= 2
    UNION ALL
    SELECT 'CROWDED_FLAT',
           event_id,
           event_ordinal,
           event_count,
           candidate_net_edge - flat_net_edge
    FROM cell_results
    WHERE candidate_count >= 2 AND flat_count >= 2
),
paired_events AS (
    SELECT rival,
           event_id,
           min(event_ordinal) AS event_ordinal,
           min(event_count) AS event_count,
           count(*) AS matched_cell_count,
           avg(candidate_minus_rival_net_edge) AS event_candidate_minus_rival_net_edge
    FROM matched_cells
    GROUP BY rival, event_id
),
paired_results AS (
    SELECT rival,
           count(*) AS paired_event_count,
           sum(matched_cell_count) AS matched_cell_count,
           avg(event_candidate_minus_rival_net_edge)
               AS candidate_minus_rival_event_macro_net_edge,
           avg(event_candidate_minus_rival_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_candidate_minus_rival_net_edge,
           avg(event_candidate_minus_rival_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_candidate_minus_rival_net_edge
    FROM paired_events
    GROUP BY rival
),
decision_checks AS (
    SELECT coalesce(c.covered_signal_count >= 300 AND c.event_count >= 30, false)
               AS coverage_passed,
           coalesce(c.event_macro_fade_return_6h > 0
                    AND c.event_macro_fade_return_24h > 0, false) AS path_reversal_passed,
           coalesce(c.early_event_macro_settlement_net_edge > 0
                    AND c.late_event_macro_settlement_net_edge > 0, false)
               AS chronology_passed,
           coalesce(count(*) FILTER (
               WHERE p.paired_event_count >= 20
                 AND p.matched_cell_count >= 40
                 AND p.candidate_minus_rival_event_macro_net_edge >= 0.010
           ) = 2, false) AS both_rivals_passed
    FROM cohort_results AS c
    LEFT JOIN paired_results AS p ON true
    WHERE c.cohort = 'CROWDED_CHASE'
    GROUP BY c.covered_signal_count, c.event_count, c.event_macro_fade_return_6h,
             c.event_macro_fade_return_24h, c.early_event_macro_settlement_net_edge,
             c.late_event_macro_settlement_net_edge
)
SELECT jsonb_build_object(
    'schema_version', 'polymarket-crowded-extrapolation/v1',
    'analysis_as_of', (SELECT analysis_as_of FROM constants),
    'adverse_execution_hurdle', (SELECT adverse_execution_hurdle FROM constants),
    'partition', (SELECT to_jsonb(partition_summary) FROM partition_summary),
    'pending_repair_markets_excluded', true,
    'coverage', (SELECT jsonb_agg(to_jsonb(coverage) ORDER BY cohort) FROM coverage),
    'cohorts', (SELECT jsonb_agg(to_jsonb(cohort_results) ORDER BY cohort) FROM cohort_results),
    'paired_rivals', (SELECT jsonb_agg(to_jsonb(paired_results) ORDER BY rival) FROM paired_results),
    'decision_checks', (SELECT to_jsonb(decision_checks) FROM decision_checks),
    'decision', CASE
        WHEN (SELECT coverage_passed AND path_reversal_passed
                     AND chronology_passed AND both_rivals_passed
              FROM decision_checks)
        THEN 'SURVIVES_DEVELOPMENT_REQUIRES_FRESH_REPLICATION'
        ELSE 'REJECT_FIXED_CROWDED_EXTRAPOLATION_CANDIDATE'
    END,
    'fixed_rules', jsonb_build_object(
        'crowd_min_wallets', 5,
        'crowd_min_agreement', 0.75,
        'thin_max_wallets', 2,
        'chase_min_move', 0.05,
        'flat_max_absolute_move', 0.02,
        'entry_delay_hours', jsonb_build_array(1, 2),
        'daily_signal_cap', 1,
        'minimum_candidate_signals', 300,
        'minimum_candidate_events', 30,
        'minimum_paired_events_per_rival', 20,
        'minimum_matched_cells_per_rival', 40,
        'minimum_rival_advantage', 0.010
    ),
    'warnings', jsonb_build_array(
        'Development selection evidence only; embargo event payouts are not joined.',
        'Hourly sampled prices are public-state proxies, not executable quotes.',
        'No missing mark falls back to a fill price or a sample outside its fixed window.',
        'Known pending-repair markets are excluded; the mutable database can still receive later backfills.',
        'The taker aggregate-leg predicate and one-wallet-per-market-hour collapse prevent party-leg and intrahour vote inflation.',
        'A component-rival failure means the behavioral interaction adds no proved value over time-series state or crowd breadth alone.'
    )
) AS result;
