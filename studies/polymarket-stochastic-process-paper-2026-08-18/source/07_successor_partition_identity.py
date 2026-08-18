result = structured_return(
    "Identity-only successor replication partition audit.",
    {
        "schema_version": "polymarket-successor-partition-audit/v1",
        "value_fields_read": 0,
        "partition_values_requested": False,
    },
    warnings=[
        "This source reads no market, probability, question, lifecycle, or payout field.",
        "Receipt-level counts and identities establish authority but are not scientific evidence.",
        "Ancestor and final protected values remain unavailable.",
    ],
)
