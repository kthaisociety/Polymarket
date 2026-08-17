aliases = [
    "cz",
    "zelenskyy",
    "nyc_mayor",
    "khamenei",
    "elon",
    "ted_cruz",
    "white_house",
    "donald_trump_truth",
]
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
record_keys = set(
    ("id", "userId", "platformId", "content", "createdAt", "importedAt", "metrics")
)
results = []
for alias in aliases:
    payload = payloads[alias]
    assert set(payload) == set(("success", "data"))
    rows = payload["data"]
    record_ids = set()
    platform_ids = set()
    minimum_created = None
    maximum_created = None
    minimum_imported = None
    maximum_imported = None
    valid_records = True
    for row in rows:
        if set(row) != record_keys:
            valid_records = False
        else:
            created_at = row["createdAt"]
            imported_at = row["importedAt"]
            if (
                len(created_at) != 24
                or len(imported_at) != 24
                or created_at[23] != "Z"
                or imported_at[23] != "Z"
                or created_at > imported_at
                or row["id"] in record_ids
                or row["platformId"] in platform_ids
            ):
                valid_records = False
            record_ids = record_ids | set((row["id"],))
            platform_ids = platform_ids | set((row["platformId"],))
            if minimum_created is None or created_at < minimum_created:
                minimum_created = created_at
            if maximum_created is None or created_at > maximum_created:
                maximum_created = created_at
            if minimum_imported is None or imported_at < minimum_imported:
                minimum_imported = imported_at
            if maximum_imported is None or imported_at > maximum_imported:
                maximum_imported = imported_at
    results = results + [
        {
            "alias": alias,
            "success": payload["success"],
            "record_count": len(rows),
            "valid_strict_record_shape": valid_records,
            "minimum_created_at": minimum_created,
            "maximum_created_at": maximum_created,
            "minimum_imported_at": minimum_imported,
            "maximum_imported_at": maximum_imported,
        }
    ]

result = emit(
    {
        "schema_version": "xtracker-family-source-audit/v1",
        "sources": results,
        "post_content_retained_in_output": False,
    }
)
