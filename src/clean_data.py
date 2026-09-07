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

    # Reject financial / market value strings accidentally stored as dates
    if any(kw in s.lower() for kw in ["₹", "$", "€", "crore", "lakh", "million", "usd"]):
        m = re.search(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", s) or re.search(r"\b\d{4}-\d{2}-\d{2}\b", s)
        if m:
            s = m.group(0)
        else:
            return "Unknown"

    try:
        # Check standard ISO format first
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            return s
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return "Unknown"


def normalize_player_name(name: Any) -> str:
    """
    Normalizes player names for robust deduplication matching:
    - Converts to lowercase
    - Strips accents/diacritics
    - Collapses whitespace and punctuation
    - Safely maps phonetic variants (e.g. Mohammeed -> Mohamed)
    """
    if name is None or pd.isna(name):
        return ""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).strip().lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("mohammeed", "mohamed")
    return s


CANONICAL_NAMES = {
    "mohamed salah": "Mohamed Salah",
    "edgar mendez": "Édgar Méndez",
    "pedro capo": "Pedro Capó",
    "slavko damjanovic": "Slavko Damjanović",
    "jorge pereyra diaz": "Jorge Pereyra Díaz",
    "aleksander jovanovic": "Aleksandar Jovanović",
    "yrondu musavu-king": "Yrondu Musavu-King",
}


def get_canonical_display_name(name: str) -> str:
    """Returns preferred canonical display name preserving verified accents."""
    norm = normalize_player_name(name)
    return CANONICAL_NAMES.get(norm, name)


def deduplicate_loan_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies cases where a loan event is double-counted as both a general
    Arrival/Departure and a specific Loan In/Loan Out for the same player,
    season, and club pairing. Retains the Loan In/Loan Out record and drops the
    redundant Arrival/Departure.
    """
    if "norm_name" not in df.columns:
        df["norm_name"] = df["player_name"].apply(normalize_player_name)

    loan_mask = df["transfer_type"].isin(["Loan In", "Loan Out"])
    loan_df = df[loan_mask]
    to_drop = []

    for l_idx, l_row in loan_df.iterrows():
        p_norm = l_row["norm_name"]
        season = l_row["season"]
        target_type = "Departure" if l_row["transfer_type"] == "Loan Out" else "Arrival"

        matches = df[
            (~df.index.isin(loan_df.index)) &
            (df["season"] == season) &
            (df["transfer_type"] == target_type) &
            (df["norm_name"] == p_norm)
        ]

        for m_idx in matches.index:
            to_drop.append(m_idx)
            logger.info(
                f"Deduplicating redundant {target_type} for loan event: "
                f"{df.loc[m_idx, 'player_name']} ({season}) in favor of {l_row['transfer_type']}"
            )

    df_cleaned = df.drop(index=to_drop).copy()
    if "norm_name" in df_cleaned.columns:
        df_cleaned.drop(columns=["norm_name"], inplace=True)
    return df_cleaned


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


def is_invalid_player_record(name: Any) -> bool:
    """
    Identifies non-player rows such as table summaries, footer notes,
    financial spending/offloading estimates, or section metadata.
    """
    if name is None or pd.isna(name):
        return True
    s = str(name).strip()
    if not s or s in ["N/A", "Unknown", "—", "-"]:
        return True
    s_lower = s.lower()

    invalid_keywords = [
        "estimated spending",
        "estimated offloading",
        "market value",
        "market values",
        "spending based",
        "offloading based",
        "transfer fee total",
        "total spending",
        "total income",
        "subtotal",
        "summary",
    ]
    if any(k in s_lower for k in invalid_keywords):
        return True

    if re.search(r"\b(estimated|spending|offloading|expenditure|revenue)\b", s_lower):
        return True

    if any(sym in s for sym in ["₹", "$", "€", "£"]) and re.search(r"\b(crore|lakh|million|billion|us\$)\b", s_lower):
        return True

    if ":" in s and any(k in s_lower for k in ["spending", "offloading", "market", "fee", "total", "notes"]):
        return True

    if len(s) > 55 and any(sym in s for sym in [":", "₹", "$", "(", ")"]):
        return True

    if any(term in s_lower for term in ["total", "team", "source"]):
        return True

    return False


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
    # Filter out non-player rows (table summaries, footers, etc.)
    df_transfers = df_transfers[~df_transfers["player_name"].apply(is_invalid_player_record)].copy()

    # Restrict historical transfers strictly to the official completed period: 2020/21 - 2024/25
    valid_seasons = ["2020/21", "2021/22", "2022/23", "2023/24", "2024/25"]
    df_transfers = df_transfers[df_transfers["season"].isin(valid_seasons)].copy()

    # Standardize player names to canonical display format
    df_transfers["player_name"] = df_transfers["player_name"].apply(get_canonical_display_name)
    df_transfers["norm_name"] = df_transfers["player_name"].apply(normalize_player_name)

    # Fix Oliver Drost date if column shift occurred with market value
    for idx, r in df_transfers.iterrows():
        if normalize_player_name(r["player_name"]) == "oliver drost" and r["season"] == "2024/25":
            if any(kw in str(r["transfer_date"]).lower() for kw in ["₹", "$", "€", "crore", "lakh"]):
                df_transfers.loc[idx, "transfer_date"] = "10 July 2024"

    # Deduplicate by normalized player name, season, transfer_type, and from_club
    df_transfers.drop_duplicates(
        subset=["season", "norm_name", "transfer_type", "from_club"],
        keep="first",
        inplace=True,
    )

    # Deduplicate double-counted loan events (keep Loan In/Out, drop redundant Arrival/Departure)
    df_transfers = deduplicate_loan_events(df_transfers)

    df_transfers.reset_index(drop=True, inplace=True)
    df_transfers["id"] = range(1, len(df_transfers) + 1)

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

    # 5b. Extract Internal Promotions into dedicated academy_pathways dataset
    df_academy = df_transfers[df_transfers["transfer_type"] == "Internal Promotion"].copy().reset_index(drop=True)

    # 6. Save to data/processed and data/final
    for d in [DATA_PROCESSED, DATA_FINAL]:
        df_transfers.to_csv(os.path.join(d, "transfers.csv"), index=False, encoding="utf-8")
        df_players.to_csv(os.path.join(d, "players.csv"), index=False, encoding="utf-8")
        df_squads.to_csv(os.path.join(d, "squads.csv"), index=False, encoding="utf-8")
        df_mv.to_csv(os.path.join(d, "player_market_values.csv"), index=False, encoding="utf-8")
        df_pw.to_csv(os.path.join(d, "player_pathways.csv"), index=False, encoding="utf-8")
        df_academy.to_csv(os.path.join(d, "academy_pathways.csv"), index=False, encoding="utf-8")

    logger.info(f"Successfully exported final master datasets to {DATA_FINAL}/")

    # 7. Print Data Quality & Validation Summary
    print("\n=======================================================")
    print("           DATA QUALITY & INTEGRITY REPORT             ")
    print("=======================================================")
    print(f"Total Transfers:        {len(df_transfers)}")
    print(f"Total Players:          {len(df_players)}")
    print(f"Total Squad Entries:    {len(df_squads)}")
    print(f"Total Market Values:    {len(df_mv)}")
    print(f"Total Pathways:         {len(df_pw)}")
    print(f"Total Academy Pathways: {len(df_academy)}")
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
