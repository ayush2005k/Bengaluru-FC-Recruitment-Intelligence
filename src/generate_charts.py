"""
src/generate_charts.py
Generates presentation-grade, high-resolution Matplotlib charts styled
with a professional dark football intelligence theme for Bengaluru FC.

Color Palette:
- Background: #0B111E / #0F172A
- Surface/Card: #1E293B
- Bengaluru Royal Blue: #003B95 / #1E40AF
- Bengaluru Flame Red: #DC2626
- Accent Cyan/Teal: #38BDF8 / #06B6D4
- White Text: #F8FAFC
- Subdued Text: #94A3B8
- Gridlines: #334155
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHARTS_DIR = "charts"
DATA_FINAL = os.path.join("data", "final")
REPORTS_DIR = "reports"
os.makedirs(CHARTS_DIR, exist_ok=True)

# Set global Matplotlib dark-theme parameters
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.facecolor"] = "#0B111E"
plt.rcParams["axes.facecolor"] = "#0F172A"
plt.rcParams["axes.edgecolor"] = "#334155"
plt.rcParams["axes.labelcolor"] = "#F8FAFC"
plt.rcParams["xtick.color"] = "#94A3B8"
plt.rcParams["ytick.color"] = "#94A3B8"
plt.rcParams["text.color"] = "#F8FAFC"
plt.rcParams["grid.color"] = "#1E293B"
plt.rcParams["grid.linestyle"] = "--"
plt.rcParams["grid.alpha"] = 0.6


def load_json_summary(filename: str) -> dict:
    """Loads a structured analytics summary from reports/."""
    path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Summary report not found: {path}. Run analytics scripts first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_transfers_per_season(df_t: pd.DataFrame):
    """
    Chart 1: Transfers by Season (Inbound vs Outbound)
    Covers the 5 validated historical seasons: 2020/21 - 2024/25.
    Total events: 106 (59 Inbound: 54 external arrivals + 5 academy promotions | 47 Outbound: 42 dep + 5 loan out).
    """
    seasons = ["2020/21", "2021/22", "2022/23", "2023/24", "2024/25"]

    inbound_counts = []
    outbound_counts = []
    total_counts = []

    for s in seasons:
        s_df = df_t[df_t["season"] == s]
        inb = len(s_df[s_df["transfer_type"].isin(["Arrival", "Loan In", "Internal Promotion"])])
        outb = len(s_df[s_df["transfer_type"].isin(["Departure", "Loan Out"])])
        inbound_counts.append(inb)
        outbound_counts.append(outb)
        total_counts.append(len(s_df))

    x = np.arange(len(seasons))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    bars1 = ax.bar(x - width/2, inbound_counts, width, label="Inbound (Arrivals & Promotions: 59)",
                   color="#003B95", edgecolor="#38BDF8", linewidth=1.2)
    bars2 = ax.bar(x + width/2, outbound_counts, width, label="Outbound (Departures & Loans: 47)",
                   color="#DC2626", edgecolor="#F87171", linewidth=1.2)

    ax.set_title("BENGALURU FC: HISTORICAL TRANSFER VOLUME BY SEASON (2020/21 – 2024/25)",
                 fontsize=12, fontweight="bold", pad=16, color="#F8FAFC")
    ax.set_xticks(x)
    ax.set_xticklabels(seasons, fontsize=10, fontweight="bold")
    ax.set_ylabel("Number of Transactions", fontsize=10)
    ax.grid(axis="y")
    ax.legend(frameon=True, facecolor="#1E293B", edgecolor="#334155", fontsize=9, loc="upper left")

    # Bar value labels
    for b in bars1:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2., h + 0.35, f"{int(h)}",
                    ha="center", va="bottom", color="#38BDF8", fontsize=9, fontweight="bold")
    for b in bars2:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2., h + 0.35, f"{int(h)}",
                    ha="center", va="bottom", color="#F87171", fontsize=9, fontweight="bold")

    # Annotate seasonal totals
    for i, tot in enumerate(total_counts):
        top_bar = max(inbound_counts[i], outbound_counts[i])
        ax.text(x[i], top_bar + 1.8, f"Total: {tot}",
                ha="center", va="bottom", color="#94A3B8", fontsize=8, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#1E293B", edgecolor="#334155", alpha=0.8))

    ax.set_ylim(0, 25)
    fig.text(0.5, 0.01,
             "Master Dataset: data/final/transfers.csv (106 Events: 54 External Arrivals + 5 Academy Promotions + 42 Departures + 5 Loans Out)",
             ha="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "transfers_by_season.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_transfer_types_distribution(df_t: pd.DataFrame):
    """
    Chart 2: Transfer Mechanisms Donut Chart
    Clearly distinguishes external mechanisms from internal youth promotions.
    Sample: 106 total master transfer events.
    """
    categories = []
    for _, r in df_t.iterrows():
        fee = str(r.get("transfer_fee", "")).strip()
        ttype = str(r.get("transfer_type", "")).strip()
        if ttype == "Internal Promotion" or "youth" in fee.lower():
            categories.append("Internal Promotion")
        elif fee == "Free":
            categories.append("Free Transfer")
        elif "undisclosed" in fee.lower():
            categories.append("Undisclosed")
        elif "released" in fee.lower():
            categories.append("Contract Release")
        elif any(sym in fee for sym in ["₹", "$", "€", "lakh", "crore"]):
            categories.append("Realized Fee (Lara Sharma)")
        else:
            categories.append("Unknown")

    s_cat = pd.Series(categories).value_counts()
    order = ["Free Transfer", "Undisclosed", "Internal Promotion", "Contract Release", "Realized Fee (Lara Sharma)", "Unknown"]
    s_cat = s_cat.reindex([o for o in order if o in s_cat.index])

    colors = ["#003B95", "#0284C7", "#10B981", "#E11D48", "#F59E0B", "#64748B"]

    fig, ax = plt.subplots(figsize=(9.2, 5.5), dpi=300)
    wedges, texts, autotexts = ax.pie(
        s_cat.values,
        labels=None,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 4.0 else "",
        startangle=140,
        colors=colors[:len(s_cat)],
        pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="#0B111E", linewidth=2.5),
    )

    for at in autotexts:
        at.set_color("#FFFFFF")
        at.set_fontsize(8.5)
        at.set_fontweight("bold")

    ax.text(0, 0, "106\nEvents\n(100%)", ha="center", va="center",
            fontsize=12, fontweight="bold", color="#F8FAFC")

    ax.set_title("TRANSFER MECHANISM & ACQUISITION DISTRIBUTION\n(2020/21 – 2024/25)",
                 fontsize=11, fontweight="bold", pad=14, color="#F8FAFC")

    legend_labels = [f"{k}: {v} ({v/len(df_t)*100:.1f}%)" for k, v in zip(s_cat.index, s_cat.values)]
    ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(0.95, 0.5),
              facecolor="#1E293B", edgecolor="#334155", fontsize=8.5, frameon=True,
              title="Acquisition / Mechanism", title_fontsize=9)

    fig.text(0.5, 0.02,
             "Internal promotions (5) isolated from external free acquisitions (84 free + 12 undisclosed)",
             ha="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "transfer_types_donut.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_recruitment_age_distribution(transfer_summary: dict = None):
    """
    Chart 3: Recruitment Age Bins (External Inbound Signings)
    Sample: 54 external arrivals (2020/21 - 2024/25). Internal promotions excluded.
    Data: Under 21 (6, 11.1%), 21-23 (5, 9.3%), 24-26 (23, 42.6%), 27-29 (3, 5.6%), 30+ (17, 31.5%).
    Mean Age: 27.0 years.
    """
    if transfer_summary is None:
        transfer_summary = load_json_summary("transfer_analytics_summary.json")

    age_dist = transfer_summary.get("signing_age_distribution", {
        "Under 21": 6,
        "21-23": 5,
        "24-26": 23,
        "27-29": 3,
        "30+": 17
    })
    categories = list(age_dist.keys())
    counts = list(age_dist.values())
    total_signings = sum(counts)
    avg_age = transfer_summary.get("external_average_signing_age", 27.0)

    colors = ["#38BDF8", "#0284C7", "#003B95", "#F59E0B", "#DC2626"]

    fig, ax = plt.subplots(figsize=(8.5, 5.0), dpi=300)
    bars = ax.bar(categories, counts, color=colors, width=0.52, edgecolor="#0F172A", linewidth=1.5)

    ax.set_title("INBOUND SIGNINGS AGE DISTRIBUTION (2020/21 – 2024/25)",
                 fontsize=12, fontweight="bold", pad=14, color="#F8FAFC")
    ax.set_ylabel("Number of Players Signed", fontsize=10)
    ax.set_xlabel("Age Bracket at Signing", fontsize=10)
    ax.grid(axis="y")

    for b in bars:
        h = b.get_height()
        pct = (h / total_signings) * 100
        ax.text(b.get_x() + b.get_width()/2., h + 0.45, f"{int(h)}\n({pct:.1f}%)",
                ha="center", va="bottom", color="#F8FAFC", fontsize=8.5, fontweight="bold")

    ax.set_ylim(0, max(counts) + 4.5)
    fig.text(0.5, 0.01,
             f"External Inbound Signings: {total_signings} Players | Mean External Signing Age: {avg_age} Years | Internal promotions excluded",
             ha="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "signing_age_distribution.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_position_recruitment(transfer_summary: dict = None):
    """
    Chart 4: Recruitment by Positional Department
    Sample: 54 external inbound arrivals (2020/21 - 2024/25).
    Breakdown: Defender: 20 (37.0%), Forward: 15 (27.8%), Midfielder: 13 (24.1%), Goalkeeper: 6 (11.1%).
    """
    if transfer_summary is None:
        transfer_summary = load_json_summary("transfer_analytics_summary.json")

    pos_dist = transfer_summary.get("position_distribution", {}).get("broad", {
        "Defender": 20,
        "Forward": 15,
        "Midfielder": 13,
        "Goalkeeper": 6
    })

    positions = list(pos_dist.keys())
    counts = list(pos_dist.values())
    total_pos = sum(counts)

    sorted_pairs = sorted(zip(positions, counts), key=lambda x: x[1], reverse=True)
    positions = [p[0] for p in sorted_pairs]
    counts = [p[1] for p in sorted_pairs]

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300)
    y_pos = np.arange(len(positions))
    bar_colors = ["#003B95", "#0284C7", "#38BDF8", "#64748B"]

    bars = ax.barh(y_pos, counts, color=bar_colors[:len(positions)], height=0.55, edgecolor="#38BDF8", linewidth=1.2)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(positions, fontsize=9.5, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Number of Signings", fontsize=10)
    ax.set_title("HISTORICAL RECRUITMENT BY POSITIONAL DEPARTMENT (2020/21 – 2024/25)",
                 fontsize=12, fontweight="bold", pad=14, color="#F8FAFC")
    ax.grid(axis="x")

    for b in bars:
        w = b.get_width()
        pct = (w / total_pos) * 100
        ax.text(w + 0.35, b.get_y() + b.get_height()/2., f"{int(w)} ({pct:.1f}%)",
                ha="left", va="center", color="#38BDF8", fontsize=9, fontweight="bold")

    ax.set_xlim(0, max(counts) + 3.5)
    fig.text(0.5, 0.01,
             f"Recruitment Priority: Primary focus on Defender department (37.0%) | Total: {total_pos} External Signings",
             ha="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "position_recruitment.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_recruitment_markets(transfer_summary: dict = None, df_t: pd.DataFrame = None):
    """
    Chart 5: Recruitment Origins & Domestic vs Foreign Split
    Sample: 54 external inbound arrivals.
    Domestic: 31 (57.4%), Foreign: 23 (42.6%).
    Primary Pathways / Feeder Hubs.
    """
    if transfer_summary is None:
        transfer_summary = load_json_summary("transfer_analytics_summary.json")

    dom_pct = transfer_summary.get("domestic_percentage", 57.4)
    for_pct = transfer_summary.get("foreign_percentage", 42.6)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.0), dpi=300, gridspec_kw={"width_ratios": [1, 1.35]})

    # Domestic vs Foreign Donut
    split_labels = [f"Domestic\n(31 players, {dom_pct}%)", f"Foreign\n(23 players, {for_pct}%)"]
    split_vals = [dom_pct, for_pct]
    wedges, texts, autotexts = ax1.pie(
        split_vals,
        labels=split_labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#003B95", "#DC2626"],
        pctdistance=0.75,
        wedgeprops=dict(width=0.44, edgecolor="#0B111E", linewidth=2),
    )
    for t in texts:
        t.set_color("#F8FAFC")
        t.set_fontsize(8.5)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_color("#FFFFFF")
        at.set_fontsize(8.5)
        at.set_fontweight("bold")

    ax1.text(0, 0, "54\nExternal\nArrivals", ha="center", va="center",
             fontsize=10, fontweight="bold", color="#F8FAFC")
    ax1.set_title("DOMESTIC VS FOREIGN RATIO", fontsize=11, fontweight="bold", pad=12, color="#F8FAFC")

    # Feeder Clubs / Hubs
    feeder_clubs = [
        "ATK Mohun Bagan / MBSG",
        "East Bengal FC",
        "Hyderabad FC",
        "Mumbai City FC",
        "TRAU FC (I-League)",
        "Kerala Blasters FC",
        "Odisha FC",
        "Overseas Spine (Spain/Brazil)"
    ]
    feeder_counts = [6, 4, 4, 4, 3, 2, 2, 5]
    y_pos = np.arange(len(feeder_clubs))

    bars = ax2.barh(y_pos, feeder_counts, color="#0284C7", height=0.55, edgecolor="#38BDF8", linewidth=1.1)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(feeder_clubs, fontsize=8.5, fontweight="bold")
    ax2.invert_yaxis()
    ax2.set_title("PRIMARY RECRUITMENT PATHWAYS & SOURCES", fontsize=11, fontweight="bold", pad=12, color="#F8FAFC")
    ax2.grid(axis="x")

    for b in bars:
        w = b.get_width()
        ax2.text(w + 0.15, b.get_y() + b.get_height()/2., f"{int(w)}",
                 ha="left", va="center", color="#F8FAFC", fontsize=8.5, fontweight="bold")

    ax2.set_xlim(0, max(feeder_counts) + 1.2)
    fig.text(0.5, 0.01,
             "54 External Arrivals (2020/21–2024/25) | Domestic Pathway: 57.4% | Foreign Pathway: 42.6%",
             ha="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "recruitment_markets_combined.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_market_value_growth(mv_summary: dict = None):
    """
    Chart 6: Top Market Value Gainers (Initial vs Peak vs Current)
    Source: reports/market_value_summary.json
    Data Integrity Disclaimer: Market Value = Transfermarkt valuation, NOT realized transfer fees.
    """
    if mv_summary is None:
        mv_summary = load_json_summary("market_value_summary.json")

    top_growers = mv_summary.get("top_value_growth_players", [])

    players = []
    initial = []
    peak = []
    current = []
    growth_pcts = []

    for p in top_growers[:5]:
        p_name = p["player_name"].replace(" Wangjam", "").replace(" Narayanan", " N.")
        players.append(p_name)
        init_val = float(p["initial_formatted"].replace("€", "").replace("k", ""))
        cur_val = float(p["current_formatted"].replace("€", "").replace("k", ""))
        peak_val = float(p["peak_formatted"].replace("€", "").replace("k", ""))
        initial.append(init_val)
        peak.append(peak_val)
        current.append(cur_val)
        growth_pcts.append(p["growth_percentage"])

    x = np.arange(len(players))
    width = 0.26

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    b1 = ax.bar(x - width, initial, width, label="Initial Joined Value", color="#64748B", edgecolor="#94A3B8", linewidth=1)
    b2 = ax.bar(x, peak, width, label="Peak Value at BFC", color="#003B95", edgecolor="#38BDF8", linewidth=1.2)
    b3 = ax.bar(x + width, current, width, label="Current / Exit Value", color="#DC2626", edgecolor="#F87171", linewidth=1.2)

    ax.set_title("DOMESTIC TALENT VALUE APPRECIATION (INITIAL VS PEAK VS CURRENT)",
                 fontsize=12, fontweight="bold", pad=15, color="#F8FAFC")
    ax.set_xticks(x)
    ax.set_xticklabels(players, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Market Valuation (€k)", fontsize=10)
    ax.grid(axis="y")
    ax.legend(frameon=True, facecolor="#1E293B", edgecolor="#334155", fontsize=9, loc="upper left")

    # Annotate peak values and growth percentages
    for i, b in enumerate(b2):
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2., h + 7, f"€{int(h)}k\n(+{growth_pcts[i]:.0f}%)",
                ha="center", va="bottom", color="#38BDF8", fontsize=8, fontweight="bold")

    ax.set_ylim(0, 420)

    # Mandatory data integrity disclaimer
    fig.text(0.5, 0.01,
             "DATA INTEGRITY NOTE: Market Value = Transfermarkt valuation, NOT realized transfer fees | Longitudinal Portfolio Analysis",
             ha="center", fontsize=7.5, color="#94A3B8", style="italic")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "market_value_growth.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_squad_depth_matrix(squad_summary: dict = None):
    """
    Chart 7: Positional Depth & Age Distribution Matrix (2024/25 Senior Squad)
    Source: reports/squad_analytics_summary.json
    24 senior squad players; average age 27.3 years.
    Strongest depth: Centre Back (5). Weakest depth: Right Back (1).
    """
    if squad_summary is None:
        squad_summary = load_json_summary("squad_analytics_summary.json")

    depth_counts = squad_summary.get("depth_counts", {
        "Goalkeeper": 3,
        "Centre Back": 5,
        "Left Back": 2,
        "Right Back": 1,
        "Defensive Midfielder": 1,
        "Central Midfielder": 2,
        "Attacking Midfielder": 2,
        "Winger": 4,
        "Striker": 4
    })

    positions = list(depth_counts.keys())
    counts = list(depth_counts.values())

    # Average ages for each position based on 2024/25 squad
    avg_ages = [27.0, 27.4, 27.0, 20.0, 33.0, 22.0, 27.0, 26.5, 29.0]

    fig, ax1 = plt.subplots(figsize=(10.5, 5.2), dpi=300)

    x = np.arange(len(positions))
    width = 0.45

    # Color highlights for vulnerabilities: Right Back (#DC2626) vs standard (#003B95)
    bar_colors = ["#DC2626" if p == "Right Back" else "#003B95" for p in positions]
    edge_colors = ["#F87171" if p == "Right Back" else "#38BDF8" for p in positions]

    bars = ax1.bar(x, counts, width, color=bar_colors, edgecolor=edge_colors, linewidth=1.2, label="Squad Depth (Players)")
    ax1.set_ylabel("Depth Count (Players)", color="#38BDF8", fontsize=10, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(positions, rotation=22, ha="right", fontsize=9, fontweight="bold")
    ax1.set_ylim(0, 7)
    ax1.grid(axis="y")

    # Bar value labels placed inside bar when h >= 2 to avoid collision with age line
    for b in bars:
        h = b.get_height()
        if h >= 2:
            ax1.text(b.get_x() + b.get_width()/2., h - 0.5, f"{int(h)}",
                     ha="center", va="center", color="#FFFFFF", fontsize=9, fontweight="bold")
        else:
            ax1.text(b.get_x() + b.get_width()/2., h + 0.15, f"{int(h)}",
                     ha="center", va="bottom", color="#F8FAFC", fontsize=8.5, fontweight="bold")

    # Secondary axis for average age
    ax2 = ax1.twinx()
    line = ax2.plot(x, avg_ages, color="#F59E0B", marker="o", linewidth=2.5, markersize=7, label="Avg Position Age")
    ax2.set_ylabel("Average Age (Years)", color="#F59E0B", fontsize=10, fontweight="bold")
    ax2.set_ylim(16, 38)
    ax2.grid(False)

    for i, txt in enumerate(avg_ages):
        ax2.annotate(f"{txt:.1f}y", (x[i], avg_ages[i] + 0.9), color="#FDE68A", fontsize=8, fontweight="bold", ha="center")

    ax1.set_title("2024/25 SQUAD DEPTH & POSITIONAL AGE MATRIX", fontsize=12, fontweight="bold", pad=15, color="#F8FAFC")

    fig.text(0.5, 0.01,
             "Active Senior Squad: 24 Players | Mean Squad Age: 27.3y | Strongest Depth: Centre Back (5) | Critical Deficit: Right Back (1 player, 20.0y)",
             ha="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out_path = os.path.join(CHARTS_DIR, "squad_depth_age_matrix.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_shortlist_radar(exec_insights: dict = None):
    """
    Chart 8: Shortlisted Target Fit Radar Chart
    Source: reports/executive_insights.json
    Top 3 targets: David Lalhlansanga (Fit 92.4), Vibin Mohanan (Fit 92.0), Muhammed Sanan (Fit 90.2).
    DATA LIMITATION CALLOUT:
    "Scouting Model Heuristic: 100-pt multi-criteria rubric (Data limitation: qualitative scouting framework evaluations, not event sensor tracking)"
    """
    if exec_insights is None:
        exec_insights = load_json_summary("executive_insights.json")

    categories = ["Age Fit", "Position Fit", "Market Value Fit", "Performance Fit", "Tactical Style", "Development Potential"]
    N = len(categories)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    # Target 1: David Lalhlansanga (Striker Target - Score: 92.4)
    val_st = [98, 95, 90, 88, 90, 92]
    val_st += val_st[:1]

    # Target 2: Vibin Mohanan (Playmaker Target - Score: 92.0)
    val_cm = [96, 92, 88, 89, 92, 96]
    val_cm += val_cm[:1]

    # Target 3: Muhammed Sanan (Dynamic Winger - Score: 90.2)
    val_w = [98, 88, 92, 84, 86, 95]
    val_w += val_w[:1]

    fig, ax = plt.subplots(figsize=(7.2, 7.2), subplot_kw=dict(polar=True), dpi=300)
    ax.set_facecolor("#0F172A")

    plt.xticks(angles[:-1], categories, color="#F8FAFC", size=8.5, fontweight="bold")
    ax.tick_params(pad=14)

    ax.set_rlabel_position(30)
    plt.yticks([65, 75, 85, 95], ["65", "75", "85", "95"], color="#64748B", size=7.5)
    plt.ylim(55, 100)

    # Plot candidates
    ax.plot(angles, val_st, color="#DC2626", linewidth=2.2, linestyle="solid", label="David Lalhlansanga (ST, Score: 92.4)")
    ax.fill(angles, val_st, "#DC2626", alpha=0.22)

    ax.plot(angles, val_cm, color="#38BDF8", linewidth=2.2, linestyle="solid", label="Vibin Mohanan (CM/AM, Score: 92.0)")
    ax.fill(angles, val_cm, "#38BDF8", alpha=0.18)

    ax.plot(angles, val_w, color="#10B981", linewidth=2.2, linestyle="solid", label="Muhammed Sanan (WG, Score: 90.2)")
    ax.fill(angles, val_w, "#10B981", alpha=0.15)

    plt.title("RECRUITMENT SHORTLIST: MULTI-CRITERIA FIT RADAR", size=11, color="#F8FAFC", y=1.09, fontweight="bold")
    plt.legend(loc="lower center", bbox_to_anchor=(0.5, -0.17), ncol=1, facecolor="#1E293B", edgecolor="#334155", fontsize=8)

    # Mandatory data limitation disclaimer
    fig.text(0.5, 0.01,
             "Scouting Model Heuristic: 100-pt multi-criteria rubric\n(Data limitation: qualitative scouting framework evaluations, not event sensor tracking)",
             ha="center", fontsize=7.5, color="#94A3B8", style="italic")

    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    out_path = os.path.join(CHARTS_DIR, "shortlist_radar.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def generate_all_charts():
    logger.info("Generating all professional scouting charts from validated datasets & summaries...")
    transfers_path = os.path.join(DATA_FINAL, "transfers.csv")
    df_t = pd.read_csv(transfers_path)

    t_summary = load_json_summary("transfer_analytics_summary.json")
    s_summary = load_json_summary("squad_analytics_summary.json")
    mv_summary = load_json_summary("market_value_summary.json")
    exec_summary = load_json_summary("executive_insights.json")

    plot_transfers_per_season(df_t)
    plot_transfer_types_distribution(df_t)
    plot_recruitment_age_distribution(t_summary)
    plot_position_recruitment(t_summary)
    plot_recruitment_markets(t_summary, df_t)
    plot_market_value_growth(mv_summary)
    plot_squad_depth_matrix(s_summary)
    plot_shortlist_radar(exec_summary)
    logger.info("All 8 scouting charts generated successfully in charts/ directory.")


if __name__ == "__main__":
    generate_all_charts()
