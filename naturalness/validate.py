"""Checks the dataset before training. Exits with an error if anything is wrong."""
import sys

from common import COLUMNS, ISSUES, STATUSES, load_pairs

pairs = load_pairs()
errors = []

if list(pairs.columns) != COLUMNS:
    errors.append(f"Columns must be {COLUMNS}, got {list(pairs.columns)}")
else:
    for i, row in pairs.iterrows():
        where = f"row {i + 2} ({row['pair_id'] or 'no id'})"
        for col in ("pair_id", "literal_ar", "natural_ar", "issue", "status"):
            if not row[col].strip():
                errors.append(f"{where}: empty {col}")
        if row["literal_ar"].strip() == row["natural_ar"].strip():
            errors.append(f"{where}: literal and natural are identical")
        if row["issue"] not in ISSUES:
            errors.append(f"{where}: unknown issue '{row['issue']}' (allowed: {', '.join(ISSUES)})")
        if row["status"] not in STATUSES:
            errors.append(f"{where}: status must be one of {sorted(STATUSES)}")
    for col in ("pair_id", "literal_ar", "natural_ar"):
        dupes = pairs[pairs[col].duplicated()][col].tolist()
        if dupes:
            errors.append(f"duplicate {col}: {dupes}")

if errors:
    print("Dataset has problems:")
    print("\n".join(f"  - {e}" for e in errors))
    sys.exit(1)

reviewed = (pairs["status"] == "reviewed").sum()
print(f"OK: {len(pairs)} pairs ({reviewed} reviewed, {len(pairs) - reviewed} seed)")
print(pairs["issue"].value_counts().to_string())
