payloads = {
    "cz": json_input("cz"),
    "zelenskyy": json_input("zelenskyy"),
    "nyc_mayor": json_input("nyc_mayor"),
    "khamenei": json_input("khamenei"),
    "elon": json_input("elon"),
    "ted_cruz": json_input("ted_cruz"),
    "white_house": json_input("white_house"),
    "donald_trump_truth": json_input("donald_trump_truth"),
}
events = [
    ["716154", "cz", "cz_binance", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["716156", "zelenskyy", "ZelenskyyUa", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["716153", "nyc_mayor", "NYCMayor", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["716150", "khamenei", "khamenei_ir", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["716159", "elon", "elonmusk", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["739241", "elon", "elonmusk", "X", "2026-07-25T16:00:00.000Z", "2026-07-27T15:59:59.000Z"],
    ["748763", "elon", "elonmusk", "X", "2026-07-27T16:00:00.000Z", "2026-07-29T15:59:59.000Z"],
    ["716157", "ted_cruz", "tedcruz", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["716151", "white_house", "WhiteHouse", "X", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
    ["727674", "white_house", "WhiteHouse", "X", "2026-07-24T16:00:00.000Z", "2026-07-31T15:59:59.000Z"],
    ["716152", "donald_trump_truth", "realDonaldTrump", "TRUTH_SOCIAL", "2026-07-21T16:00:00.000Z", "2026-07-28T15:59:59.000Z"],
]
profile_id = param("profile_id")
record_keys = set(
    ("id", "userId", "platformId", "content", "createdAt", "importedAt", "metrics")
)
observation_count = 0
for event in events:
    payload = payloads[event[1]]
    for row in payload["data"]:
        if event[4] <= row["createdAt"] and row["createdAt"] <= event[5]:
            observation_count = observation_count + 1

observations = [None for unused in range(observation_count)]
observation_ordinal = 0
observation_keys = {}

for event in events:
    event_id = event[0]
    alias = event[1]
    user_handle = event[2]
    platform = event[3]
    start_time = event[4]
    end_time = event[5]
    payload = payloads[alias]
    assert set(payload) == set(("success", "data"))
    assert payload["success"] is True
    admitted = 0
    for row in payload["data"]:
        assert set(row) == record_keys
        created_at = row["createdAt"]
        imported_at = row["importedAt"]
        assert created_at <= imported_at
        if start_time <= created_at and created_at <= end_time:
            key = event_id + ":" + platform + ":" + row["platformId"]
            assert key not in observation_keys
            observation_keys[key] = True
            admitted = admitted + 1
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
    assert admitted > 0

assert observation_ordinal == observation_count

result = emit(
    {
        "schema_version": "temporal-observations/v1",
        "profile_id": profile_id,
        "observations": observations,
    }
)
