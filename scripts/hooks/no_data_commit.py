#!/usr/bin/env python3
"""Pre-commit hook: block any file under data/ or any file larger than 5 MB."""

import sys
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024  # 5 MB
violations = []

for path_str in sys.argv[1:]:
    path = Path(path_str)
    parts = path.parts

    if "data" in parts:
        violations.append(f"  data/ file: {path_str}")
        continue

    try:
        size = path.stat().st_size
    except FileNotFoundError:
        continue  # deleted file, not a commit violation

    if size > MAX_BYTES:
        violations.append(f"  file too large ({size / 1e6:.1f} MB): {path_str}")

if violations:
    print("COMMIT BLOCKED — the following files violate the no-data policy:")
    for v in violations:
        print(v)
    print(
        "\nSurvey microdata must never be committed (GESIS/EVS license).\n"
        "Large files belong in outputs/ (gitignored) or object storage."
    )
    sys.exit(1)
