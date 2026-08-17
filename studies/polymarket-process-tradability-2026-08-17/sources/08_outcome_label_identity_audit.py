markets = read("polymarket-development-outcomes", "market_id")
labels = read("polymarket-development-outcomes", "outcome_label")

label_counts = {}
for label in labels:
    if label not in label_counts:
        label_counts[label] = 0
    label_counts[label] = label_counts[label] + 1

result = structured_return(
    "Exact retained outcome-label audit for every development probability path.",
    {
        "market_count": len(markets),
        "label_counts": label_counts,
        "all_paths_are_yes_labeled": label_counts == {"Yes": len(markets)},
    },
    warnings=[
        "Outcome meaning is read from retained contract identity rather than inferred from index zero.",
        "Protected contracts remain unavailable.",
    ],
)
