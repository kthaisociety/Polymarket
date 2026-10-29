WITH resolved_markets AS (
    SELECT m.market_id,
           m.event_id,
           r.resolved_time,
           r.payouts
    FROM market.markets AS m
    JOIN market.resolutions AS r USING (venue, market_id)
    WHERE m.venue = 'polymarket'
      AND m.market_type = 'binary'
      AND m.event_id IS NOT NULL
      AND cardinality(r.payouts) = 2
),
resolved_events AS (
    SELECT event_id,
           max(resolved_time) AS event_resolved_time
    FROM resolved_markets
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
training_wallet_market AS (
    SELECT f.account,
           f.market_id,
           avg(
               CASE f.side
                   WHEN 'BUY' THEN rm.payouts[f.outcome_index + 1] - f.price
                   ELSE f.price - rm.payouts[f.outcome_index + 1]
               END
           ) AS signed_settlement_edge
    FROM market.fills AS f
    JOIN resolved_markets AS rm USING (market_id)
    JOIN partitioned_events AS pe USING (event_id)
    WHERE f.venue = 'polymarket'
      AND pe.partition = 'TRAIN'
      AND f.fill_time < rm.resolved_time
      AND f.price BETWEEN 0.05 AND 0.95
      AND lower('0x' || right(f.raw->'topics'->>3, 40)) = lower(f.raw->>'address')
    GROUP BY f.account, f.market_id
),
wallet_skill AS (
    SELECT account,
           count(*) AS training_market_count,
           avg(signed_settlement_edge) AS unshrunk_edge,
           count(*)::numeric / (count(*) + 10) * avg(signed_settlement_edge)
               AS shrunk_edge
    FROM training_wallet_market
    GROUP BY account
),
development_fills AS (
    SELECT f.account,
           f.market_id,
           rm.event_id,
           pe.event_ordinal,
           pe.event_count,
           CASE f.side
               WHEN 'BUY' THEN rm.payouts[f.outcome_index + 1] - f.price
               ELSE f.price - rm.payouts[f.outcome_index + 1]
           END AS signed_settlement_edge,
           ws.training_market_count,
           ws.shrunk_edge
    FROM market.fills AS f
    JOIN resolved_markets AS rm USING (market_id)
    JOIN partitioned_events AS pe USING (event_id)
    CROSS JOIN partition_summary AS ps
    LEFT JOIN wallet_skill AS ws USING (account)
    WHERE f.venue = 'polymarket'
      AND pe.partition = 'DEVELOPMENT'
      AND f.fill_time > ps.training_cutoff
      AND f.fill_time < rm.resolved_time
      AND f.price BETWEEN 0.05 AND 0.95
      AND lower('0x' || right(f.raw->'topics'->>3, 40)) = lower(f.raw->>'address')
),
expanded_cohorts AS (
    SELECT development_fills.*, 'ALL' AS cohort
    FROM development_fills
    UNION ALL
    SELECT development_fills.*, 'ELIGIBLE_POSITIVE' AS cohort
    FROM development_fills
    WHERE training_market_count >= 5
      AND shrunk_edge > 0
    UNION ALL
    SELECT development_fills.*, 'HIGH_SKILL' AS cohort
    FROM development_fills
    WHERE training_market_count >= 5
      AND shrunk_edge >= 0.02
    UNION ALL
    SELECT development_fills.*, 'LOW_SKILL' AS cohort
    FROM development_fills
    WHERE training_market_count >= 5
      AND shrunk_edge <= -0.02
),
market_results AS (
    SELECT cohort,
           event_id,
           event_ordinal,
           event_count,
           market_id,
           count(*) AS fill_count,
           count(DISTINCT account) AS wallet_count,
           avg(signed_settlement_edge) AS fill_mean_edge
    FROM expanded_cohorts
    GROUP BY cohort, event_id, event_ordinal, event_count, market_id
),
event_results AS (
    SELECT cohort,
           event_id,
           event_ordinal,
           event_count,
           sum(fill_count) AS fill_count,
           sum(fill_count * fill_mean_edge) / sum(fill_count) AS fill_mean_edge,
           avg(fill_mean_edge) AS market_macro_edge
    FROM market_results
    GROUP BY cohort, event_id, event_ordinal, event_count
),
cohort_results AS (
    SELECT er.cohort,
           sum(er.fill_count) AS fill_count,
           (SELECT count(*) FROM market_results AS mr WHERE mr.cohort = er.cohort)
               AS market_count,
           count(*) AS event_count,
           sum(er.fill_count * er.fill_mean_edge) / sum(er.fill_count) AS fill_mean_edge,
           (SELECT avg(mr.fill_mean_edge)
            FROM market_results AS mr
            WHERE mr.cohort = er.cohort) AS market_macro_edge,
           avg(er.market_macro_edge) AS event_macro_edge,
           avg((er.market_macro_edge > 0)::int::numeric) AS positive_event_share,
           avg(er.market_macro_edge) FILTER (
               WHERE er.event_ordinal * 10 <= er.event_count * 7
           ) AS early_event_macro_edge,
           avg(er.market_macro_edge) FILTER (
               WHERE er.event_ordinal * 10 > er.event_count * 7
           ) AS late_event_macro_edge
    FROM event_results AS er
    GROUP BY er.cohort
),
skill_summary AS (
    SELECT count(*) AS wallet_count,
           count(*) FILTER (WHERE training_market_count >= 5) AS eligible_wallet_count,
           count(*) FILTER (
               WHERE training_market_count >= 5 AND shrunk_edge >= 0.02
           ) AS high_skill_wallet_count,
           count(*) FILTER (
               WHERE training_market_count >= 5 AND shrunk_edge <= -0.02
           ) AS low_skill_wallet_count
    FROM wallet_skill
)
SELECT jsonb_build_object(
    'schema_version', 'polymarket-fold-local-skilled-wallet/v1',
    'partition', (SELECT to_jsonb(partition_summary) FROM partition_summary),
    'skill_population', (SELECT to_jsonb(skill_summary) FROM skill_summary),
    'cohorts', (
        SELECT jsonb_agg(to_jsonb(cohort_results) ORDER BY cohort)
        FROM cohort_results
    ),
    'warnings', jsonb_build_array(
        'This is development evidence from recorded taker fill prices, not delayed executable entry.',
        'The final event block is excluded by the SQL source but is not a governed Chronos protected backtest.',
        'Wallet identity is the aggressive account on the on-chain aggregate taker leg.',
        'Signed settlement edge does not deduct fees, spread, latency, or market impact.',
        'Price state, topic specialization, and activity remain mandatory rivals.'
    )
) AS result;
