# Bengaluru FC Recruitment Intelligence (2020/21 – 2026/27)
### Professional Football Scouting & Recruitment Intelligence Report

A modular, data-driven football scouting and recruitment analysis system built for **Bengaluru FC**, covering the 2020/21 through 2026/27 seasons. 

The objective of this platform is to analyse Bengaluru FC's historical recruitment strategy, player pathways, squad composition, market value development, and current squad gaps in order to generate data-backed recruitment profiles and actionable player recommendations.

---

## Analytical Flow

```
Historical Transfers
        ↓
Recruitment Analysis
        ↓
Recruitment Identity
        ↓
Player Pathways
        ↓
Market Value Analysis
        ↓
Current Squad Analysis
        ↓
Squad Gaps
        ↓
Recruitment Profiles
        ↓
Player Shortlist
        ↓
Final Recommendations & PDF Report
```

---

## Core Data Rules

1. **Never Invent Data**: No fabricated player statistics, transfer fees, or valuations.
2. **Market Value $\neq$ Transfer Fee**: Transfer fees are transaction prices between clubs; market values reflect market asset worth. They are never conflated.
3. **Missing Data Standard**: If information is unconfirmed or unavailable, it is explicitly marked as `N/A`, `Unknown`, or `Undisclosed`.
4. **Data Validation Tracking**: Every record maintains:
   - `source` (e.g., Wikipedia, Transfermarkt)
   - `source_url`
   - `validation_status` (`Verified`, `Partial`, `Conflicting`, `Missing`)

---

## Project Structure

```
Bengaluru-FC-Recruitment-Intelligence/
├── assets/
│   ├── images/
│   └── logo/
├── charts/                           # High-resolution Matplotlib dark-theme figures
├── data/
│   ├── raw/
│   │   ├── wikipedia/                # Raw Wikipedia season transfer data
│   │   └── transfermarkt/            # Manually supplied Transfermarkt CSVs
│   ├── processed/                    # Cleaned & standardized intermediate datasets
│   └── final/                        # Master datasets
├── output/                           # Generated PDF reports
│   └── Bengaluru_FC_Scouting_Report.pdf
├── src/
│   ├── collect_wikipedia.py          # Wikipedia transfer scraper
│   ├── clean_data.py                 # Harmonization, validation & data cleaning
│   ├── analyse_transfers.py          # Historical transfer analytics
│   ├── analyse_squad.py              # Squad composition, depth & gap identification
│   ├── analyse_market_value.py       # Valuation growth & career pathways
│   ├── generate_insights.py          # 6 Key conclusions, recruitment profiles & shortlist
│   └── generate_report.py            # 15-page presentation-grade ReportLab PDF builder
├── templates/                        # Reusable CSV templates with schema definitions
│   ├── transfers_template.csv
│   ├── players_template.csv
│   ├── squads_template.csv
│   ├── player_market_values_template.csv
│   └── player_pathways_template.csv
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## Setup & Execution

### 1. Installation
Create and activate your Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
pip install -r requirements.txt
```

### 2. Running Data Pipeline & Analysis
```bash
# Step 1: Scrape Wikipedia historical transfers
python src/collect_wikipedia.py

# Step 2: Clean and validate datasets
python src/clean_data.py

# Step 3: Run analytics engines
python src/analyse_transfers.py
python src/analyse_squad.py
python src/analyse_market_value.py
python src/generate_insights.py

# Step 4: Build final 15-page Scouting Report PDF
python src/generate_report.py
```

---

## Final Deliverable
The primary output is a 14–15 page presentation-grade PDF scouting report (`output/Bengaluru_FC_Scouting_Report.pdf`) styled in Bengaluru FC colors (`#003B95` Royal Blue, `#DC2626` Crimson Red, `#0B111E` Dark theme), designed for sporting directors, chief scouts, and football decision-makers.

**Author**: Ayush Singh
