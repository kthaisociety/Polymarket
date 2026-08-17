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

observations = []
for event in events:
    event_id = event[0]
    event_start = event[1]
    event_end = event[2]
    decisions = event[3]
    previous_count = -1
    for decision in decisions:
        decision_day = decision[0]
        decision_time = decision[1]
        count = 0
        for row in rows:
            assert set(row) == record_keys
            created_at = row["createdAt"]
            imported_at = row["importedAt"]
            assert created_at <= imported_at
            if (
                event_start <= created_at
                and created_at <= event_end
                and imported_at <= decision_time
            ):
                count = count + 1
        assert count >= previous_count
        previous_count = count
        observations = observations + [
            {
                "field_id": "cumulative_post_count",
                "value": count,
                "reference_time": decision_time,
                "available_at": decision_time,
                "vintage_id": event_id + ":day-" + str(decision_day),
                "revision_number": 0,
                "dimensions": {
                    "event_id": event_id,
                    "user_handle": user_handle,
                    "platform": platform,
                    "decision_day": str(decision_day),
                },
                "caveats": [
                    "COUNT_INCLUDES_ONLY_POSTS_IMPORTED_BY_DECISION",
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
