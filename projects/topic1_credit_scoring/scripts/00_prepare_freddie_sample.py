"""
00_prepare_freddie_sample.py

Convert Freddie Mac sample origination and monthly performance files into:

projects/topic1_credit_scoring/data/raw/freddie_sample.csv

Expected input files:
- data/raw/freddie/sample_orig_2022.txt
- data/raw/freddie/sample_svcg_2022.txt
- data/raw/freddie/sample_orig_2023.txt
- data/raw/freddie/sample_svcg_2023.txt

Output columns:
- loan_sequence_number
- credit_score
- cltv
- dti
- interest_rate
- ever_30_dpd
- ever_90_dpd
- vintage
"""

from pathlib import Path
import re
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_DIR = TOPIC_DIR / "data" / "raw"
FREDDIE_DIR = RAW_DIR / "freddie"
OUTPUT_PATH = RAW_DIR / "freddie_sample.csv"


def extract_year(path: Path) -> int:
    match = re.search(r"(20\d{2}|19\d{2})", path.name)
    if not match:
        raise ValueError(f"Cannot extract vintage year from filename: {path.name}")
    return int(match.group(1))


def clean_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def read_orig_file(path: Path) -> pd.DataFrame:
    """
    Freddie sample_orig files are pipe-delimited and do not include headers.

    Correct observed layout:
    0  = credit score
    1  = first payment date
    8  = original CLTV
    9  = original DTI
    12 = original interest rate
    19 = loan sequence number
    """
    vintage = extract_year(path)

    df = pd.read_csv(
        path,
        sep="|",
        header=None,
        dtype=str,
        engine="python",
    )

    required_positions = [0, 1, 8, 9, 12, 19]
    if df.shape[1] <= max(required_positions):
        raise ValueError(
            f"{path.name} has only {df.shape[1]} columns; expected at least {max(required_positions) + 1}."
        )

    out = pd.DataFrame({
        "loan_sequence_number": df.iloc[:, 19].astype(str).str.strip(),
        "credit_score": clean_numeric(df.iloc[:, 0]),
        "first_payment_yyyymm": df.iloc[:, 1].astype(str).str.strip(),
        "cltv": clean_numeric(df.iloc[:, 8]),
        "dti": clean_numeric(df.iloc[:, 9]),
        "interest_rate": clean_numeric(df.iloc[:, 12]),
        "vintage": vintage,
    })

    return out


def read_svcg_file(path: Path) -> pd.DataFrame:
    """
    Freddie sample_svcg files are pipe-delimited and do not include headers.

    Observed layout:
    0 = loan sequence number
    3 = current loan delinquency status

    Delinquency coding used here:
    0 = current
    1 = 30 days delinquent
    2 = 60 days delinquent
    3 or higher = 90+ days delinquent
    """
    df = pd.read_csv(
        path,
        sep="|",
        header=None,
        dtype=str,
        engine="python",
    )

    required_positions = [0, 3]
    if df.shape[1] <= max(required_positions):
        raise ValueError(
            f"{path.name} has only {df.shape[1]} columns; expected at least {max(required_positions) + 1}."
        )

    out = pd.DataFrame({
        "loan_sequence_number": df.iloc[:, 0].astype(str).str.strip(),
        "delinquency_status": clean_numeric(df.iloc[:, 3]),
    })

    out["delinquency_status"] = out["delinquency_status"].fillna(0)

    perf = (
        out
        .groupby("loan_sequence_number", as_index=False)
        .agg(max_delinquency_status=("delinquency_status", "max"))
    )

    perf["ever_30_dpd"] = (perf["max_delinquency_status"] >= 1).astype(int)
    perf["ever_90_dpd"] = (perf["max_delinquency_status"] >= 3).astype(int)

    return perf[["loan_sequence_number", "ever_30_dpd", "ever_90_dpd"]]


def main():
    orig_files = sorted(FREDDIE_DIR.glob("sample_orig_*.txt"))
    svcg_files = sorted(FREDDIE_DIR.glob("sample_svcg_*.txt"))

    if not orig_files:
        raise FileNotFoundError(f"No sample_orig_*.txt files found in {FREDDIE_DIR}")

    if not svcg_files:
        raise FileNotFoundError(f"No sample_svcg_*.txt files found in {FREDDIE_DIR}")

    orig_frames = []
    perf_frames = []

    for path in orig_files:
        print(f"Reading origination file: {path.name}")
        orig_frames.append(read_orig_file(path))

    for path in svcg_files:
        print(f"Reading performance file: {path.name}")
        perf_frames.append(read_svcg_file(path))

    orig = pd.concat(orig_frames, ignore_index=True)
    perf = pd.concat(perf_frames, ignore_index=True)

    perf = (
        perf
        .groupby("loan_sequence_number", as_index=False)
        .agg(
            ever_30_dpd=("ever_30_dpd", "max"),
            ever_90_dpd=("ever_90_dpd", "max"),
        )
    )

    merged = orig.merge(perf, on="loan_sequence_number", how="left")

    merged["ever_30_dpd"] = merged["ever_30_dpd"].fillna(0).astype(int)
    merged["ever_90_dpd"] = merged["ever_90_dpd"].fillna(0).astype(int)

    for col in ["credit_score", "cltv", "dti", "interest_rate"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    final = merged.dropna(
        subset=["credit_score", "cltv", "dti", "interest_rate", "vintage"]
    ).copy()

    final = final[
        [
            "loan_sequence_number",
            "credit_score",
            "cltv",
            "dti",
            "interest_rate",
            "ever_30_dpd",
            "ever_90_dpd",
            "vintage",
        ]
    ]

    final.to_csv(OUTPUT_PATH, index=False)

    print()
    print("Saved Freddie sample CSV to:")
    print(OUTPUT_PATH)
    print()
    print("Shape:", final.shape)
    print()
    print("Vintage counts:")
    print(final["vintage"].value_counts().sort_index())
    print()
    print("ever_30_dpd positive rate:")
    print(final["ever_30_dpd"].mean())
    print()
    print("ever_90_dpd positive rate:")
    print(final["ever_90_dpd"].mean())
    print()
    print(final.head())


if __name__ == "__main__":
    main()
