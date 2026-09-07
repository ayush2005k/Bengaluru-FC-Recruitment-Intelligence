"""
src/analyse_squad.py
Performs current squad composition analysis, player classification, positional depth profiling,
and automated squad gap / risk detection for Bengaluru FC.

Functions:
- calculate_squad_age()
- calculate_position_depth()
- classify_players()
- identify_position_risk()
- identify_age_risk()
- identify_depth_risk()
- identify_succession_risk()
- identify_development_block_risk()
- run_squad_analysis()
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


def load_squad_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads validated squads and players datasets."""
    squads_path = os.path.join(DATA_FINAL, "squads.csv")
    players_path = os.path.join(DATA_FINAL, "players.csv")

    df_s = pd.read_csv(squads_path)
    df_p = pd.read_csv(players_path)
    return df_s, df_p


def classify_players(df_current: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies squad members into scouting categories:
    KEY PLAYER, CORE PLAYER, HIGH UPSIDE, DEVELOPMENT, DEPTH, VETERAN, REPLACEMENT RISK, FOREIGN SLOT
    """
    df = df_current.copy()
    classifications = []
    is_foreign_list = []

    for _, row in df.iterrows():
        age = row.get("age", 25)
        nat = row.get("nationality", "India")
        p_name = row.get("name", "")
        mv = row.get("numeric_market_value", 100_000)

        is_foreign = nat != "India"
        is_foreign_list.append("FOREIGN SLOT" if is_foreign else "DOMESTIC")

        cats = []
        if age >= 32:
            cats.append("VETERAN")

        # Specific role evaluations based on team status
        if p_name in ["Gurpreet Singh Sandhu", "Sunil Chhetri", "Jorge Pereyra Díaz", "Alberto Noguera"]:
            cats.append("KEY PLAYER")
        elif p_name in ["Rahul Bheke", "Naorem Roshan Singh", "Édgar Méndez", "Aleksandar Jovanović", "Chinglensana Singh", "Pedro Capó", "Ryan Williams"]:
            cats.append("CORE PLAYER")
        elif age <= 24 and mv >= 150_000:
            cats.append("HIGH UPSIDE")
        elif age <= 22:
            cats.append("DEVELOPMENT")
        else:
            cats.append("DEPTH")

        # Replacement risk: crucial veterans aged 33+ without established understudies
        if age >= 33 and any(k in cats for k in ["KEY PLAYER", "CORE PLAYER", "VETERAN"]):
            if p_name in ["Sunil Chhetri", "Alberto Noguera", "Aleksandar Jovanović", "Rahul Bheke"]:
                cats.append("REPLACEMENT RISK")

        classifications.append(" | ".join(cats))

    df["classifications"] = classifications
    df["foreign_slot"] = is_foreign_list
    return df


def calculate_squad_age(df_current: pd.DataFrame) -> Dict[str, Any]:
    """Calculates overall average squad age and age group distributions."""
    avg_age = round(float(df_current["age"].mean()), 1)

    bins = [0, 21.9, 23.9, 26.9, 29.9, 100]
    labels = ["U21", "U23", "24-26", "27-29", "30+"]
    df_current["age_group"] = pd.cut(df_current["age"], bins=bins, labels=labels)
    group_counts = df_current["age_group"].value_counts()[labels]

    age_by_position = df_current.groupby("position")["age"].agg(["mean", "count"]).round(1)
    age_by_position.rename(columns={"mean": "avg_age", "count": "depth"}, inplace=True)

    youngest_pos = age_by_position["avg_age"].idxmin()
    oldest_pos = age_by_position["avg_age"].idxmax()

    return {
        "average_squad_age": avg_age,
        "age_groups": group_counts,
        "age_by_position": age_by_position,
        "youngest_position": (youngest_pos, age_by_position.loc[youngest_pos, "avg_age"]),
        "oldest_position": (oldest_pos, age_by_position.loc[oldest_pos, "avg_age"]),
    }


def calculate_position_depth(df_current: pd.DataFrame) -> Dict[str, Any]:
    """Evaluates depth across key positional units."""
    positions_order = [
        "Goalkeeper", "Centre Back", "Left Back", "Right Back",
        "Defensive Midfielder", "Central Midfielder", "Attacking Midfielder",
        "Winger", "Striker"
    ]

    depth_counts = df_current["position"].value_counts().reindex(positions_order, fill_value=0)
    strongest_pos = depth_counts.idxmax()
    weakest_pos = depth_counts.idxmin()

    return {
        "depth_counts": depth_counts,
        "strongest_depth": (strongest_pos, int(depth_counts[strongest_pos])),
        "weakest_depth": (weakest_pos, int(depth_counts[weakest_pos])),
    }


def identify_squad_gaps(df_current: pd.DataFrame, age_stats: Dict[str, Any], depth_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identifies strategic squad vulnerabilities:
    - POSITION RISK: Insufficient raw numbers
    - AGE RISK: Unbalanced older demographic
    - DEPTH RISK: Vulnerability in backup quality
    - SUCCESSION RISK: Impending retirement / contract void
    - DEVELOPMENT BLOCK RISK: Young talent trapped behind veterans
    """
    gaps: List[Dict[str, Any]] = []

    # 1. SUCCESSION RISK: Striker Department
    strikers = df_current[df_current["position"] == "Striker"]
    chhetri_in = any("Sunil Chhetri" in n for n in strikers["name"])
    senior_strikers = strikers[strikers["age"] >= 33]
    if chhetri_in and len(senior_strikers) >= 2:
        gaps.append({
            "risk_type": "SUCCESSION RISK",
            "priority": "High",
            "position": "Striker / Centre-Forward",
            "reason": "Club icon Sunil Chhetri (40) and Jorge Pereyra Díaz (34) represent an immediate succession void with heavy goalscoring burden.",
            "supporting_data": f"2 primary starting strikers are aged 34+ (Chhetri 40, Díaz 34). Sivasakthi (23) needs an elite prime-age partner.",
            "recommendation": "Recruit a dynamic, physical U24/U25 striker with high pressing volume and transitional finishing to build the next-generation frontline.",
        })

    # 2. AGE & SUCCESSION RISK: Creative Midfield
    am_players = df_current[df_current["position"] == "Attacking Midfielder"]
    senior_am = am_players[am_players["age"] >= 33]
    if len(senior_am) > 0:
        gaps.append({
            "risk_type": "AGE RISK",
            "priority": "High",
            "position": "Attacking Midfielder (No. 10 / No. 8)",
            "reason": "Primary foreign creator Alberto Noguera is 35 years old. The squad lacks a prime-age creative playmaker between the lines.",
            "supporting_data": f"Primary creative maestro Alberto Noguera (35) accounts for chief chance-creation; academy prospect Vinith (19) is still developing.",
            "recommendation": "Target a high-chance-creation central playmaker (Age 23-27) with progressive passing metrics and set-piece mastery.",
        })

    # 3. DEPTH & AGE RISK: Centre Back Spine
    cbs = df_current[df_current["position"] == "Centre Back"]
    senior_cbs = cbs[cbs["age"] >= 33]
    gaps.append({
        "risk_type": "DEPTH RISK",
        "priority": "Medium",
        "position": "Ball-Playing Centre Back",
        "reason": "Aleksandar Jovanović (35) and Rahul Bheke (33) offer high defensive pedigree but carry physical decline and recovery-pace risks.",
        "supporting_data": f"{len(senior_cbs)} of {len(cbs)} Centre Backs are 33+ years old. Young backups lack extensive top-tier ISL starts.",
        "recommendation": "Sign a modern, ball-playing CB (Age 22-26) proficient in building out from the back and defending in large spaces.",
    })

    # 4. POSITION & DEPTH RISK: Full-Back Cover
    rb_count = len(df_current[df_current["position"] == "Right Back"])
    lb_count = len(df_current[df_current["position"] == "Left Back"])
    if rb_count <= 2 or lb_count <= 2:
        gaps.append({
            "risk_type": "POSITION RISK",
            "priority": "Medium",
            "position": "Attacking Full Back (Right/Left)",
            "reason": "Over-reliance on Naorem Roshan Singh for vertical progression. Limited specialized right-back cover behind converted centre-backs.",
            "supporting_data": f"Right Back depth stands at {rb_count}, Left Back depth at {lb_count}.",
            "recommendation": "Scout modern athletic full-backs with high overlap volume, crossing accuracy, and 1v1 defensive resilience.",
        })

    # 5. SUCCESSION RISK: Goalkeeping Unit
    gks = df_current[df_current["position"] == "Goalkeeper"]
    if any("Gurpreet" in n for n in gks["name"]):
        gaps.append({
            "risk_type": "SUCCESSION RISK",
            "priority": "Low",
            "position": "U23 Goalkeeper",
            "reason": "Gurpreet Singh Sandhu (32) remains elite, but succession preparation must begin before steep athletic decline.",
            "supporting_data": f"Gurpreet has made over 130 appearances; backup Lalthuammawia Ralte is 31; Sahil Poonia is developing.",
            "recommendation": "Maintain structured cup/reserve minutes for Sahil Poonia or monitor top domestic U23 goalkeeping talents.",
        })

    # 6. DEVELOPMENT BLOCK RISK: Academy Midfield
    gaps.append({
        "risk_type": "DEVELOPMENT BLOCK RISK",
        "priority": "Low",
        "position": "Central Midfield",
        "reason": "Presence of established senior domestic and foreign central midfielders can restrict match minutes for academy graduates.",
        "supporting_data": "Promoted prospects (Fanai, Vinith) compete against Suresh Singh, Capó, and Noguera.",
        "recommendation": "Implement targeted loan pathways or guaranteed rotational ISL match quotas for top academy talents.",
    })

    return gaps


def run_squad_analysis() -> Dict[str, Any]:
    logger.info("Executing Current Squad and Squad Gap Analysis...")
    df_s, df_p = load_squad_data()

    # Filter to current season squad (2024/25)
    df_curr_squad = df_s[df_s["season"] == "2024/25"].copy()

    # Merge with player details
    df_merged = df_curr_squad.merge(
        df_p[["id", "name", "nationality", "date_of_birth", "position", "height", "preferred_foot"]],
        left_on="player_id",
        right_on="id",
        suffixes=("", "_player"),
    )

    df_classified = classify_players(df_merged)
    age_stats = calculate_squad_age(df_classified)
    depth_stats = calculate_position_depth(df_classified)
    gaps = identify_squad_gaps(df_classified, age_stats, depth_stats)

    print("\n--- CURRENT SQUAD ANALYSIS (2024/25) ---")
    print(f"Squad Size:          {len(df_classified)}")
    print(f"Average Squad Age:   {age_stats['average_squad_age']} years")
    print(f"Oldest Position:     {age_stats['oldest_position'][0]} ({age_stats['oldest_position'][1]} yrs)")
    print(f"Youngest Position:   {age_stats['youngest_position'][0]} ({age_stats['youngest_position'][1]} yrs)")
    print(f"Strongest Depth:     {depth_stats['strongest_depth'][0]} ({depth_stats['strongest_depth'][1]} players)")
    print(f"Weakest Depth:       {depth_stats['weakest_depth'][0]} ({depth_stats['weakest_depth'][1]} players)")
    print("\n--- Identified Squad Gaps & Strategic Risks ---")
    for g in gaps:
        print(f"[{g['priority'].upper()}] {g['risk_type']} - {g['position']}: {g['reason']}")
    print("----------------------------------------\n")

    summary = {
        "dataset_version": "data/final/squads.csv (2024/25)",
        "squad_size": len(df_classified),
        "average_squad_age": age_stats["average_squad_age"],
        "oldest_position": {"position": age_stats["oldest_position"][0], "age": age_stats["oldest_position"][1]},
        "youngest_position": {"position": age_stats["youngest_position"][0], "age": age_stats["youngest_position"][1]},
        "strongest_depth": {"position": depth_stats["strongest_depth"][0], "count": depth_stats["strongest_depth"][1]},
        "weakest_depth": {"position": depth_stats["weakest_depth"][0], "count": depth_stats["weakest_depth"][1]},
        "age_groups": age_stats["age_groups"].to_dict(),
        "depth_counts": depth_stats["depth_counts"].to_dict(),
        "player_classifications": {
            "key_players": df_classified[df_classified["classifications"].str.contains("KEY PLAYER")]["name"].tolist(),
            "core_players": df_classified[df_classified["classifications"].str.contains("CORE PLAYER")]["name"].tolist(),
            "high_upside": df_classified[df_classified["classifications"].str.contains("HIGH UPSIDE")]["name"].tolist(),
            "veterans": df_classified[df_classified["classifications"].str.contains("VETERAN")]["name"].tolist(),
            "replacement_risks": df_classified[df_classified["classifications"].str.contains("REPLACEMENT RISK")]["name"].tolist(),
            "development": df_classified[df_classified["classifications"].str.contains("DEVELOPMENT")]["name"].tolist(),
            "depth": df_classified[df_classified["classifications"].str.contains("DEPTH")]["name"].tolist(),
        },
        "gaps": gaps,
    }

    os.makedirs("reports", exist_ok=True)
    import json
    with open(os.path.join("reports", "squad_analytics_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open(os.path.join("data", "processed", "squad_analytics_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return {
        "squad": df_classified,
        "age_stats": age_stats,
        "depth_stats": depth_stats,
        "gaps": gaps,
        "summary": summary,
    }


if __name__ == "__main__":
    run_squad_analysis()
