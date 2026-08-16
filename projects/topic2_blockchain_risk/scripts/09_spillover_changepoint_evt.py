"""
09_spillover_changepoint_evt.py

Run spillover, change-point, and EVT/POT tail-risk diagnostics for Topic 2.

Inputs:
- data/processed/blockchain_risk_panel_weak_supervision.csv
- data/processed/incident_ledger_validated.csv

Outputs:
- results/tables/spillover_connectedness.csv
- results/tables/change_point_timeline.csv
- results/tables/evt_tail_risk.csv
- results/figures/spillover_connectedness_heatmap.png
- results/figures/changepoint_timeline.png
- results/figures/evt_tail_thresholds.png
"""

from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import genpareto

try:
    import ruptures as rpt
    RUPTURES_AVAILABLE = True
except Exception:
    RUPTURES_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"
FIGURE_DIR = TOPIC_DIR / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

INPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_weak_supervision.csv"
INCIDENT_PATH = PROCESSED_DIR / "incident_ledger_validated.csv"

SPILLOVER_PATH = TABLE_DIR / "spillover_connectedness.csv"
CHANGEPOINT_PATH = TABLE_DIR / "change_point_timeline.csv"
EVT_PATH = TABLE_DIR / "evt_tail_risk.csv"

SPILLOVER_FIGURE_PATH = FIGURE_DIR / "spillover_connectedness_heatmap.png"
CHANGEPOINT_FIGURE_PATH = FIGURE_DIR / "changepoint_timeline.png"
EVT_FIGURE_PATH = FIGURE_DIR / "evt_tail_thresholds.png"


def safe_corr(a, b):
    tmp = pd.concat([a, b], axis=1).dropna()
    if len(tmp) < 10:
        return np.nan
    if tmp.iloc[:, 0].nunique() <= 1 or tmp.iloc[:, 1].nunique() <= 1:
        return np.nan
    return tmp.iloc[:, 0].corr(tmp.iloc[:, 1])


def nearest_incident(date, incidents):
    if incidents.empty:
        return "", "", np.nan

    d = pd.to_datetime(date)
    incidents = incidents.copy()
    incidents["event_date"] = pd.to_datetime(incidents["event_date"], errors="coerce")
    incidents = incidents.dropna(subset=["event_date"])

    if incidents.empty:
        return "", "", np.nan

    distances = (incidents["event_date"] - d).abs().dt.days
    idx = distances.idxmin()

    return (
        incidents.loc[idx, "event_id"],
        incidents.loc[idx, "event_type"],
        int(distances.loc[idx]),
    )


