"""
src/analyse_market_value.py
Performs player market value trajectory analysis, portfolio development calculations,
and career pathway tracking for Bengaluru FC.

Rules:
- Never mix Market Value and Transfer Fee.
- Market Value is an estimated economic asset valuation.
- Transfer Fee is a realized inter-club transaction price.
- Formula: ((Current Value - Initial Value) / Initial Value) * 100
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_FINAL = os.path.join("data", "final")


def load_market_datasets() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads validated market values, pathways, and players datasets."""
    mv_path = os.path.join(DATA_FINAL, "player_market_values.csv")
    pw_path = os.path.join(DATA_FINAL, "player_pathways.csv")
    p_path = os.path.join(DATA_FINAL, "players.csv")

    df_mv = pd.read_csv(mv_path)
    df_pw = pd.read_csv(pw_path)
    df_p = pd.read_csv(p_path)
    return df_mv, df_pw, df_p


def calculate_market_value_growth() -> pd.DataFrame:
    """
    Computes initial joined value, peak value, leaving value, current value,
    absolute value growth, and percentage growth for tracked players.
    """
    df_mv, _, _ = load_market_datasets()

    # Sort chronologically
    df_mv["date"] = pd.to_datetime(df_mv["date"])
    df_mv_sorted = df_mv.sort_values(by=["player_id", "date"]).copy()

    records = []
    for p_id, group in df_mv_sorted.groupby("player_id"):
        p_name = group["player_name"].iloc[0]

        # Initial joined value (earliest recorded valuation upon signing)
        initial_val = group["numeric_market_value"].iloc[0]
        # Peak valuation during tenure
        peak_val = group["numeric_market_value"].max()
        # Current or latest valuation
        current_val = group["numeric_market_value"].iloc[-1]

        # Leaving value (if player departed Bengaluru FC, else current)
        leaving_val = current_val

        # Absolute growth in Euros
        abs_growth = current_val - initial_val

        # Percentage growth: ((Current - Initial) / Initial) * 100
        pct_growth = round(((current_val - initial_val) / initial_val) * 100, 1) if initial_val > 0 else 0.0

        records.append({
            "player_id": p_id,
            "player_name": p_name,
            "initial_value_eur": initial_val,
            "peak_value_eur": peak_val,
            "current_value_eur": current_val,
            "leaving_value_eur": leaving_val,
            "absolute_growth_eur": abs_growth,
            "growth_percentage": pct_growth,
            "initial_formatted": f"€{int(initial_val/1000)}k",
            "peak_formatted": f"€{int(peak_val/1000)}k",
            "current_formatted": f"€{int(current_val/1000)}k",
        })

    df_growth = pd.DataFrame(records)
    df_growth.sort_values(by="absolute_growth_eur", ascending=False, inplace=True)
    return df_growth


def analyze_player_pathways() -> pd.DataFrame:
    """
    Structures and enriches career trajectories:
    Previous Club -> Bengaluru FC -> Next Club
    """
    _, df_pw, _ = load_market_datasets()
    df = df_pw.copy()

    # Calculate status and tenure
    df["career_pathway"] = df.apply(
        lambda r: f"{r['previous_club']} ({r['previous_league']}) -> Bengaluru FC -> {r['next_club'] if r['next_club'] != 'N/A' else 'Active Squad'}",
        axis=1,
    )
    return df


def run_market_value_analysis() -> Dict[str, Any]:
    logger.info("Executing Market Value & Career Pathway Analysis...")
    df_growth = calculate_market_value_growth()
    df_pathways = analyze_player_pathways()

    top_gainers = df_growth[df_growth["absolute_growth_eur"] > 0].head(5)
    top_declines = df_growth[df_growth["absolute_growth_eur"] < 0].sort_values(by="absolute_growth_eur").head(5)

    print("\n--- MARKET VALUE GROWTH & PLAYER DEVELOPMENT ---")
    print("TOP VALUE GROWTH PLAYERS:")
    for _, r in top_gainers.iterrows():
        print(f"  {r['player_name']}: {r['initial_formatted']} -> {r['current_formatted']} (+{r['growth_percentage']}%, Peak: {r['peak_formatted']})")

    print("\nTOP VALUE DECLINES (VETERANS / AGE CURVE):")
    for _, r in top_declines.iterrows():
        print(f"  {r['player_name']}: {r['initial_formatted']} -> {r['current_formatted']} ({r['growth_percentage']}%)")

    print("\n--- SAMPLE PLAYER PATHWAYS ---")
    for _, r in df_pathways.head(5).iterrows():
        print(f"  {r['player_name']}: {r['career_pathway']} [Tenure: {r['years_at_bengaluru']} yrs]")
    summary = {
        "dataset_version": "data/final/player_market_values.csv & data/final/player_pathways.csv",
        "tracked_players_count": len(df_growth),
        "top_value_growth_players": top_gainers[[
            "player_id", "player_name", "initial_formatted", "current_formatted", "peak_formatted", "growth_percentage", "absolute_growth_eur"
        ]].to_dict(orient="records"),
        "top_value_decline_players": top_declines[[
            "player_id", "player_name", "initial_formatted", "current_formatted", "peak_formatted", "growth_percentage", "absolute_growth_eur"
        ]].to_dict(orient="records"),
        "pathways_tracked_count": len(df_pathways),
    }

    os.makedirs("reports", exist_ok=True)
    import json
    with open(os.path.join("reports", "market_value_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open(os.path.join("data", "processed", "market_value_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return {
        "growth": df_growth,
        "pathways": df_pathways,
        "top_gainers": top_gainers,
        "top_declines": top_declines,
        "summary": summary,
    }


if __name__ == "__main__":
    run_market_value_analysis()
