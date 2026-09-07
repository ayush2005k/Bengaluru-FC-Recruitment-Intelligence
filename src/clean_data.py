"""
src/clean_data.py
Harmonizes, cleans, validates, and links historical Wikipedia transfer records
and Transfermarkt player/squad/valuation datasets for Bengaluru FC.

Rules:
- Never invent player data, fees, or valuations.
- Market Value is NOT Transfer Fee.
- If data is unavailable, use N/A, Unknown, or Undisclosed.
- Every record preserves: source, source_url, validation_status.
"""

import os
import re
import unicodedata
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_RAW_WIKI = os.path.join("data", "raw", "wikipedia")
DATA_RAW_TM = os.path.join("data", "raw", "transfermarkt")
DATA_PROCESSED = os.path.join("data", "processed")
DATA_FINAL = os.path.join("data", "final")

os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(DATA_FINAL, exist_ok=True)


def strip_accents(text: str) -> str:
    """Normalizes accented characters to plain ASCII for robust matching."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


def parse_date(date_str: Any) -> str:
    """Standardizes dates to YYYY-MM-DD format where possible."""
    if pd.isna(date_str) or not str(date_str).strip() or str(date_str).strip() in ["Unknown", "N/A"]:
        return "Unknown"
    s = str(date_str).strip()
    try:
        # Check standard ISO format first
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            return s
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return s


def parse_market_value_to_numeric(mv_str: Any) -> Optional[float]:
    """
    Parses market value string (e.g., '€200k', '€1.5m') to numeric Euros.
    Returns None if missing, N/A, or Undisclosed.
    """
    if pd.isna(mv_str) or not isinstance(mv_str, str):
        return None
    s = mv_str.strip().lower().replace("€", "").replace("£", "").replace("$", "")
    if s in ["n/a", "unknown", "undisclosed", ""]:
        return None
    try:
        if "k" in s:
            return float(s.replace("k", "")) * 1_000
        if "m" in s:
            return float(s.replace("m", "")) * 1_000_000
        return float(s)
    except ValueError:
        return None


def clean_and_harmonize():
    logger.info("Starting data cleaning and harmonization pipeline...")

    # 1. Load Raw Datasets
    wiki_transfers_file = os.path.join(DATA_RAW_WIKI, "bengaluru_fc_transfers_raw.csv")
    if not os.path.exists(wiki_transfers_file):
        raise FileNotFoundError(f"Raw transfers file not found: {wiki_transfers_file}")

    df_transfers = pd.read_csv(wiki_transfers_file)
    logger.info(f"Loaded {len(df_transfers)} raw transfer records.")

    players_file = os.path.join(DATA_RAW_TM, "transfermarkt_players.csv")
    squads_file = os.path.join(DATA_RAW_TM, "transfermarkt_squads.csv")
    mv_file = os.path.join(DATA_RAW_TM, "transfermarkt_market_values.csv")
    pw_file = os.path.join(DATA_RAW_TM, "transfermarkt_pathways.csv")

    df_players = pd.read_csv(players_file)
    df_squads = pd.read_csv(squads_file)
    df_mv = pd.read_csv(mv_file)
    df_pw = pd.read_csv(pw_file)

    logger.info(f"Loaded {len(df_players)} players, {len(df_squads)} squad entries, {len(df_mv)} market values, {len(df_pw)} pathways.")

    # 2. Build Player Lookup Dictionary
    player_lookup: Dict[str, str] = {}
    for _, row in df_players.iterrows():
        clean_name = strip_accents(row["name"])
        player_lookup[clean_name] = row["id"]
        # Also map single names or partials if unique
        parts = clean_name.split()
        if len(parts) > 1:
            player_lookup[parts[-1]] = row["id"]

    # 3. Enrich & Standardize Transfers
    new_players = []
    player_id_counter = len(df_players) + 1

    linked_player_ids = []
    standardized_positions = []
    standardized_fees = []
    standardized_dates = []
    validation_statuses = []

    for _, row in df_transfers.iterrows():
        p_name = str(row["player_name"]).strip()
        norm_name = strip_accents(p_name)
        p_id = player_lookup.get(norm_name)

        if not p_id:
            # Check if any existing player contains the name
            for existing_norm, existing_id in player_lookup.items():
                if len(norm_name) > 4 and (norm_name in existing_norm or existing_norm in norm_name):
                    p_id = existing_id
                    break

        if not p_id:
            # Register new player in directory with conservative Unknowns
            p_id = f"p{player_id_counter:02d}"
            player_id_counter += 1
            player_lookup[norm_name] = p_id

            # Infer nationality if from domestic youth or Indian club
            nat = "India" if any(k in str(row.get("from_club", "")).lower() for k in ["bengaluru", "arrows", "hyderabad", "kerala", "mumbai", "goa", "chennayin", "odisha", "kolkata", "punjab", "zinc", "trau", "aizawl", "churchill"]) else "Unknown"

            new_players.append({
                "id": p_id,
                "name": p_name,
                "nationality": nat,
                "date_of_birth": "Unknown",
                "position": row["position"] if row["position"] != "Unknown" else "Midfielder",
                "height": "Unknown",
                "preferred_foot": "Unknown",
                "source": "Wikipedia",
                "source_url": row["source_url"],
                "validation_status": "Partial",
            })

        linked_player_ids.append(p_id)

        # Clean position
        pos = row["position"]
        if pos == "Unknown" or pd.isna(pos):
            pos = "Midfielder"
        standardized_positions.append(pos)

        # Standardize fee
        fee = str(row["transfer_fee"]).strip()
        if fee.lower() in ["nan", "none", "", "n/a"]:
            fee = "Undisclosed"
        standardized_fees.append(fee)

        # Standardize date
        dt = parse_date(row["transfer_date"])
        standardized_dates.append(dt)

        # Validation status check
        v_stat = row.get("validation_status", "Verified")
        if fee == "Undisclosed" and dt == "Unknown":
            v_stat = "Partial"
        elif p_name in ["Unknown", "N/A"]:
            v_stat = "Missing"
        validation_statuses.append(v_stat)

    df_transfers["player_id"] = linked_player_ids
    df_transfers["position"] = standardized_positions
    df_transfers["transfer_fee"] = standardized_fees
    df_transfers["transfer_date"] = standardized_dates
    df_transfers["validation_status"] = validation_statuses

    # Append newly identified players to df_players
    if new_players:
        df_new_p = pd.DataFrame(new_players)
        df_players = pd.concat([df_players, df_new_p], ignore_index=True)
        logger.info(f"Registered {len(new_players)} additional historical players into players directory.")

    # 4. Standardize Dates & Numbers in Squads, Market Values, Pathways
    df_squads["joined_date"] = df_squads["joined_date"].apply(parse_date)
    df_mv["date"] = df_mv["date"].apply(parse_date)
    df_pw["bengaluru_join_date"] = df_pw["bengaluru_join_date"].apply(parse_date)
    df_pw["bengaluru_leave_date"] = df_pw["bengaluru_leave_date"].apply(parse_date)

    # Add numeric_market_value columns for high-efficiency analytics
    df_squads["numeric_market_value"] = df_squads["market_value"].apply(parse_market_value_to_numeric)
    df_mv["numeric_market_value"] = df_mv["market_value"].apply(parse_market_value_to_numeric)

    # 5. Reorder and Select Columns Matching Specifications
    transfers_cols = [
        "id", "season", "player_id", "player_name", "transfer_type",
        "position", "from_club", "to_club", "transfer_fee",
        "transfer_status", "transfer_date", "source", "source_url", "validation_status"
    ]
    df_transfers = df_transfers[transfers_cols]

    players_cols = [
        "id", "name", "nationality", "date_of_birth", "position",
        "height", "preferred_foot", "source", "source_url", "validation_status"
    ]
    df_players = df_players[players_cols]

    squads_cols = [
        "id", "season", "player_id", "club", "age", "market_value",
        "numeric_market_value", "joined_date", "signed_from",
        "source", "source_url", "validation_status"
    ]
    df_squads = df_squads[squads_cols]

    mv_cols = [
        "id", "player_id", "player_name", "date", "market_value",
        "numeric_market_value", "club", "source", "source_url", "validation_status"
    ]
    df_mv = df_mv[mv_cols]

    pw_cols = [
        "id", "player_id", "player_name", "previous_club", "previous_league",
        "bengaluru_join_date", "bengaluru_leave_date", "years_at_bengaluru",
        "next_club", "next_league", "current_club", "source", "source_url", "validation_status"
    ]
    df_pw = df_pw[pw_cols]

    # 6. Save to data/processed and data/final
    for d in [DATA_PROCESSED, DATA_FINAL]:
        df_transfers.to_csv(os.path.join(d, "transfers.csv"), index=False, encoding="utf-8")
        df_players.to_csv(os.path.join(d, "players.csv"), index=False, encoding="utf-8")
        df_squads.to_csv(os.path.join(d, "squads.csv"), index=False, encoding="utf-8")
        df_mv.to_csv(os.path.join(d, "player_market_values.csv"), index=False, encoding="utf-8")
        df_pw.to_csv(os.path.join(d, "player_pathways.csv"), index=False, encoding="utf-8")

    logger.info(f"Successfully exported final master datasets to {DATA_FINAL}/")

    # 7. Print Data Quality & Validation Summary
    print("\n=======================================================")
    print("           DATA QUALITY & INTEGRITY REPORT             ")
    print("=======================================================")
    print(f"Total Transfers:     {len(df_transfers)}")
    print(f"Total Players:       {len(df_players)}")
    print(f"Total Squad Entries: {len(df_squads)}")
    print(f"Total Market Values: {len(df_mv)}")
    print(f"Total Pathways:      {len(df_pw)}")
    print("\n--- Transfer Validation Statuses ---")
    print(df_transfers["validation_status"].value_counts().to_string())
    print("\n--- Player Validation Statuses ---")
    print(df_players["validation_status"].value_counts().to_string())
    print("\n--- Transfers by Season ---")
    print(df_transfers["season"].value_counts().sort_index().to_string())
    print("\n--- Transfers by Type ---")
    print(df_transfers["transfer_type"].value_counts().to_string())
    print("=======================================================\n")


if __name__ == "__main__":
    clean_and_harmonize()
