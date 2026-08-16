"""
00_project_setup_topic2.py

Create and verify the Topic 2 Blockchain Market Integrity Risk project structure.
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

DIRS = [
    "data/raw",
    "data/processed",
    "results/tables",
    "results/figures",
    "scripts",
    "docs",
]

REQUIRED_FILES = [
    "README.md",
    "docs/claim_boundary.md",
    "docs/data_notes.md",
    "data/raw/crypto_incidents_seed.csv",
]


def main():
    rows = []

    for d in DIRS:
        path = TOPIC_DIR / d
        path.mkdir(parents=True, exist_ok=True)
        rows.append({
            "item_type": "directory",
            "path": str(path.relative_to(PROJECT_ROOT)),
            "exists": path.exists(),
        })

    for f in REQUIRED_FILES:
        path = TOPIC_DIR / f
        rows.append({
            "item_type": "file",
            "path": str(path.relative_to(PROJECT_ROOT)),
            "exists": path.exists(),
        })

    out = pd.DataFrame(rows)

    output_path = TOPIC_DIR / "results" / "tables" / "topic2_project_setup_check.csv"
    out.to_csv(output_path, index=False)

    print(out)
    print()
    print("Saved setup check to:")
    print(output_path)


if __name__ == "__main__":
    main()
