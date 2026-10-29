WITH
constants AS (
    SELECT 33605403::bigint AS genesis_block,
           statement_timestamp() AS audited_at
),
cursors AS (
    SELECT jsonb_agg(
               jsonb_build_object(
                   'name', name,
                   'block', CASE WHEN cursor ? 'block' THEN (cursor ->> 'block')::bigint END,
                   'updated_at', updated_at
               ) ORDER BY name
           ) AS rows,
           max((cursor ->> 'block')::bigint)
               FILTER (WHERE name = 'pm-onchain-history') AS history_block
    FROM ops.ingest_cursors
    WHERE name IN ('pm-gamma-sync', 'pm-onchain-forward', 'pm-onchain-history')
),
repairs AS (
    SELECT count(*) AS total,
           count(*) FILTER (WHERE state = 'pending') AS pending,
           count(*) FILTER (
               WHERE state = 'done'
                 AND (covered_through IS NULL OR covered_through < to_block)
           ) AS incomplete_done,
           min(from_block) AS min_from_block,
           max(to_block) AS max_to_block,
           max(enqueued_at) AS latest_enqueued_at
    FROM ops.scope_repairs
    WHERE venue = 'polymarket'
),
privileges AS (
    SELECT jsonb_object_agg(qualified_name, can_select ORDER BY qualified_name) AS rows,
           bool_and(can_select) AS all_select
    FROM (
        SELECT qualified_name,
               has_table_privilege(current_user, qualified_name, 'SELECT') AS can_select
        FROM unnest(ARRAY[
            'ops.ingest_cursors', 'ops.scope_repairs',
            'internal.pm_order_fills', 'internal.pm_position_splits',
            'internal.pm_position_merges', 'internal.pm_redemptions',
            'market.fills', 'market.markets', 'market.market_outcomes', 'market.positions'
        ]) AS required(qualified_name)
    ) AS checks
),
existence AS (
    SELECT jsonb_build_object(
               'internal.pm_order_fills',
                   EXISTS (SELECT 1 FROM internal.pm_order_fills LIMIT 1),
               'internal.pm_position_splits',
                   EXISTS (SELECT 1 FROM internal.pm_position_splits LIMIT 1),
               'internal.pm_position_merges',
                   EXISTS (SELECT 1 FROM internal.pm_position_merges LIMIT 1),
               'internal.pm_redemptions',
                   EXISTS (SELECT 1 FROM internal.pm_redemptions LIMIT 1),
               'market.fills',
                   EXISTS (
                       SELECT 1 FROM market.fills WHERE venue = 'polymarket' LIMIT 1
                   ),
               'market.positions_diagnostic_only',
                   EXISTS (
                       SELECT 1 FROM market.positions WHERE venue = 'polymarket' LIMIT 1
                   )
           ) AS rows
),
gates AS (
    SELECT (c.history_block IS NOT NULL AND c.history_block <= k.genesis_block)
               AS history_complete,
           (r.pending = 0 AND r.incomplete_done = 0) AS repairs_complete,
           p.all_select AS privileges_complete,
           ((e.rows ->> 'internal.pm_order_fills')::boolean
            AND (e.rows ->> 'internal.pm_position_splits')::boolean
            AND (e.rows ->> 'internal.pm_position_merges')::boolean
            AND (e.rows ->> 'internal.pm_redemptions')::boolean
            AND (e.rows ->> 'market.fills')::boolean) AS required_nonempty
    FROM constants k
    CROSS JOIN cursors c
    CROSS JOIN repairs r
    CROSS JOIN privileges p
    CROSS JOIN existence e
)
SELECT jsonb_pretty(
    jsonb_build_object(
        'study', 'polymarket.disposition-data-sufficiency',
        'audit_stage', 'operational-history-gate',
        'audited_at', k.audited_at,
        'configured_genesis_block', k.genesis_block,
        'cursors', c.rows,
        'repairs', jsonb_build_object(
            'total', r.total, 'pending', r.pending, 'incomplete_done', r.incomplete_done,
            'min_from_block', r.min_from_block, 'max_to_block', r.max_to_block,
            'latest_enqueued_at', r.latest_enqueued_at
        ),
        'required_table_existence', e.rows,
        'select_privileges', p.rows,
        'gates', to_jsonb(g),
        'decision', CASE
            WHEN g.history_complete AND g.repairs_complete
             AND g.privileges_complete AND g.required_nonempty
            THEN 'PASS_TO_EXHAUSTIVE_IDENTITY_AUDIT'
            ELSE 'BLOCK_DISPOSITION_SCREEN'
        END,
        'deferred_when_blocked', jsonb_build_array(
            'exact fill-to-market/outcome mapping proof',
            'exact CTF-condition-to-market mapping proof',
            'historical wallet inventory replay',
            'behavioral or strategy test'
        ),
        'caveats', jsonb_build_array(
            'market.positions is current diagnostic output, not historical input',
            'block inclusion is the public availability clock; collector arrival and confirmation delay remain separate',
            'a passing operational gate still requires exhaustive identity audit before replay'
        )
    )
)
FROM constants k
CROSS JOIN cursors c
CROSS JOIN repairs r
CROSS JOIN existence e
CROSS JOIN privileges p
CROSS JOIN gates g;
