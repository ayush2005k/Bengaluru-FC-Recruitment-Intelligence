"""
scripts/create_assets.py
Generates high-resolution branding graphics for Bengaluru FC Scouting Report.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ASSETS_LOGO_DIR = os.path.join("assets", "logo")
os.makedirs(ASSETS_LOGO_DIR, exist_ok=True)


def generate_bengaluru_crest():
    fig, ax = plt.subplots(figsize=(3, 3), dpi=300)
    ax.set_facecolor("#0B111E")
    fig.patch.set_facecolor("#0B111E")

    # Outer Shield
    shield = patches.Polygon(
        [[0.5, 0.95], [0.85, 0.85], [0.85, 0.45], [0.5, 0.05], [0.15, 0.45], [0.15, 0.85]],
        closed=True,
        facecolor="#003B95",
        edgecolor="#DC2626",
        linewidth=4,
    )
    ax.add_patch(shield)

    # Inner Accent
    inner = patches.Polygon(
        [[0.5, 0.90], [0.80, 0.82], [0.80, 0.46], [0.5, 0.12], [0.20, 0.46], [0.20, 0.82]],
        closed=True,
        facecolor="#0F172A",
        edgecolor="#38BDF8",
        linewidth=1.5,
    )
    ax.add_patch(inner)

    # Text
    ax.text(0.5, 0.65, "BFC", ha="center", va="center", color="#F8FAFC", fontsize=20, fontweight="bold")
    ax.text(0.5, 0.48, "★ ★", ha="center", va="center", color="#F59E0B", fontsize=11)
    ax.text(0.5, 0.32, "RECRUITMENT", ha="center", va="center", color="#38BDF8", fontsize=7, fontweight="bold")
    ax.text(0.5, 0.23, "INTELLIGENCE", ha="center", va="center", color="#E2E8F0", fontsize=6, fontweight="bold")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    out_path = os.path.join(ASSETS_LOGO_DIR, "bfc_crest.png")
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight", pad_inches=0.1)
    plt.close()
    print(f"Generated Bengaluru FC Crest at {out_path}")


if __name__ == "__main__":
    generate_bengaluru_crest()
