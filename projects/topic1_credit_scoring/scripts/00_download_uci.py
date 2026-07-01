"""
00_download_uci.py

Download the UCI Default of Credit Card Clients dataset and save it as:
projects/topic1_credit_scoring/data/raw/uci_default.csv

The saved file uses clear column names and a binary label:
target_default
"""

from pathlib import Path
import pandas as pd
from ucimlrepo import fetch_ucirepo


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_DIR = TOPIC_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RAW_DIR / "uci_default.csv"


def main():
    dataset = fetch_ucirepo(id=350)

    X = dataset.data.features.copy()
    y = dataset.data.targets.copy()

    # Rename target to a clear project label.
    y = y.rename(columns={y.columns[0]: "target_default"})

    df = pd.concat([X, y], axis=1)

    # UCI may return columns as X1-X23. Rename them to financial meanings.
    rename_map = {
        "X1": "LIMIT_BAL",
        "X2": "SEX",
        "X3": "EDUCATION",
        "X4": "MARRIAGE",
        "X5": "AGE",
        "X6": "PAY_0",
        "X7": "PAY_2",
        "X8": "PAY_3",
        "X9": "PAY_4",
        "X10": "PAY_5",
        "X11": "PAY_6",
        "X12": "BILL_AMT1",
        "X13": "BILL_AMT2",
        "X14": "BILL_AMT3",
        "X15": "BILL_AMT4",
        "X16": "BILL_AMT5",
        "X17": "BILL_AMT6",
        "X18": "PAY_AMT1",
        "X19": "PAY_AMT2",
        "X20": "PAY_AMT3",
        "X21": "PAY_AMT4",
        "X22": "PAY_AMT5",
        "X23": "PAY_AMT6",
    }
    df = df.rename(columns=rename_map)

    df.to_csv(OUTPUT_PATH, index=False)

    print("Saved UCI dataset to:")
    print(OUTPUT_PATH)
    print()
    print("Shape:", df.shape)
    print("Columns:")
    print(df.columns.tolist())
    print()
    print("Positive rate target_default:")
    print(df["target_default"].mean())


if __name__ == "__main__":
    main()