def spillover_connectedness(panel):
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["asset"] = df["asset"].astype(str).str.upper()

    # Event day is defined at the market level: any asset-day in weak_label_7d.
    event_dates = set(
        df.loc[df["weak_label_7d"] == 1, "date"].dropna().unique()
    )

    returns = df.pivot_table(
        index="date",
        columns="asset",
        values="log_return",
        aggfunc="first",
        dropna=False,
    ).sort_index()

    weak_scores = df.pivot_table(
        index="date",
        columns="asset",
        values="weak_supervision_score",
        aggfunc="first",
        dropna=False,
    ).sort_index()

    rows = []

    assets = sorted(df["asset"].dropna().unique())

    for asset_a, asset_b in itertools.combinations(assets, 2):
        if asset_a not in returns.columns or asset_b not in returns.columns:
            continue

        if asset_a not in weak_scores.columns or asset_b not in weak_scores.columns:
            continue

        r_a = returns[asset_a]
        r_b = returns[asset_b]

        s_a = weak_scores[asset_a]
        s_b = weak_scores[asset_b]

        # Important fix:
        # returns and weak_scores can have slightly different index lengths
        # because log_return can be missing on the first date.
        # Therefore each mask must be built from the corresponding series index.
        return_event_mask = r_a.index.isin(event_dates)
        return_non_event_mask = ~return_event_mask

        score_event_mask = s_a.index.isin(event_dates)
        score_non_event_mask = ~score_event_mask

        corr_all = safe_corr(r_a, r_b)
        corr_event = safe_corr(r_a.loc[return_event_mask], r_b.loc[return_event_mask])
        corr_non_event = safe_corr(r_a.loc[return_non_event_mask], r_b.loc[return_non_event_mask])

        score_corr_all = safe_corr(s_a, s_b)
        score_corr_event = safe_corr(s_a.loc[score_event_mask], s_b.loc[score_event_mask])
        score_corr_non_event = safe_corr(s_a.loc[score_non_event_mask], s_b.loc[score_non_event_mask])

        rows.append({
            "asset_a": asset_a,
            "asset_b": asset_b,
            "return_corr_all": corr_all,
            "return_corr_event_window_7d": corr_event,
            "return_corr_non_event": corr_non_event,
            "delta_abs_return_corr_event_minus_non_event": abs(corr_event) - abs(corr_non_event) if pd.notna(corr_event) and pd.notna(corr_non_event) else np.nan,
            "weak_score_corr_all": score_corr_all,
            "weak_score_corr_event_window_7d": score_corr_event,
            "weak_score_corr_non_event": score_corr_non_event,
            "delta_abs_score_corr_event_minus_non_event": abs(score_corr_event) - abs(score_corr_non_event) if pd.notna(score_corr_event) and pd.notna(score_corr_non_event) else np.nan,
            "n_all_days": int(pd.concat([r_a, r_b], axis=1).dropna().shape[0]),
            "n_event_window_days": int(pd.concat([r_a.loc[return_event_mask], r_b.loc[return_event_mask]], axis=1).dropna().shape[0]),
            "n_non_event_days": int(pd.concat([r_a.loc[return_non_event_mask], r_b.loc[return_non_event_mask]], axis=1).dropna().shape[0]),
            "claim_boundary": "Connectedness is descriptive spillover evidence, not causal transmission proof.",
        })

    out = pd.DataFrame(rows)

    # Heatmap: full-sample return correlation.
    corr = returns.corr()

    plt.figure(figsize=(8, 6))
    plt.imshow(corr.values, aspect="auto")
    plt.colorbar(label="Return correlation")
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45)
    plt.yticks(range(len(corr.index)), corr.index)
    plt.title("Full-sample return connectedness")
    plt.tight_layout()
    plt.savefig(SPILLOVER_FIGURE_PATH, dpi=200)
    plt.close()

    return out



