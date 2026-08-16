"""
11_false_alert_taxonomy.py

Build false-alert taxonomy and manual error-review sample for Topic 2.

Important boundary:
- Alerts are review candidates.
- Non-event-window alerts are not necessarily false in reality.
- Event-window labels are weak labels, not verified fraud ground truth.

Inputs:
- data/processed/blockchain_risk_panel_weak_supervision.csv

Outputs:
- results/tables/false_alert_taxonomy.csv
- results/tables/false_alert_summary.csv
- results/tables/error_review_sample.csv
- results/figures/false_alert_taxonomy_counts.png
- results/figures/false_alert_score_by_category.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"
FIGURE_DIR = TOPIC_DIR / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

INPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_weak_supervision.csv"

TAXONOMY_PATH = TABLE_DIR / "false_alert_taxonomy.csv"
SUMMARY_PATH = TABLE_DIR / "false_alert_summary.csv"
ERROR_SAMPLE_PATH = TABLE_DIR / "error_review_sample.csv"

COUNT_FIGURE_PATH = FIGURE_DIR / "false_alert_taxonomy_counts.png"
SCORE_FIGURE_PATH = FIGURE_DIR / "false_alert_score_by_category.png"


def get_num(df, col, default=0):
    if col not in df.columns:
        return pd.Series(default, index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def classify_alerts(df):
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["asset"] = out["asset"].astype(str).str.upper()

    score = get_num(out, "weak_supervision_score")
    out["asset_score_pct"] = score.groupby(out["asset"]).rank(pct=True)

    # Top alerts are asset-specific top 5%.
    top = out[out["asset_score_pct"] >= 0.95].copy()

    # Numeric helper variables.
    top["weak_label_7d"] = get_num(top, "weak_label_7d").astype(int)
    top["weak_label_3d"] = get_num(top, "weak_label_3d").astype(int)
    top["lf_vote_count"] = get_num(top, "lf_vote_count").astype(int)

    top["stablecoin_peg_deviation"] = get_num(top, "stablecoin_peg_deviation")
    top["abs_log_return"] = get_num(top, "abs_log_return")
    top["volume_z_30d"] = get_num(top, "volume_z_30d")
    top["intraday_range_z_30d"] = get_num(top, "intraday_range_z_30d")
    top["drawdown_30d"] = get_num(top, "drawdown_30d")
    top["dex_volume_z_30d"] = get_num(top, "dex_volume_z_30d")
    top["chain_tvl_z_30d"] = get_num(top, "chain_tvl_z_30d")
    top["transparent_risk_score"] = get_num(top, "transparent_risk_score")
    top["anomaly_ensemble_score"] = get_num(top, "anomaly_ensemble_score")

    categories = []
    review_notes = []

    for _, r in top.iterrows():
        asset = r["asset"]

        in_event_window = int(r["weak_label_7d"]) == 1
        in_tight_event_window = int(r["weak_label_3d"]) == 1

        is_stablecoin = asset in ["USDC", "USDT"]
        peg_stress = is_stablecoin and r["stablecoin_peg_deviation"] >= 0.005

        market_stress = (
            abs(r["volume_z_30d"]) >= 2
            or abs(r["intraday_range_z_30d"]) >= 2
            or r["abs_log_return"] >= top["abs_log_return"].quantile(0.90)
            or r["drawdown_30d"] <= top["drawdown_30d"].quantile(0.10)
        )

        defi_context = (
            abs(r["dex_volume_z_30d"]) >= 2
            or abs(r["chain_tvl_z_30d"]) >= 2
        )

        method_consensus = (
            r["transparent_risk_score"] >= 90
            and r["anomaly_ensemble_score"] >= 0.90
        ) or r["lf_vote_count"] >= 3

        if in_tight_event_window:
            category = "event_window_hit_3d"
            note = "Alert falls within a tight public incident window. This supports weak-label alignment, not verified fraud detection."
        elif in_event_window:
            category = "event_window_hit_7d"
            note = "Alert falls within a wider public incident window. This is weak-label evidence only."
        elif peg_stress:
            category = "stablecoin_peg_stress_non_event"
            note = "Stablecoin price deviates from peg outside the public incident window. Review as peg-stress alert, not confirmed event."
        elif method_consensus and market_stress:
            category = "multi_method_market_stress_non_event"
            note = "Multiple methods agree and market stress variables are elevated, but no event-window label is present."
        elif method_consensus:
            category = "multi_method_consensus_non_event"
            note = "Multiple methods agree, but the alert is outside known public incident windows."
        elif market_stress:
            category = "market_stress_non_event"
            note = "Market stress variables are elevated outside known public incident windows."
        elif defi_context:
            category = "defi_context_shock_non_event"
            note = "DeFi or chain-context variables are unusual outside known public incident windows."
        else:
            category = "isolated_anomaly_review"
            note = "High score is driven by limited or isolated signals. Treat as likely false-alert candidate for manual review."

        categories.append(category)
        review_notes.append(note)

    top["taxonomy_category"] = categories
    top["review_note"] = review_notes

    top["manual_review_priority"] = np.select(
        [
            top["taxonomy_category"].isin(["event_window_hit_3d", "event_window_hit_7d"]),
            top["taxonomy_category"].isin(["multi_method_market_stress_non_event", "stablecoin_peg_stress_non_event"]),
            top["taxonomy_category"].isin(["multi_method_consensus_non_event", "market_stress_non_event"]),
        ],
        [
            "high",
            "medium_high",
            "medium",
        ],
        default="low",
    )

    top["claim_boundary"] = (
        "False-alert taxonomy is an error-review framework. "
        "Non-event-window alerts are not proof of model failure, and event-window hits are not verified fraud ground truth."
    )

    return top


def make_summary(taxonomy):
    if taxonomy.empty:
        return pd.DataFrame()

    summary = (
        taxonomy
        .groupby("taxonomy_category", as_index=False)
        .agg(
            n_alerts=("taxonomy_category", "size"),
            mean_weak_supervision_score=("weak_supervision_score", "mean"),
            mean_transparent_score=("transparent_risk_score", "mean"),
            mean_anomaly_score=("anomaly_ensemble_score", "mean"),
            weak_label_3d_rate=("weak_label_3d", "mean"),
            weak_label_7d_rate=("weak_label_7d", "mean"),
            mean_lf_vote_count=("lf_vote_count", "mean"),
        )
    )

    summary["share_of_top_alerts"] = summary["n_alerts"] / summary["n_alerts"].sum()

    summary["interpretation"] = summary["taxonomy_category"].map({
        "event_window_hit_3d": "Top alerts that align with tight public incident windows.",
        "event_window_hit_7d": "Top alerts that align with wider public incident windows.",
        "stablecoin_peg_stress_non_event": "Stablecoin peg-stress alerts outside public incident windows.",
        "multi_method_market_stress_non_event": "Non-event alerts where several methods agree and market stress is visible.",
        "multi_method_consensus_non_event": "Non-event alerts where methods agree but market-stress evidence is less direct.",
        "market_stress_non_event": "Non-event alerts mainly explained by market volatility, return, drawdown, or volume stress.",
        "defi_context_shock_non_event": "Non-event alerts mainly explained by DeFi or chain-context variables.",
        "isolated_anomaly_review": "Isolated high-score cases that need manual review and are likely false-alert candidates.",
    })

    summary["claim_boundary"] = (
        "Category counts describe review patterns, not confirmed false-positive rates."
    )

    return summary.sort_values("n_alerts", ascending=False)


def make_error_review_sample(taxonomy):
    if taxonomy.empty:
        return pd.DataFrame()

    cols = [
        "date",
        "asset",
        "taxonomy_category",
        "manual_review_priority",
        "weak_supervision_score",
        "transparent_risk_score",
        "anomaly_ensemble_score",
        "lf_vote_count",
        "weak_label_3d",
        "weak_label_7d",
        "event_ids_7d",
        "event_type_list_7d",
        "severity_list_7d",
        "log_return",
        "abs_log_return",
        "volume_z_30d",
        "intraday_range_z_30d",
        "drawdown_30d",
        "stablecoin_peg_deviation",
        "dex_volume_z_30d",
        "chain_tvl_z_30d",
        "review_note",
        "claim_boundary",
    ]

    existing = [c for c in cols if c in taxonomy.columns]

    # Take a balanced sample by category, then sort by priority and score.
    sample = (
        taxonomy
        .sort_values("weak_supervision_score", ascending=False)
        .groupby("taxonomy_category", group_keys=False)
        .head(10)
        .copy()
    )

    priority_order = {
        "high": 1,
        "medium_high": 2,
        "medium": 3,
        "low": 4,
    }

    sample["priority_order"] = sample["manual_review_priority"].map(priority_order).fillna(9)

    sample = sample.sort_values(
        ["priority_order", "weak_supervision_score"],
        ascending=[True, False],
    )

    sample = sample[existing].copy()

    return sample


def make_figures(taxonomy, summary):
    if taxonomy.empty or summary.empty:
        plt.figure(figsize=(8, 5))
        plt.text(0.1, 0.5, "No top alerts available for taxonomy.")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(COUNT_FIGURE_PATH, dpi=200)
        plt.close()

        plt.figure(figsize=(8, 5))
        plt.text(0.1, 0.5, "No top alerts available for taxonomy.")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(SCORE_FIGURE_PATH, dpi=200)
        plt.close()
        return

    plot_data = summary.sort_values("n_alerts", ascending=False)

    plt.figure(figsize=(12, 5))
    plt.bar(plot_data["taxonomy_category"], plot_data["n_alerts"])
    plt.title("False-alert taxonomy: top-alert counts")
    plt.ylabel("Number of top alerts")
    plt.xlabel("Taxonomy category")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(COUNT_FIGURE_PATH, dpi=200)
    plt.close()

    score_data = summary.sort_values("mean_weak_supervision_score", ascending=False)

    plt.figure(figsize=(12, 5))
    plt.bar(score_data["taxonomy_category"], score_data["mean_weak_supervision_score"])
    plt.title("False-alert taxonomy: mean weak-supervision score")
    plt.ylabel("Mean weak-supervision score")
    plt.xlabel("Taxonomy category")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(SCORE_FIGURE_PATH, dpi=200)
    plt.close()


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing blockchain_risk_panel_weak_supervision.csv. Run 08_weak_supervision_label_model.py first.")

    df = pd.read_csv(INPUT_PATH)

    taxonomy = classify_alerts(df)
    summary = make_summary(taxonomy)
    error_sample = make_error_review_sample(taxonomy)

    taxonomy.to_csv(TAXONOMY_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    error_sample.to_csv(ERROR_SAMPLE_PATH, index=False)

    make_figures(taxonomy, summary)

    print("Saved false-alert taxonomy to:")
    print(TAXONOMY_PATH)
    print()
    print(taxonomy[["date", "asset", "taxonomy_category", "manual_review_priority", "weak_supervision_score", "weak_label_7d"]].head(30))

    print()
    print("Saved false-alert summary to:")
    print(SUMMARY_PATH)
    print()
    print(summary)

    print()
    print("Saved error-review sample to:")
    print(ERROR_SAMPLE_PATH)
    print()
    print(error_sample.head(30))

    print()
    print("Saved figures:")
    print(COUNT_FIGURE_PATH)
    print(SCORE_FIGURE_PATH)


if __name__ == "__main__":
    main()
