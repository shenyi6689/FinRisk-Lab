"""
00_download_fred.py

Download simple FRED macro-rate series and save them as:
projects/topic1_credit_scoring/data/raw/fred_macro.csv
"""

from pathlib import Path
from functools import reduce
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_DIR = TOPIC_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RAW_DIR / "fred_macro.csv"

SERIES = {
    "FEDFUNDS": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS",
    "MORTGAGE30US": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US",
    "DGS10": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
    "UNRATE": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE",
}


def read_fred_series(name, url):
    df = pd.read_csv(url)
    df = df.rename(columns={"observation_date": "date", name: name})
    df["date"] = pd.to_datetime(df["date"])
    df[name] = pd.to_numeric(df[name], errors="coerce")
    return df[["date", name]]


def main():
    frames = [read_fred_series(name, url) for name, url in SERIES.items()]
    macro = reduce(lambda left, right: left.merge(right, on="date", how="outer"), frames)
    macro = macro.sort_values("date")

    macro.to_csv(OUTPUT_PATH, index=False)

    print("Saved FRED macro data to:")
    print(OUTPUT_PATH)
    print()
    print(macro.tail())


if __name__ == "__main__":
    main()
