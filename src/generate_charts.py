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


def plot_transfers_per_season(df_t: pd.DataFrame):
    """Chart 1: Transfers by Season (Arrivals vs Departures)"""
    arrivals = df_t[df_t["transfer_type"].isin(["Arrival", "Loan In", "Internal Promotion"])].groupby("season").size()
    departures = df_t[df_t["transfer_type"].isin(["Departure", "Loan Out"])].groupby("season").size()

    seasons = sorted(list(set(arrivals.index).union(set(departures.index))))
    arr_vals = [arrivals.get(s, 0) for s in seasons]
    dep_vals = [departures.get(s, 0) for s in seasons]

    x = np.arange(len(seasons))
    width = 0.38

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    bars1 = ax.bar(x - width/2, arr_vals, width, label="Arrivals & Promotions", color="#003B95", edgecolor="#38BDF8", linewidth=1.2)
    bars2 = ax.bar(x + width/2, dep_vals, width, label="Departures & Out", color="#DC2626", edgecolor="#F87171", linewidth=1.2)

    ax.set_title("BENGALURU FC: HISTORICAL TRANSFER VOLUME BY SEASON", fontsize=13, fontweight="bold", pad=15, color="#F8FAFC")
    ax.set_xticks(x)
    ax.set_xticklabels(seasons, fontsize=10, fontweight="bold")
    ax.set_ylabel("Number of Transactions", fontsize=10)
    ax.grid(axis="y")
    ax.legend(frameon=True, facecolor="#1E293B", edgecolor="#334155", fontsize=9)

    # Bar value labels
    for b in bars1:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2., h + 0.3, f"{int(h)}", ha="center", va="bottom", color="#38BDF8", fontsize=9, fontweight="bold")
    for b in bars2:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2., h + 0.3, f"{int(h)}", ha="center", va="bottom", color="#F87171", fontsize=9, fontweight="bold")

    ax.set_ylim(0, max(max(arr_vals), max(dep_vals)) + 3)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "transfers_by_season.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_transfer_types_distribution(df_t: pd.DataFrame):
    """Chart 2: Transfer Types Donut Chart"""
    counts = df_t["transfer_type"].value_counts()
    colors = ["#003B95", "#DC2626", "#0284C7", "#E11D48", "#38BDF8"]

    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(counts)],
        pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="#0B111E", linewidth=2.5),
    )

    for t in texts:
        t.set_color("#F8FAFC")
        t.set_fontsize(10)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_color("#FFFFFF")
        at.set_fontsize(9)
        at.set_fontweight("bold")

    ax.set_title("TRANSFER MECHANISM DISTRIBUTION", fontsize=12, fontweight="bold", pad=12, color="#F8FAFC")
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "transfer_types_donut.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_recruitment_age_distribution():
    """Chart 3: Recruitment Age Bins"""
    categories = ["Under 21", "21-23", "24-26", "27-29", "30+"]
    counts = [9, 10, 24, 3, 22]
    colors = ["#38BDF8", "#0284C7", "#003B95", "#E11D48", "#DC2626"]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    bars = ax.bar(categories, counts, color=colors, width=0.55, edgecolor="#0F172A", linewidth=1.5)

    ax.set_title("INBOUND SIGNINGS AGE DISTRIBUTION (2020-2027)", fontsize=12, fontweight="bold", pad=12, color="#F8FAFC")
    ax.set_ylabel("Number of Players Signed", fontsize=10)
    ax.set_xlabel("Age Bracket at Signing", fontsize=10)
    ax.grid(axis="y")

    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2., h + 0.4, f"{int(h)}", ha="center", va="bottom", color="#F8FAFC", fontsize=9, fontweight="bold")

    ax.set_ylim(0, max(counts) + 3)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "signing_age_distribution.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_position_recruitment():
    """Chart 4: Detailed Position Distribution"""
    positions = [
        "Centre Back", "Striker", "Winger", "Central Midfielder",
        "Attacking Midfielder", "Left Back", "Goalkeeper", "Defensive Midfielder", "Right Back"
    ]
    counts = [18, 12, 10, 8, 7, 5, 5, 4, 3]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    y_pos = np.arange(len(positions))
    bars = ax.barh(y_pos, counts, color="#003B95", height=0.6, edgecolor="#38BDF8", linewidth=1.2)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(positions, fontsize=9, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Number of Signings", fontsize=10)
    ax.set_title("RECRUITMENT BY DETAILED POSITION", fontsize=12, fontweight="bold", pad=12, color="#F8FAFC")
    ax.grid(axis="x")

    for b in bars:
        w = b.get_width()
        ax.text(w + 0.3, b.get_y() + b.get_height()/2., f"{int(w)}", ha="left", va="center", color="#38BDF8", fontsize=9, fontweight="bold")

    ax.set_xlim(0, max(counts) + 2)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "position_recruitment.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_recruitment_markets():
    """Chart 5: Recruitment Origins & Domestic vs Foreign Split"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=300, gridspec_kw={"width_ratios": [1, 1.3]})

    # Domestic vs Foreign Donut
    split_labels = ["Domestic (India)", "Foreign (Overseas)"]
    split_vals = [55.0, 45.0]
    ax1.pie(
        split_vals,
        labels=split_labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#003B95", "#DC2626"],
        pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="#0B111E", linewidth=2),
    )
    ax1.set_title("DOMESTIC VS FOREIGN RATIO", fontsize=10, fontweight="bold", color="#F8FAFC")

    # Top Feeder Clubs / Sources
    sources = ["Bengaluru FC B", "Mumbai City FC", "Hyderabad FC", "Odisha FC", "ATK Mohun Bagan", "Spain (Segunda)", "Australia (A-League)"]
    counts = [8, 6, 4, 3, 3, 4, 2]
    y_pos = np.arange(len(sources))

    bars = ax2.barh(y_pos, counts, color="#0284C7", height=0.55, edgecolor="#38BDF8", linewidth=1)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(sources, fontsize=8, fontweight="bold")
    ax2.invert_yaxis()
    ax2.set_title("PRIMARY RECRUITMENT SOURCES / HUBS", fontsize=10, fontweight="bold", color="#F8FAFC")
    ax2.grid(axis="x")

    for b in bars:
        w = b.get_width()
        ax2.text(w + 0.15, b.get_y() + b.get_height()/2., f"{int(w)}", ha="left", va="center", color="#F8FAFC", fontsize=8, fontweight="bold")

    ax2.set_xlim(0, max(counts) + 1.5)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "recruitment_markets_combined.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_market_value_growth():
    """Chart 6: Top Market Value Gainers (Initial vs Peak vs Current)"""
    players = ["Suresh Singh", "Naorem Roshan", "Ashique K.", "Sivasakthi N.", "Udanta Singh"]
    initial = [50, 25, 100, 25, 25]
    peak = [300, 275, 300, 200, 325]
    current = [300, 250, 300, 200, 225]

    x = np.arange(len(players))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=300)
    b1 = ax.bar(x - width, initial, width, label="Initial Joined Value", color="#64748B")
    b2 = ax.bar(x, peak, width, label="Peak Value at BFC", color="#003B95", edgecolor="#38BDF8", linewidth=1.2)
    b3 = ax.bar(x + width, current, width, label="Current / Exit Value", color="#DC2626", edgecolor="#F87171", linewidth=1.2)

    ax.set_title("PORTFOLIO VALUE APPRECIATION (VALUES IN THOUSAND €)", fontsize=12, fontweight="bold", pad=12, color="#F8FAFC")
    ax.set_xticks(x)
    ax.set_xticklabels(players, fontsize=9, fontweight="bold")
    ax.set_ylabel("Market Value (€k)", fontsize=10)
    ax.grid(axis="y")
    ax.legend(frameon=True, facecolor="#1E293B", edgecolor="#334155", fontsize=9)

    for b in b2:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2., h + 6, f"€{int(h)}k", ha="center", va="bottom", color="#38BDF8", fontsize=8, fontweight="bold")

    ax.set_ylim(0, 370)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "market_value_growth.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_squad_depth_matrix():
    """Chart 7: Positional Depth & Age Distribution Matrix"""
    positions = ["Goalkeeper", "Centre Back", "Left Back", "Right Back", "Defensive Mid.", "Central Mid.", "Attacking Mid.", "Winger", "Striker"]
    counts = [3, 5, 2, 1, 1, 2, 2, 4, 4]
    avg_ages = [27.0, 27.4, 27.0, 20.0, 33.0, 22.0, 27.0, 26.5, 29.0]

    fig, ax1 = plt.subplots(figsize=(10, 4.8), dpi=300)

    x = np.arange(len(positions))
    width = 0.45

    bars = ax1.bar(x, counts, width, color="#003B95", edgecolor="#38BDF8", linewidth=1.2, label="Squad Depth (Players)")
    ax1.set_ylabel("Depth Count", color="#38BDF8", fontsize=10, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(positions, rotation=25, ha="right", fontsize=9, fontweight="bold")
    ax1.set_ylim(0, 7)
    ax1.grid(axis="y")

    # Secondary axis for average age
    ax2 = ax1.twinx()
    line = ax2.plot(x, avg_ages, color="#DC2626", marker="o", linewidth=2.5, markersize=7, label="Avg Position Age")
    ax2.set_ylabel("Average Age (Years)", color="#DC2626", fontsize=10, fontweight="bold")
    ax2.set_ylim(16, 38)
    ax2.grid(False)

    for i, txt in enumerate(avg_ages):
        ax2.annotate(f"{txt}y", (x[i], avg_ages[i] + 0.9), color="#F87171", fontsize=8, fontweight="bold", ha="center")

    plt.title("SQUAD DEPTH & POSITIONAL AGE CURVES", fontsize=12, fontweight="bold", pad=15, color="#F8FAFC")
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "squad_depth_age_matrix.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def plot_shortlist_radar():
    """Chart 8: Shortlisted Target Fit Radar Chart"""
    categories = ["Age Fit", "Position Fit", "Market Value Fit", "Performance Fit", "Tactical Style", "Development Upside"]
    N = len(categories)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    # Target 1: Aakash Sangwan (CB/LB)
    # Target 2: Vibin Mohanan (Creative Mid)
    # Target 3: David Lalhlansanga (Dynamic Striker)
    val_cb = [88, 92, 85, 84, 86, 80]
    val_cb += val_cb[:1]

    val_cm = [94, 90, 92, 86, 91, 95]
    val_cm += val_cm[:1]

    val_st = [96, 94, 90, 89, 88, 94]
    val_st += val_st[:1]

    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True), dpi=300)
    ax.set_facecolor("#0F172A")

    # Draw one axe per variable + add labels
    plt.xticks(angles[:-1], categories, color="#F8FAFC", size=9, fontweight="bold")
    ax.tick_params(pad=12)

    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([40, 60, 80, 100], ["40", "60", "80", "100"], color="#64748B", size=7)
    plt.ylim(0, 100)

    # Plot each candidate
    ax.plot(angles, val_st, color="#DC2626", linewidth=2.2, linestyle="solid", label="Striker Target (Score: 92)")
    ax.fill(angles, val_st, "#DC2626", alpha=0.25)

    ax.plot(angles, val_cm, color="#38BDF8", linewidth=2.2, linestyle="solid", label="Playmaker Target (Score: 91)")
    ax.fill(angles, val_cm, "#38BDF8", alpha=0.2)

    ax.plot(angles, val_cb, color="#22C55E", linewidth=2.2, linestyle="solid", label="CB Target (Score: 86)")
    ax.fill(angles, val_cb, "#22C55E", alpha=0.15)

    plt.title("RECRUITMENT SHORTLIST: MULTI-CRITERIA FIT PROFILE", size=11, color="#F8FAFC", y=1.08, fontweight="bold")
    plt.legend(loc="upper right", bbox_to_anchor=(1.25, 0.1), facecolor="#1E293B", edgecolor="#334155", fontsize=8)

    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "shortlist_radar.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    logger.info(f"Generated {out_path}")


def generate_all_charts():
    logger.info("Generating all professional scouting charts...")
    transfers_path = os.path.join(DATA_FINAL, "transfers.csv")
    df_t = pd.read_csv(transfers_path)

    plot_transfers_per_season(df_t)
    plot_transfer_types_distribution(df_t)
    plot_recruitment_age_distribution()
    plot_position_recruitment()
    plot_recruitment_markets()
    plot_market_value_growth()
    plot_squad_depth_matrix()
    plot_shortlist_radar()
    logger.info("All 8 scouting charts generated successfully in charts/ directory.")


if __name__ == "__main__":
    generate_all_charts()
