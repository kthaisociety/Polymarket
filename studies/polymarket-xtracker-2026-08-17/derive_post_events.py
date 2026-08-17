payload = json_input("xtracker")
assert set(payload) == set(("success", "data"))
assert payload["success"] is True
rows = payload["data"]
assert len(rows) > 0

start_time = param("start_time")
end_time = param("end_time")
profile_id = param("profile_id")
event_id = param("event_id")
tracking_id = param("tracking_id")
user_handle = param("user_handle")
platform = param("platform")

record_keys = set(
    ("id", "userId", "platformId", "content", "createdAt", "importedAt", "metrics")
)
platform_ids = set()
record_ids = set()
observations = []

for row in rows:
    assert set(row) == record_keys
    assert len(row["id"]) > 0
    assert len(row["userId"]) > 0
    assert len(row["platformId"]) > 0
    assert row["id"] not in record_ids
    assert row["platformId"] not in platform_ids
    created_at = row["createdAt"]
    imported_at = row["importedAt"]
    assert len(created_at) == 24
    assert len(imported_at) == 24
    assert created_at[4] == "-"
    assert created_at[7] == "-"
    assert created_at[10] == "T"
    assert created_at[23] == "Z"
    assert imported_at[4] == "-"
    assert imported_at[7] == "-"
    assert imported_at[10] == "T"
    assert imported_at[23] == "Z"
    assert start_time <= created_at
    assert created_at <= end_time
    assert created_at <= imported_at
    record_ids = record_ids | set((row["id"],))
    platform_ids = platform_ids | set((row["platformId"],))
    observations = observations + [
        {
            "field_id": "post_imported",
            "value": 1,
            "reference_time": created_at,
            "available_at": imported_at,
            "vintage_id": row["id"],
            "revision_number": 0,
            "dimensions": {
                "event_id": event_id,
                "tracking_id": tracking_id,
                "user_handle": user_handle,
                "platform": platform,
                "platform_post_id": row["platformId"],
            },
            "caveats": [
                "CURRENT_RESPONSE_PROVES_PRESENCE_NOT_HISTORICAL_COMPLETENESS",
                "POST_TEXT_AND_METRICS_EXCLUDED",
            ],
        }
    ]

result = emit(
    {
        "schema_version": "temporal-observations/v1",
        "profile_id": profile_id,
        "observations": observations,
    }
)

