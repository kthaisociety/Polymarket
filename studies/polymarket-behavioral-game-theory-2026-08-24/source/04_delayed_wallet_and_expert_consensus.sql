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
b1_with_delayed_price AS (
    SELECT v.*,
           dp.ts AS delayed_price_time,
           dp.price AS delayed_price
    FROM wallet_hour_votes AS v
    CROSS JOIN constants AS c
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
    ) AS dp ON true
),
b1_covered AS (
    SELECT *,
           canonical_direction * (outcome_zero_payout - delayed_price)
               AS delayed_settlement_edge,
           canonical_direction * (outcome_zero_payout - delayed_price)
               - (SELECT adverse_execution_hurdle FROM constants) AS net_edge
    FROM b1_with_delayed_price
    WHERE delayed_price IS NOT NULL
),
b1_coverage AS (
    SELECT skill_cohort,
           count(*) AS signal_count,
           count(*) FILTER (WHERE delayed_price IS NOT NULL) AS covered_signal_count,
           count(DISTINCT event_id) AS signal_event_count,
           count(DISTINCT event_id) FILTER (WHERE delayed_price IS NOT NULL)
               AS covered_event_count,
           avg((delayed_price IS NOT NULL)::int::numeric) AS coverage_share
    FROM b1_with_delayed_price
    GROUP BY skill_cohort
),
b1_market_results AS (
    SELECT skill_cohort,
           event_id,
           event_ordinal,
           event_count,
           market_id,
           count(*) AS signal_count,
           avg(net_edge) AS market_net_edge
    FROM b1_covered
    GROUP BY skill_cohort, event_id, event_ordinal, event_count, market_id
),
b1_event_results AS (
    SELECT skill_cohort,
           event_id,
           event_ordinal,
           event_count,
           sum(signal_count) AS signal_count,
           avg(market_net_edge) AS event_net_edge
    FROM b1_market_results
    GROUP BY skill_cohort, event_id, event_ordinal, event_count
),
b1_cohort_results AS (
    SELECT skill_cohort,
           sum(signal_count) AS covered_signal_count,
           count(*) AS event_count,
           avg(event_net_edge) AS event_macro_net_edge,
           avg(event_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_event_macro_net_edge,
           avg(event_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_event_macro_net_edge,
           avg((event_net_edge > 0)::int::numeric) AS positive_event_share
    FROM b1_event_results
    GROUP BY skill_cohort
),
b1_paired_events AS (
    SELECT high.event_id,
           high.event_ordinal,
           high.event_count,
           high.event_net_edge AS high_net_edge,
           rival.event_net_edge AS non_high_net_edge,
           high.event_net_edge - rival.event_net_edge AS high_minus_non_high_net_edge
    FROM b1_event_results AS high
    JOIN b1_event_results AS rival USING (event_id)
    WHERE high.skill_cohort = 'HIGH_SKILL'
      AND rival.skill_cohort = 'NON_HIGH'
),
b1_paired_result AS (
    SELECT count(*) AS paired_event_count,
           avg(high_minus_non_high_net_edge) AS high_minus_non_high_event_macro_net_edge,
           avg(high_minus_non_high_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_high_minus_non_high_net_edge,
           avg(high_minus_non_high_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_high_minus_non_high_net_edge
    FROM b1_paired_events
),
vote_groups AS (
    SELECT skill_cohort,
           market_id,
           event_id,
           event_ordinal,
           event_count,
           resolved_time,
           outcome_zero_payout,
           signal_hour,
           signal_hour + interval '1 hour' AS decision_time,
           count(*) AS wallet_count,
           count(*) FILTER (WHERE canonical_direction = 1) AS positive_wallet_count,
           count(*) FILTER (WHERE canonical_direction = -1) AS negative_wallet_count
    FROM wallet_hour_votes
    GROUP BY skill_cohort, market_id, event_id, event_ordinal, event_count,
             resolved_time, outcome_zero_payout, signal_hour
),
b2_signals AS (
    SELECT 'EXPERT_CONSENSUS' AS cohort,
           *,
           CASE WHEN positive_wallet_count > negative_wallet_count THEN 1 ELSE -1 END
               AS canonical_direction,
           greatest(positive_wallet_count, negative_wallet_count)::numeric / wallet_count
               AS agreement_share
    FROM vote_groups
    WHERE skill_cohort = 'HIGH_SKILL'
      AND wallet_count >= 2
      AND greatest(positive_wallet_count, negative_wallet_count)::numeric / wallet_count >= 0.75
      AND positive_wallet_count <> negative_wallet_count
    UNION ALL
    SELECT 'SINGLE_HIGH' AS cohort,
           *,
           CASE WHEN positive_wallet_count > negative_wallet_count THEN 1 ELSE -1 END,
           1::numeric AS agreement_share
    FROM vote_groups
    WHERE skill_cohort = 'HIGH_SKILL'
      AND wallet_count = 1
    UNION ALL
    SELECT 'NON_HIGH_CONSENSUS' AS cohort,
           *,
           CASE WHEN positive_wallet_count > negative_wallet_count THEN 1 ELSE -1 END,
           greatest(positive_wallet_count, negative_wallet_count)::numeric / wallet_count
               AS agreement_share
    FROM vote_groups
    WHERE skill_cohort = 'NON_HIGH'
      AND wallet_count >= 2
      AND greatest(positive_wallet_count, negative_wallet_count)::numeric / wallet_count >= 0.75
      AND positive_wallet_count <> negative_wallet_count
),
b2_with_delayed_price AS (
    SELECT s.*,
           dp.ts AS delayed_price_time,
           dp.price AS delayed_price
    FROM b2_signals AS s
    CROSS JOIN constants AS c
    LEFT JOIN LATERAL (
        SELECT p.ts,
               p.price
        FROM market.price_series AS p
        WHERE p.venue = 'polymarket'
          AND p.market_id = s.market_id
          AND p.outcome_index = 0
          AND p.fidelity = 60
          AND p.ts >= s.decision_time + interval '1 hour'
          AND p.ts <= s.decision_time + interval '2 hours'
          AND p.ts < s.resolved_time
          AND p.ts <= c.analysis_as_of
        ORDER BY p.ts
        LIMIT 1
    ) AS dp ON true
),
b2_covered AS (
    SELECT *,
           canonical_direction * (outcome_zero_payout - delayed_price)
               AS delayed_settlement_edge,
           canonical_direction * (outcome_zero_payout - delayed_price)
               - (SELECT adverse_execution_hurdle FROM constants) AS net_edge
    FROM b2_with_delayed_price
    WHERE delayed_price IS NOT NULL
),
b2_coverage AS (
    SELECT cohort,
           count(*) AS signal_count,
           count(*) FILTER (WHERE delayed_price IS NOT NULL) AS covered_signal_count,
           count(DISTINCT event_id) AS signal_event_count,
           count(DISTINCT event_id) FILTER (WHERE delayed_price IS NOT NULL)
               AS covered_event_count,
           avg((delayed_price IS NOT NULL)::int::numeric) AS coverage_share,
           avg(wallet_count) AS mean_wallet_count,
           avg(agreement_share) AS mean_agreement_share
    FROM b2_with_delayed_price
    GROUP BY cohort
),
b2_market_results AS (
    SELECT cohort,
           event_id,
           event_ordinal,
           event_count,
           market_id,
           count(*) AS signal_count,
           avg(net_edge) AS market_net_edge
    FROM b2_covered
    GROUP BY cohort, event_id, event_ordinal, event_count, market_id
),
b2_event_results AS (
    SELECT cohort,
           event_id,
           event_ordinal,
           event_count,
           sum(signal_count) AS signal_count,
           avg(market_net_edge) AS event_net_edge
    FROM b2_market_results
    GROUP BY cohort, event_id, event_ordinal, event_count
),
b2_cohort_results AS (
    SELECT cohort,
           sum(signal_count) AS covered_signal_count,
           count(*) AS event_count,
           avg(event_net_edge) AS event_macro_net_edge,
           avg(event_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_event_macro_net_edge,
           avg(event_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_event_macro_net_edge,
           avg((event_net_edge > 0)::int::numeric) AS positive_event_share
    FROM b2_event_results
    GROUP BY cohort
),
b2_paired_rivals AS (
    SELECT expert.event_id,
           expert.event_ordinal,
           expert.event_count,
           rival.cohort AS rival_cohort,
           expert.event_net_edge,
           rival.event_net_edge AS rival_event_net_edge,
           expert.event_net_edge - rival.event_net_edge AS expert_minus_rival_net_edge
    FROM b2_event_results AS expert
    JOIN b2_event_results AS rival USING (event_id)
    WHERE expert.cohort = 'EXPERT_CONSENSUS'
      AND rival.cohort IN ('SINGLE_HIGH', 'NON_HIGH_CONSENSUS')
),
b2_rival_results AS (
    SELECT rival_cohort,
           count(*) AS paired_event_count,
           avg(expert_minus_rival_net_edge) AS expert_minus_rival_event_macro_net_edge,
           avg(expert_minus_rival_net_edge) FILTER (
               WHERE event_ordinal * 10 <= event_count * 7
           ) AS early_expert_minus_rival_net_edge,
           avg(expert_minus_rival_net_edge) FILTER (
               WHERE event_ordinal * 10 > event_count * 7
           ) AS late_expert_minus_rival_net_edge
    FROM b2_paired_rivals
    GROUP BY rival_cohort
)
SELECT jsonb_build_object(
    'schema_version', 'polymarket-delayed-wallet-consensus/v1',
    'analysis_as_of', (SELECT analysis_as_of FROM constants),
    'adverse_execution_hurdle', (SELECT adverse_execution_hurdle FROM constants),
    'partition', (SELECT to_jsonb(partition_summary) FROM partition_summary),
    'b1_delayed', jsonb_build_object(
        'coverage', (SELECT jsonb_agg(to_jsonb(b1_coverage) ORDER BY skill_cohort) FROM b1_coverage),
        'cohorts', (SELECT jsonb_agg(to_jsonb(b1_cohort_results) ORDER BY skill_cohort) FROM b1_cohort_results),
        'paired_result', (SELECT to_jsonb(b1_paired_result) FROM b1_paired_result),
        'decision_rule', jsonb_build_object(
            'minimum_high_skill_events', 30,
            'minimum_high_skill_signals', 1000,
            'minimum_paired_event_macro_difference', 0.010,
            'high_skill_halves_must_be_positive', true
        )
    ),
    'b2_expert_consensus', jsonb_build_object(
        'coverage', (SELECT jsonb_agg(to_jsonb(b2_coverage) ORDER BY cohort) FROM b2_coverage),
        'cohorts', (SELECT jsonb_agg(to_jsonb(b2_cohort_results) ORDER BY cohort) FROM b2_cohort_results),
        'paired_rivals', (SELECT jsonb_agg(to_jsonb(b2_rival_results) ORDER BY rival_cohort) FROM b2_rival_results),
        'decision_rule', jsonb_build_object(
            'minimum_consensus_events', 30,
            'minimum_consensus_signals', 500,
            'minimum_paired_event_macro_advantage_over_each_rival', 0.010,
            'consensus_halves_must_be_positive', true,
            'minimum_wallet_count', 2,
            'minimum_agreement_share', 0.75
        )
    ),
    'warnings', jsonb_build_array(
        'Development selection evidence only; the final event block is excluded from label joins.',
        'Hourly sampled prices are delayed public-state proxies, not executable quotes.',
        'No missing delayed price falls back to the originating fill price.',
        'Binary token trades are mapped to one canonical outcome-zero vote per wallet and market hour.',
        'The fixed one-cent hurdle is an adverse-execution stress, not an estimated fee, spread, or impact model.',
        'The production database is mutable; the fixed as-of ceiling excludes later timestamps but not later backfills.'
    )
) AS result;
