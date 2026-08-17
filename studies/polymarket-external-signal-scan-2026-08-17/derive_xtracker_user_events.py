payload = json_input("xtracker")
assert set(payload) == set(("success", "data"))
assert payload["success"] is True
rows = payload["data"]
events = param("events")
profile_id = param("profile_id")
user_handle = param("user_handle")
platform = param("platform")
record_keys = set(
    ("id", "userId", "platformId", "content", "createdAt", "importedAt", "metrics")
)

observation_count = 0
for event in events:
    for row in rows:
        if event[1] <= row["createdAt"] and row["createdAt"] <= event[2]:
            observation_count = observation_count + 1

observations = [None for unused in range(observation_count)]
observation_ordinal = 0
observation_keys = {}
for event in events:
    event_id = event[0]
    admitted = 0
    for row in rows:
        assert set(row) == record_keys
        created_at = row["createdAt"]
        imported_at = row["importedAt"]
        assert created_at <= imported_at
        if event[1] <= created_at and created_at <= event[2]:
            key = event_id + ":" + platform + ":" + row["platformId"]
            assert key not in observation_keys
            observation_keys[key] = True
            observations[observation_ordinal] = {
                "field_id": "post_imported",
                "value": 1,
                "reference_time": created_at,
                "available_at": imported_at,
                "vintage_id": row["id"],
                "revision_number": 0,
                "dimensions": {
                    "event_id": event_id,
                    "user_handle": user_handle,
                    "platform": platform,
                    "platform_post_id": row["platformId"],
                },
                "caveats": [
                    "CURRENT_RESPONSE_PROVES_PRESENCE_NOT_HISTORICAL_COMPLETENESS",
                    "XTRACKER_IMPORTED_AT_IS_CONSERVATIVE_AVAILABILITY",
                    "POST_TEXT_AND_METRICS_EXCLUDED",
                ],
            }
            observation_ordinal = observation_ordinal + 1
            admitted = admitted + 1
    assert admitted > 0

assert observation_ordinal == observation_count
result = emit(
    {
        "schema_version": "temporal-observations/v1",
        "profile_id": profile_id,
        "observations": observations,
    }
)