def change_point_timeline(panel, incidents):
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])

    daily = (
        df.groupby("date", as_index=False)
        .agg(
            mean_weak_supervision_score=("weak_supervision_score", "mean"),
            mean_anomaly_ensemble_score=("anomaly_ensemble_score", "mean"),
            mean_abs_log_return=("abs_log_return", "mean"),
            max_weak_label_7d=("weak_label_7d", "max"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    signal_cols = [
        "mean_weak_supervision_score",
        "mean_anomaly_ensemble_score",
        "mean_abs_log_return",
    ]

    X = daily[signal_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True)).fillna(0)

    # Standardize manually.
    X_std = (X - X.mean()) / X.std().replace(0, np.nan)
    X_std = X_std.fillna(0).values

    candidate_indices = []

    method = "ruptures_pelt_rbf" if RUPTURES_AVAILABLE else "fallback_top_daily_jumps"

    if RUPTURES_AVAILABLE and len(daily) > 100:
        try:
            algo = rpt.Pelt(model="rbf").fit(X_std)
            cps = algo.predict(pen=8)

            # Remove final endpoint.
            candidate_indices = [cp for cp in cps if cp < len(daily)]
        except Exception:
            method = "fallback_top_daily_jumps"
            candidate_indices = []

    if not candidate_indices:
        # Fallback: largest one-day changes in aggregate weak-supervision score.
        jump = daily["mean_weak_supervision_score"].diff().abs()
        candidate_indices = list(jump.sort_values(ascending=False).head(12).index)

    rows = []

    for idx in candidate_indices:
        if idx <= 0 or idx >= len(daily):
            continue

        date = daily.loc[idx, "date"]

        before = daily.iloc[max(0, idx - 7):idx]
        after = daily.iloc[idx:min(len(daily), idx + 7)]

        if before.empty or after.empty:
            continue

        weak_before = before["mean_weak_supervision_score"].mean()
        weak_after = after["mean_weak_supervision_score"].mean()
        anomaly_before = before["mean_anomaly_ensemble_score"].mean()
        anomaly_after = after["mean_anomaly_ensemble_score"].mean()
        absret_before = before["mean_abs_log_return"].mean()
        absret_after = after["mean_abs_log_return"].mean()

        nearest_id, nearest_type, distance_days = nearest_incident(date, incidents)

        rows.append({
            "change_point_date": date.date(),
            "method": method,
            "weak_score_mean_before_7d": weak_before,
            "weak_score_mean_after_7d": weak_after,
            "weak_score_delta_after_minus_before": weak_after - weak_before,
            "anomaly_score_mean_before_7d": anomaly_before,
            "anomaly_score_mean_after_7d": anomaly_after,
            "anomaly_score_delta_after_minus_before": anomaly_after - anomaly_before,
            "abs_return_mean_before_7d": absret_before,
            "abs_return_mean_after_7d": absret_after,
            "abs_return_delta_after_minus_before": absret_after - absret_before,
            "nearest_event_id": nearest_id,
            "nearest_event_type": nearest_type,
            "days_to_nearest_event": distance_days,
            "within_14d_of_incident": bool(pd.notna(distance_days) and distance_days <= 14),
            "claim_boundary": "Change points are structural-break candidates, not proof that incidents caused the break.",
        })

    out = pd.DataFrame(rows)

    if not out.empty:
        out = out.sort_values(
            ["within_14d_of_incident", "weak_score_delta_after_minus_before"],
            ascending=[False, False],
        ).reset_index(drop=True)

    # Figure.
    plt.figure(figsize=(12, 5))
    plt.plot(daily["date"], daily["mean_weak_supervision_score"], label="mean weak-supervision score")

    if not out.empty:
        cp_dates = pd.to_datetime(out["change_point_date"])
        cp_values = daily.set_index("date").reindex(cp_dates)["mean_weak_supervision_score"]
        plt.scatter(cp_dates, cp_values, s=20, label="candidate change point")

    event_days = daily[daily["max_weak_label_7d"] == 1]
    plt.scatter(event_days["date"], event_days["mean_weak_supervision_score"], s=8, label="event-window day")

    plt.title("Change-point candidates in aggregate risk score")
    plt.xlabel("Date")
    plt.ylabel("Mean weak-supervision score")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHANGEPOINT_FIGURE_PATH, dpi=200)
    plt.close()

    return out


def evt_tail_risk(panel):
    df = panel.copy()
    df["asset"] = df["asset"].astype(str).str.upper()

    variables = [
        ("abs_log_return", "absolute daily log return"),
        ("intraday_range", "intraday range divided by close"),
        ("stablecoin_peg_deviation", "absolute stablecoin peg deviation"),
    ]

    rows = []

    for asset, sub in df.groupby("asset"):
        for var, definition in variables:
            if var not in sub.columns:
                continue

            x = pd.to_numeric(sub[var], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()

            # Peg deviation only meaningful for stablecoins.
            if var == "stablecoin_peg_deviation" and asset not in ["USDC", "USDT"]:
                continue

            if len(x) < 100 or x.nunique() <= 5:
                rows.append({
                    "asset": asset,
                    "tail_variable": var,
                    "definition": definition,
                    "n_obs": len(x),
                    "threshold_quantile": 0.95,
                    "threshold_value": np.nan,
                    "n_exceedances": 0,
                    "exceedance_rate": np.nan,
                    "gpd_shape": np.nan,
                    "gpd_scale": np.nan,
                    "empirical_q99": x.quantile(0.99) if len(x) > 0 else np.nan,
                    "evt_var_99": np.nan,
                    "evt_expected_shortfall_99": np.nan,
                    "weak_label_7d_rate_among_exceedances": np.nan,
                    "status": "insufficient_variation",
                    "claim_boundary": "EVT estimates require sufficient tail variation and are not incident attribution.",
                })
                continue

            threshold = x.quantile(0.95)
            exceed = x[x > threshold]
            excess = exceed - threshold

            if len(excess) < 20:
                status = "too_few_exceedances"
                shape = np.nan
                scale = np.nan
                evt_var_99 = np.nan
                evt_es_99 = np.nan
            else:
                try:
                    shape, loc, scale = genpareto.fit(excess, floc=0)
                    p_excess = (0.99 - 0.95) / (1 - 0.95)
                    evt_var_99 = threshold + genpareto.ppf(p_excess, shape, loc=0, scale=scale)

                    if shape < 1:
                        evt_es_99 = threshold + (scale + shape * (evt_var_99 - threshold)) / (1 - shape)
                    else:
                        evt_es_99 = np.nan

                    status = "completed"
                except Exception:
                    shape = np.nan
                    scale = np.nan
                    evt_var_99 = np.nan
                    evt_es_99 = np.nan
                    status = "fit_failed"

            exceed_dates = set(sub.loc[pd.to_numeric(sub[var], errors="coerce") > threshold, "date"])

            if "weak_label_7d" in sub.columns and exceed_dates:
                weak_rate = sub.loc[sub["date"].isin(exceed_dates), "weak_label_7d"].mean()
            else:
                weak_rate = np.nan

            rows.append({
                "asset": asset,
                "tail_variable": var,
                "definition": definition,
                "n_obs": len(x),
                "threshold_quantile": 0.95,
                "threshold_value": threshold,
                "n_exceedances": len(excess),
                "exceedance_rate": len(excess) / len(x),
                "gpd_shape": shape,
                "gpd_scale": scale,
                "empirical_q99": x.quantile(0.99),
                "evt_var_99": evt_var_99,
                "evt_expected_shortfall_99": evt_es_99,
                "weak_label_7d_rate_among_exceedances": weak_rate,
                "status": status,
                "claim_boundary": "EVT/POT tail risk is a statistical stress diagnostic, not proof of manipulation or fraud.",
            })

    out = pd.DataFrame(rows)

    # Figure: EVT thresholds for abs_log_return.
    plot_data = out[
        (out["tail_variable"] == "abs_log_return")
        & (out["status"] == "completed")
    ].copy()

    if not plot_data.empty:
        plt.figure(figsize=(10, 5))
        plt.bar(plot_data["asset"], plot_data["threshold_value"])
        plt.title("EVT/POT 95% thresholds for absolute log returns")
        plt.xlabel("Asset")
        plt.ylabel("95% threshold")
        plt.tight_layout()
        plt.savefig(EVT_FIGURE_PATH, dpi=200)
        plt.close()
    else:
        plt.figure(figsize=(10, 5))
        plt.text(0.1, 0.5, "No completed EVT threshold estimates.")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(EVT_FIGURE_PATH, dpi=200)
        plt.close()

    return out


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing blockchain_risk_panel_weak_supervision.csv. Run 08_weak_supervision_label_model.py first.")

    panel = pd.read_csv(INPUT_PATH)
    panel["date"] = pd.to_datetime(panel["date"])

    if INCIDENT_PATH.exists():
        incidents = pd.read_csv(INCIDENT_PATH)
    else:
        incidents = pd.DataFrame()

    spillover = spillover_connectedness(panel)
    changepoints = change_point_timeline(panel, incidents)
    evt = evt_tail_risk(panel)

    spillover.to_csv(SPILLOVER_PATH, index=False)
    changepoints.to_csv(CHANGEPOINT_PATH, index=False)
    evt.to_csv(EVT_PATH, index=False)

    print("Saved spillover connectedness table to:")
    print(SPILLOVER_PATH)
    print()
    print(spillover.head(20))

    print()
    print("Saved change-point timeline table to:")
    print(CHANGEPOINT_PATH)
    print()
    print(changepoints.head(20))

    print()
    print("Saved EVT tail-risk table to:")
    print(EVT_PATH)
    print()
    print(evt.head(30))

    print()
    print("Saved figures:")
    print(SPILLOVER_FIGURE_PATH)
    print(CHANGEPOINT_FIGURE_PATH)
    print(EVT_FIGURE_PATH)


if __name__ == "__main__":
    main()
