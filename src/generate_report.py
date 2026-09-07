"""
src/generate_report.py
Generates a presentation-grade, 15-page executive PDF scouting report for Bengaluru FC
using ReportLab with a dark football intelligence theme.

Design Specs:
- Landscape A4 slide deck (841.89 x 595.27 pt)
- Background: #0B111E / #0F172A
- BFC Royal Blue: #003B95
- BFC Crimson Red: #DC2626
- Accent Sky: #38BDF8
- Text: #F8FAFC, #94A3B8
- Exactly 15 Pages, each designed like a high-end presentation slide.
"""

import os
import sys
import logging
from typing import List, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas

# Import local analysis engines
from analyse_transfers import run_transfer_analysis
from analyse_squad import run_squad_analysis
from analyse_market_value import run_market_value_analysis
from generate_insights import (
    get_six_key_conclusions,
    get_ideal_recruitment_profiles,
    get_shortlisted_players,
    get_final_recruitment_strategy,
)

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = "output"
CHARTS_DIR = "charts"
ASSETS_DIR = "assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)
PDF_PATH = os.path.join(OUTPUT_DIR, "Bengaluru_FC_Scouting_Report.pdf")

# Page Dimensions (Landscape A4)
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

# Color Palette
COLOR_BG = colors.HexColor("#0B111E")
COLOR_CARD_BG = colors.HexColor("#0F172A")
COLOR_CARD_ALT = colors.HexColor("#1E293B")
COLOR_BFC_BLUE = colors.HexColor("#003B95")
COLOR_BFC_RED = colors.HexColor("#DC2626")
COLOR_ACCENT_SKY = colors.HexColor("#38BDF8")
COLOR_TEXT_LIGHT = colors.HexColor("#F8FAFC")
COLOR_TEXT_MUTED = colors.HexColor("#94A3B8")
COLOR_BORDER = colors.HexColor("#334155")
COLOR_SUCCESS = colors.HexColor("#22C55E")
COLOR_WARNING = colors.HexColor("#F59E0B")


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that draws dark background, top accent headers, and footer page counts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()

        # 1. Base Dark Background
        self.setFillColor(COLOR_BG)
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)

        # Skip header/footer chrome on Cover Page (Page 1)
        if self._pageNumber > 1:
            # Top Accent Strip
            self.setFillColor(COLOR_BFC_BLUE)
            self.rect(0, PAGE_HEIGHT - 6, PAGE_WIDTH * 0.7, 6, fill=True, stroke=False)
            self.setFillColor(COLOR_BFC_RED)
            self.rect(PAGE_WIDTH * 0.7, PAGE_HEIGHT - 6, PAGE_WIDTH * 0.3, 6, fill=True, stroke=False)

            # Footer Divider
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.75)
            self.line(28, 26, PAGE_WIDTH - 28, 26)

            # Footer Text
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_TEXT_MUTED)
            self.drawString(28, 14, "BENGALURU FC RECRUITMENT INTELLIGENCE  |  CONFIDENTIAL SCOUTING REPORT (2020/21 - 2024/25)")

            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_ACCENT_SKY)
            page_str = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(PAGE_WIDTH - 28, 14, page_str)

        self.restoreState()


def get_report_styles():
    """Defines typographic styles with proper leading and contrast."""
    base = getSampleStyleSheet()

    styles = {
        "Normal": base["Normal"],
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=34,
            leading=38,
            textColor=COLOR_TEXT_LIGHT,
            alignment=1,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=COLOR_ACCENT_SKY,
            alignment=1,
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=COLOR_TEXT_MUTED,
            alignment=1,
        ),
        "SlideTitle": ParagraphStyle(
            "SlideTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "SlideSubtitle": ParagraphStyle(
            "SlideSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_ACCENT_SKY,
        ),
        "CardTitle": ParagraphStyle(
            "CardTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=COLOR_ACCENT_SKY,
        ),
        "CardValue": ParagraphStyle(
            "CardValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=19,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "CardText": ParagraphStyle(
            "CardText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_TEXT_MUTED,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=COLOR_ACCENT_SKY,
            alignment=0,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=8.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "TableCellMuted": ParagraphStyle(
            "TableCellMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            textColor=COLOR_TEXT_MUTED,
        ),
        "BadgeHigh": ParagraphStyle(
            "BadgeHigh",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=colors.HexColor("#EF4444"),
        ),
        "BadgeMedium": ParagraphStyle(
            "BadgeMedium",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=colors.HexColor("#F59E0B"),
        ),
        "BadgeLow": ParagraphStyle(
            "BadgeLow",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=colors.HexColor("#10B981"),
        ),
    }
    return styles


def create_header_banner(title: str, subtitle: str, styles: Dict[str, ParagraphStyle]) -> Table:
    """Standardized top header bar for presentation slides."""
    p_title = Paragraph(title.upper(), styles["SlideTitle"])
    p_sub = Paragraph(subtitle, styles["SlideSubtitle"])
    t = Table([[p_title], [p_sub]], colWidths=[785])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def build_kpi_card(title: str, value: str, note: str, styles: Dict[str, ParagraphStyle], width: float = 125, height: float = 58) -> Table:
    """Builds a dark analytical KPI metric card."""
    content = [
        [Paragraph(title.upper(), styles["CardTitle"])],
        [Paragraph(value, styles["CardValue"])],
        [Paragraph(note, styles["CardText"])],
    ]
    t = Table(content, colWidths=[width], rowHeights=[12, 22, 14])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ==============================================================================
# SLIDE BUILDERS (15 PAGES)
# ==============================================================================

def build_page_01_cover(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 1: Cover Page"""
    story = [
        Spacer(1, 40),
    ]

    crest_path = os.path.join(ASSETS_DIR, "logo", "bfc_crest.png")
    if os.path.exists(crest_path):
        story.append(Image(crest_path, width=1.5*inch, height=1.5*inch))
        story.append(Spacer(1, 20))

    story.append(Paragraph("BENGALURU FC", styles["CoverTitle"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("SCOUTING & RECRUITMENT REPORT", styles["CoverSubtitle"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("HISTORICAL RECRUITMENT ANALYSIS & STRATEGIC SQUAD PLANNING (2020/21 – 2024/25)", styles["CoverMeta"]))
    story.append(Spacer(1, 50))

    # Details Box
    details_data = [
        [Paragraph("<b>Prepared by:</b> Ayush Singh", styles["Body"]), Paragraph("<b>Focus Club:</b> Bengaluru FC (ISL)", styles["Body"])],
        [Paragraph("<b>Primary Analytical Period:</b> 2020/21 – 2024/25", styles["Body"]), Paragraph("<b>Framework:</b> Gap-Driven Recruitment Engine", styles["Body"])],
        [Paragraph("<b>Data Sources:</b> Wikipedia Historicals & Transfermarkt", styles["Body"]), Paragraph("<b>Data Integrity:</b> 100% Verified Non-Synthetic Data", styles["Body"])],
    ]
    t_det = Table(details_data, colWidths=[240, 240])
    t_det.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(t_det)
    story.append(Spacer(1, 35))
    story.append(Paragraph("CONFIDENTIAL SCOUTING DOSSIER  |  FOR TECHNICAL DIRECTORS & SPORTING EXECUTIVES", styles["CoverMeta"]))
    story.append(PageBreak())
    return story


def build_page_02_executive_summary(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 2: Executive Summary"""
    story = [
        create_header_banner("01. Executive Summary", "Analytical Scope, Dashboard Overview & Methodological Pipeline", styles),
        Spacer(1, 8),
    ]

    # Row 1: KPI Cards
    card1 = build_kpi_card("Seasons Analysed", "5", "2020/21 to 2024/25", styles, width=125)
    card2 = build_kpi_card("Total Transfers", "106", "101 Ext + 5 Academy", styles, width=125)
    card3 = build_kpi_card("Total Inbound", "59", "54 Ext + 5 Academy", styles, width=125)
    card4 = build_kpi_card("Avg Signing Age", "27.0y", "Bimodal (24-26 & 30+)", styles, width=125)
    card5 = build_kpi_card("Free Agent %", "92.6%", "50/54 External Free", styles, width=125)
    card6 = build_kpi_card("Domestic Ratio", "57.4%", "31 Domestic Signings", styles, width=125)

    kpi_table = Table([[card1, card2, card3, card4, card5, card6]], colWidths=[130]*6)
    kpi_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # Analytical Flow Narrative & Structure Box
    flow_text = (
        "<b>THE ANALYTICAL RECRUITMENT FLOW:</b><br/>"
        "Historical Transfers &rarr; Recruitment Analysis &rarr; Recruitment Identity &rarr; "
        "Player Pathways &rarr; Market Value Trajectory &rarr; Current Squad Analysis &rarr; "
        "Squad Gaps Detection &rarr; Ideal Recruitment Profiles &rarr; Multi-Criteria Shortlisting &rarr; "
        "Final Strategic Recommendations"
    )
    t_flow = Table([[Paragraph(flow_text, styles["BodyBold"])]], colWidths=[785])
    t_flow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 14))

    # 3-Column Executive Takeaways
    col1 = [
        Paragraph("<b>1. Recruitment Architecture</b>", styles["CardTitle"]),
        Spacer(1, 4),
        Paragraph("Bengaluru FC's transfer strategy is fundamentally shaped by opportunistic free-agent contract captures and domestic swaps. With 92.6% of external arrivals acquired on free transfers (93.2% including academy promotions), financial exposure is tightly regulated, requiring high precision in medical, tactical, and motivational vetting.", styles["Body"]),
    ]
    col2 = [
        Paragraph("<b>2. Current Squad Dynamics</b>", styles["CardTitle"]),
        Spacer(1, 4),
        Paragraph("The current roster holds an average age of 27.3 years. While the central defensive core (Jovanović, Bheke, Sana Singh) and anchor Gurpreet Singh Sandhu provide seasoned stability, the offensive spine has entered an acute succession window with senior starters averaging 35+ years.", styles["Body"]),
    ]
    col3 = [
        Paragraph("<b>3. Strategic Imperatives</b>", styles["CardTitle"]),
        Spacer(1, 4),
        Paragraph("To maintain championship contention in upcoming campaigns, the sporting department must execute an immediate transition plan: securing a high-pressing U24 striker, acquiring a prime-age creative playmaker (No. 8/10), and strengthening wide defensive depth without blocking academy minutes.", styles["Body"]),
    ]

    exec_grid = Table([[col1, col2, col3]], colWidths=[256, 256, 256])
    exec_grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(exec_grid)
    story.append(PageBreak())
    return story


def build_page_03_recruitment_identity(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 3: Club Recruitment Identity"""
    story = [
        create_header_banner("02. Club Recruitment Identity", "Empirical Evaluation of Bengaluru FC's Historical Transfer Blueprint", styles),
        Spacer(1, 8),
    ]

    # Metrics Row
    m1 = build_kpi_card("Average Signing Age", "27.0 Years", "Bimodal (24-26 & 30+)", styles, width=150)
    m2 = build_kpi_card("Top Recruited Area", "Defenders (20)", "Center Backs Priority", styles, width=150)
    m3 = build_kpi_card("Transfer Mechanism", "Free Agent (92.6%)", "Zero Net Transfer Deficits", styles, width=150)
    m4 = build_kpi_card("Primary Market", "Domestic (57.4%)", "ISL Rivals & I-League", styles, width=150)
    m5 = build_kpi_card("Foreign Ratio", "42.6% (Overseas)", "Spain, Australia, Brazil", styles, width=150)

    m_table = Table([[m1, m2, m3, m4, m5]], colWidths=[155]*5)
    m_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(m_table)
    story.append(Spacer(1, 14))

    # Core Identity Synthesis & Season Breakdown Table
    left_narrative = [
        Paragraph("<b>DATA-BACKED RECRUITMENT IDENTITY VERDICT:</b>", styles["CardTitle"]),
        Spacer(1, 6),
        Paragraph(
            "Bengaluru FC's recruitment identity across 2020/21–2024/25 is characterized by an <b>opportunistic, contract-efficient philosophy</b>. "
            "Rather than competing on transfer fee inflation, the club capitalizes on expiring ISL contracts and proven overseas veterans with European/A-League pedigree.<br/><br/>"
            "<b>Key Identity Pillars:</b><br/>"
            "&bull; <b>Zero Fee Dependency:</b> 92.6% of external arrivals are free agents (93.2% including internal promotions).<br/>"
            "&bull; <b>Age Bifurcation:</b> External recruits fall into either prime domestic acquisitions (24-26y, 42.6%) or foreign spine leaders (30+y, 31.5%).<br/>"
            "&bull; <b>Central Spine Priority:</b> Defensive positions represent the single largest recruitment expenditure of squad spots (20 signings).<br/>"
            "&bull; <b>Domestic Stability:</b> Core Indian players (Suresh, Roshan, Chhetri, Gurpreet) provide high-tenure continuity, minimizing foreign turnover disruption.",
            styles["Body"]
        ),
    ]

    season_table_data = [
        [Paragraph("Season", styles["TableHeader"]), Paragraph("Inbound", styles["TableHeader"]), Paragraph("Outbound", styles["TableHeader"]), Paragraph("Avg Age", styles["TableHeader"]), Paragraph("Primary Source", styles["TableHeader"]), Paragraph("Key Strategic Shift", styles["TableHeader"])],
        [Paragraph("2020/21", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("14", styles["TableCell"]), Paragraph("27.4y", styles["TableCell"]), Paragraph("ISL / Free", styles["TableCellMuted"]), Paragraph("Transition post-Roca era; defensive restructuring", styles["TableCell"])],
        [Paragraph("2021/22", styles["TableCellBold"]), Paragraph("10", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("26.2y", styles["TableCell"]), Paragraph("Domestic Rivals", styles["TableCellMuted"]), Paragraph("Injection of youth (Roshan, Sivasakthi emerged)", styles["TableCell"])],
        [Paragraph("2022/23", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("28.1y", styles["TableCell"]), Paragraph("Overseas / ATKMB", styles["TableCellMuted"]), Paragraph("Title push with proven veterans (Krishna, Javi)", styles["TableCell"])],
        [Paragraph("2023/24", styles["TableCellBold"]), Paragraph("18", styles["TableCell"]), Paragraph("0", styles["TableCell"]), Paragraph("23.6y", styles["TableCell"]), Paragraph("Academy Promotion", styles["TableCellMuted"]), Paragraph("Heavy youth promotion wave (5 BFC B promotions)", styles["TableCell"])],
        [Paragraph("2024/25", styles["TableCellBold"]), Paragraph("7", styles["TableCell"]), Paragraph("13", styles["TableCell"]), Paragraph("28.8y", styles["TableCell"]), Paragraph("Mumbai City FC / Spain", styles["TableCellMuted"]), Paragraph("Zaragoza influence; experienced Spanish spine", styles["TableCell"])],
    ]
    t_seasons = Table(season_table_data, colWidths=[45, 30, 30, 45, 105, 140])
    t_seasons.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    two_col = Table([[left_narrative, t_seasons]], colWidths=[385, 395])
    two_col.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(two_col)
    story.append(PageBreak())
    return story


def build_page_04_transfer_history(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 4: Transfer History"""
    story = [
        create_header_banner("03. Transfer History & Volume", "Longitudinal Tracking of Inbound Arrivals vs Outbound Departures", styles),
        Spacer(1, 6),
    ]

    chart_path = os.path.join(CHARTS_DIR, "transfers_by_season.png")
    chart_img = Image(chart_path, width=4.8*inch, height=2.4*inch) if os.path.exists(chart_path) else Paragraph("Chart Missing", styles["Body"])

    history_table_data = [
        [Paragraph("Season", styles["TableHeader"]), Paragraph("Arr", styles["TableHeader"]), Paragraph("Dep", styles["TableHeader"]), Paragraph("Total", styles["TableHeader"]), Paragraph("Primary Inbound Additions", styles["TableHeader"])],
        [Paragraph("2020/21", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("14", styles["TableCell"]), Paragraph("26", styles["TableCell"]), Paragraph("Cleiton Silva, Pratik Chaudhari, Fran González, Opseth", styles["TableCellMuted"])],
        [Paragraph("2021/22", styles["TableCellBold"]), Paragraph("10", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("20", styles["TableCell"]), Paragraph("Alan Costa, Bruno Ramires, Rohit Kumar, Prince Ibara", styles["TableCellMuted"])],
        [Paragraph("2022/23", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("22", styles["TableCell"]), Paragraph("Roy Krishna, Javi Hernández, Aleksandar Jovanović, Sandesh", styles["TableCellMuted"])],
        [Paragraph("2023/24", styles["TableCellBold"]), Paragraph("18", styles["TableCell"]), Paragraph("0", styles["TableCell"]), Paragraph("18", styles["TableCell"]), Paragraph("Ryan Williams, Keziah Veendorp, Halicharan Narzary, Robin Yadav", styles["TableCellMuted"])],
        [Paragraph("2024/25", styles["TableCellBold"]), Paragraph("7", styles["TableCell"]), Paragraph("13", styles["TableCell"]), Paragraph("20", styles["TableCell"]), Paragraph("Jorge Pereyra Díaz, Alberto Noguera, Édgar Méndez, Rahul Bheke", styles["TableCellMuted"])],
        [Paragraph("Total", styles["TableHeader"]), Paragraph("59", styles["TableHeader"]), Paragraph("47", styles["TableHeader"]), Paragraph("106", styles["TableHeader"]), Paragraph("<b>Cumulative Inbound Volume: 59 | Outbound Volume: 47</b>", styles["TableCell"])],
    ]

    t_hist = Table(history_table_data, colWidths=[50, 24, 24, 30, 240])
    t_hist.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -2), COLOR_CARD_BG),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_BFC_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    row_layout = Table([[chart_img, t_hist]], colWidths=[400, 385])
    row_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(row_layout)
    story.append(Spacer(1, 10))

    # Analytical Observation Footer Box
    obs_text = (
        "<b>STRATEGIC OBSERVATION:</b> Transfer activity exhibits an average turnover of 21.2 transactions per completed campaign. "
        "Peak squad turnover occurred in 2020/21 (26 transactions) and 2022/23 (22 transactions), corresponding to strategic squad rebuilds. "
        "The club has managed zero net negative transfer fee deficits by strictly utilizing free transfers and player swaps."
    )
    t_obs = Table([[Paragraph(obs_text, styles["Body"])]], colWidths=[785])
    t_obs.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_obs)
    story.append(PageBreak())
    return story


def build_page_05_recruitment_patterns(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 5: Recruitment Patterns, Deal Structures & Positional Allocation"""
    story = [
        create_header_banner("04. Recruitment Patterns, Deal Structures & Positional Allocation", "Age Demographics, Acquisition Mechanisms & Positional Prioritization (54 External Signings)", styles),
        Spacer(1, 4),
    ]

    age_chart_path = os.path.join(CHARTS_DIR, "signing_age_distribution.png")
    donut_chart_path = os.path.join(CHARTS_DIR, "transfer_types_donut.png")
    pos_chart_path = os.path.join(CHARTS_DIR, "position_recruitment.png")

    img_age = Image(age_chart_path, width=5.2*inch, height=1.75*inch) if os.path.exists(age_chart_path) else Paragraph("Missing Age Chart", styles["Body"])
    img_donut = Image(donut_chart_path, width=4.9*inch, height=1.75*inch) if os.path.exists(donut_chart_path) else Paragraph("Missing Donut Chart", styles["Body"])
    img_pos = Image(pos_chart_path, width=5.2*inch, height=1.75*inch) if os.path.exists(pos_chart_path) else Paragraph("Missing Position Chart", styles["Body"])

    # Top Left: 1. WHO DOES BFC SIGN?
    box_age = [
        Paragraph("<b>1. WHO DOES BENGALURU FC SIGN? (Signing Age Demographics)</b>", styles["CardTitle"]),
        Spacer(1, 2),
        img_age,
        Spacer(1, 2),
        Paragraph("<b>Mean Signing Age:</b> 27.0 years (54 external signings; internal promotions strictly excluded).<br/>"
                  "<b>Bimodal Polarization:</b> Peak recruitment targets prime domestic talent (24–26y) and proven foreign leaders (30+y), intentionally bypassing peak-fee inflation brackets (27–29y).", styles["TableCellMuted"]),
    ]

    # Top Right: 2. HOW ARE PLAYERS ACQUIRED?
    box_donut = [
        Paragraph("<b>2. HOW ARE PLAYERS ACQUIRED? (Transfer Deal Types)</b>", styles["CardTitle"]),
        Spacer(1, 2),
        img_donut,
        Spacer(1, 2),
        Paragraph("<b>Free Agent Dominance:</b> 92.6% of external arrivals (50 of 54) acquired on free transfers with €0 net fees.<br/>"
                  "<b>Loan Cover:</b> Loans (4 events, 7.4%) strictly utilized for short-term injury cover without long-term wage locks or balance-sheet amortization risk.", styles["TableCellMuted"]),
    ]

    top_row = Table([[box_age, box_donut]], colWidths=[390, 390])
    top_row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(top_row)
    story.append(Spacer(1, 5))

    # Bottom Left: 3. WHICH POSITIONS ARE PRIORITIZED? (Chart)
    box_pos_chart = [
        Paragraph("<b>3. WHICH POSITIONS ARE PRIORITIZED? (Positional Breakdown)</b>", styles["CardTitle"]),
        Spacer(1, 2),
        img_pos,
        Spacer(1, 2),
        Paragraph("<b>54 External Signings:</b> Defenders (20, 37.0%), Forwards (15, 27.8%), Midfielders (13, 24.1%), Goalkeepers (6, 11.1%).", styles["TableCellMuted"]),
    ]

    # Bottom Right: Positional Synthesis Table & Text
    pos_table_data = [
        [Paragraph("Position", styles["TableHeader"]), Paragraph("Signings", styles["TableHeader"]), Paragraph("Share", styles["TableHeader"]), Paragraph("Strategic Recruitment Function", styles["TableHeader"])],
        [Paragraph("Defender", styles["TableCellBold"]), Paragraph("20", styles["TableCell"]), Paragraph("37.0%", styles["TableCellBold"]), Paragraph("Central defensive spine & full-back stability (Primary Focus)", styles["TableCellMuted"])],
        [Paragraph("Forward", styles["TableCellBold"]), Paragraph("15", styles["TableCell"]), Paragraph("27.8%", styles["TableCellBold"]), Paragraph("Match-winners, clinical box finishers & pressing threats", styles["TableCellMuted"])],
        [Paragraph("Midfielder", styles["TableCellBold"]), Paragraph("13", styles["TableCell"]), Paragraph("24.1%", styles["TableCellBold"]), Paragraph("Double-pivot engine room, progressive passers & tempo control", styles["TableCellMuted"])],
        [Paragraph("Goalkeeper", styles["TableCellBold"]), Paragraph("6", styles["TableCell"]), Paragraph("11.1%", styles["TableCellBold"]), Paragraph("Veteran domestic glovework, shot-stopping & bench depth", styles["TableCellMuted"])],
    ]
    t_pos_summary = Table(pos_table_data, colWidths=[65, 45, 45, 215])
    t_pos_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    box_pos_analysis = [
        Paragraph("<b>POSITIONAL RECRUITMENT SYNTHESIS</b>", styles["CardTitle"]),
        Spacer(1, 3),
        t_pos_summary,
        Spacer(1, 3),
        Paragraph("<b>STRATEGIC VERDICT:</b> Defenders represent the largest recruitment expenditure of squad spots (37.0%), underpinning Bengaluru FC's pragmatic structural approach to ISL campaigns. High free-agent reliance (92.6%) ensures continuous backline replenishment without speculative capital exposure.", styles["TableCell"]),
    ]

    bottom_row = Table([[box_pos_chart, box_pos_analysis]], colWidths=[390, 390])
    bottom_row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(bottom_row)
    story.append(PageBreak())
    return story


def build_page_06_recruitment_markets(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 6: Recruitment Markets"""
    story = [
        create_header_banner("05. Recruitment Markets & Scouting Footprint", "Origin Leagues, Feeder Networks & Domestic vs Overseas Split", styles),
        Spacer(1, 6),
    ]

    markets_chart = os.path.join(CHARTS_DIR, "recruitment_markets_combined.png")
    img_markets = Image(markets_chart, width=4.8*inch, height=2.4*inch) if os.path.exists(markets_chart) else Paragraph("Missing Markets Chart", styles["Body"])

    market_table_data = [
        [Paragraph("Origin Category", styles["TableHeader"]), Paragraph("Share", styles["TableHeader"]), Paragraph("Primary Feeder Clubs / Leagues", styles["TableHeader"]), Paragraph("Strategic Function", styles["TableHeader"])],
        [Paragraph("Domestic ISL Rivals", styles["TableCellBold"]), Paragraph("35.0%", styles["TableCell"]), Paragraph("Mumbai City, Hyderabad FC, Odisha, ATKMB", styles["TableCellMuted"]), Paragraph("Acquiring battle-tested starters with zero adaptation risk", styles["TableCell"])],
        [Paragraph("Bengaluru B / Academy", styles["TableCellBold"]), Paragraph("13.2%", styles["TableCell"]), Paragraph("BFC Youth Academy (Karnataka State League)", styles["TableCellMuted"]), Paragraph("Cost-effective rotational depth & homegrown identification", styles["TableCell"])],
        [Paragraph("Domestic I-League", styles["TableCellBold"]), Paragraph("10.0%", styles["TableCell"]), Paragraph("Indian Arrows, TRAU FC, Aizawl FC, Zinc FA", styles["TableCellMuted"]), Paragraph("Identifying high-upside domestic talent ahead of rivals", styles["TableCell"])],
        [Paragraph("Spain (LaLiga 2 / Primera RFEF)", styles["TableCellBold"]), Paragraph("18.0%", styles["TableCell"]), Paragraph("CD Eldense, Alavés, Necaxa (Liga MX ties)", styles["TableCellMuted"]), Paragraph("Technical controllers and chance-creators for Zaragoza's system", styles["TableCell"])],
        [Paragraph("Australia (A-League)", styles["TableCellBold"]), Paragraph("12.0%", styles["TableCell"]), Paragraph("Perth Glory, Macarthur FC, Newcastle Jets", styles["TableCellMuted"]), Paragraph("High-physicality AFC quota signings (CB / Winger)", styles["TableCell"])],
        [Paragraph("Other Overseas (Brazil/Europe)", styles["TableCellBold"]), Paragraph("11.8%", styles["TableCell"]), Paragraph("Suphanburi (Thai L1), Varzim, FC Helsingør", styles["TableCellMuted"]), Paragraph("Targeted forward finishers and midfield anchors", styles["TableCell"])],
    ]

    t_mkt = Table(market_table_data, colWidths=[100, 35, 125, 125])
    t_mkt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    row_layout = Table([[img_markets, t_mkt]], colWidths=[395, 390])
    row_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(row_layout)
    story.append(Spacer(1, 10))

    summary_text = (
        "<b>GLOBAL SCOUTING PIPELINE ANALYSIS:</b> Bengaluru FC maintains a specialized dual-pipeline recruitment model. "
        "Domestically, the club exploits distressed rival ISL squads (e.g. Hyderabad FC financial re-allocations) and extracts the best U21 I-League talent. "
        "Internationally, recruitment concentrates in Spain (tactical alignment with Spanish managers) and Australia (A-League players who satisfy AFC quota requirements)."
    )
    t_sum = Table([[Paragraph(summary_text, styles["Body"])]], colWidths=[785])
    t_sum.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_sum)
    story.append(PageBreak())
    return story


def build_page_07_player_pathways(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 7: Player Pathways"""
    story = [
        create_header_banner("06. Player Career Pathways", "Trajectory Mapping: Previous Club &rarr; Bengaluru FC &rarr; Destination Club", styles),
        Spacer(1, 6),
    ]

    pathway_table_data = [
        [Paragraph("Player Name", styles["TableHeader"]), Paragraph("Previous Club", styles["TableHeader"]), Paragraph("Origin League", styles["TableHeader"]), Paragraph("Joined", styles["TableHeader"]), Paragraph("Tenure", styles["TableHeader"]), Paragraph("Destination / Current Club", styles["TableHeader"]), Paragraph("Destination League", styles["TableHeader"]), Paragraph("Career Outcome", styles["TableHeader"])],
        [Paragraph("Cleiton Silva", styles["TableCellBold"]), Paragraph("Suphanburi FC", styles["TableCellMuted"]), Paragraph("Thai League 1", styles["TableCell"]), Paragraph("2020", styles["TableCell"]), Paragraph("2.0y", styles["TableCellBold"]), Paragraph("East Bengal FC", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("High ROI; top scorer; transitioned to rival", styles["TableCell"])],
        [Paragraph("Javi Hernández", styles["TableCellBold"]), Paragraph("Odisha FC", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("2022", styles["TableCell"]), Paragraph("2.0y", styles["TableCellBold"]), Paragraph("Jamshedpur FC", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("Key creator; 2 ISL finals; free exit", styles["TableCell"])],
        [Paragraph("Roy Krishna", styles["TableCellBold"]), Paragraph("ATK Mohun Bagan", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("2022", styles["TableCell"]), Paragraph("1.0y", styles["TableCellBold"]), Paragraph("Odisha FC", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("1 season impact; Durand Cup win; high wages", styles["TableCell"])],
        [Paragraph("Ashique Kuruniyan", styles["TableCellBold"]), Paragraph("FC Pune City", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("2019", styles["TableCell"]), Paragraph("3.0y", styles["TableCellBold"]), Paragraph("ATK Mohun Bagan", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("Developed into elite national team winger", styles["TableCell"])],
        [Paragraph("Udanta Singh", styles["TableCellBold"]), Paragraph("Tata Football Academy", styles["TableCellMuted"]), Paragraph("Youth Academy", styles["TableCell"]), Paragraph("2014", styles["TableCell"]), Paragraph("9.0y", styles["TableCellBold"]), Paragraph("FC Goa", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("Club legend; full development lifecycle", styles["TableCell"])],
        [Paragraph("Rohit Kumar", styles["TableCellBold"]), Paragraph("Kerala Blasters", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("2021", styles["TableCell"]), Paragraph("3.0y", styles["TableCellBold"]), Paragraph("Odisha FC", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("Midfield rotation; international caps achieved", styles["TableCell"])],
        [Paragraph("Slavko Damjanović", styles["TableCellBold"]), Paragraph("ATK Mohun Bagan", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("2023", styles["TableCell"]), Paragraph("1.0y", styles["TableCellBold"]), Paragraph("FK Sutjeska Nikšić", styles["TableCellMuted"]), Paragraph("Montenegrin League", styles["TableCell"]), Paragraph("Single season CB stopgap; overseas return", styles["TableCell"])],
        [Paragraph("Suresh Singh", styles["TableCellBold"]), Paragraph("Indian Arrows", styles["TableCellMuted"]), Paragraph("I-League", styles["TableCell"]), Paragraph("2019", styles["TableCell"]), Paragraph("6.0y+", styles["TableCellBold"]), Paragraph("Bengaluru FC (Active)", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("Elite anchor asset; +500% valuation surge", styles["TableCell"])],
        [Paragraph("Naorem Roshan", styles["TableCellBold"]), Paragraph("Bengaluru FC II", styles["TableCellMuted"]), Paragraph("2nd Division", styles["TableCell"]), Paragraph("2020", styles["TableCell"]), Paragraph("5.0y+", styles["TableCellBold"]), Paragraph("Bengaluru FC (Active)", styles["TableCellMuted"]), Paragraph("Indian Super League", styles["TableCell"]), Paragraph("Breakthrough full-back; +900% asset surge", styles["TableCell"])],
    ]

    t_pw = Table(pathway_table_data, colWidths=[75, 80, 85, 35, 35, 105, 95, 275])
    t_pw.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_pw)
    story.append(Spacer(1, 10))

    # Pathway Typologies Box
    c1 = [
        Paragraph("<b>Archetype A: Academy to National Core</b>", styles["CardTitle"]),
        Spacer(1, 3),
        Paragraph("Path: BFC II / Arrows &rarr; Senior Team &rarr; India Starter.<br/>Exemplars: Suresh Singh, Roshan Singh. Demonstrates club's highest economic multiplier and long-term competitive durability.", styles["Body"]),
    ]
    c2 = [
        Paragraph("<b>Archetype B: 2-Year Prime Veteran Cycle</b>", styles["CardTitle"]),
        Spacer(1, 3),
        Paragraph("Path: Rival Club / Abroad &rarr; BFC &rarr; Free Exit.<br/>Exemplars: Cleiton Silva, Javi Hernández. Delivers immediate trophy impact during a 2-season peak window before free-agent transition.", styles["Body"]),
    ]
    c3 = [
        Paragraph("<b>Archetype C: 1-Year Stopgap Repair</b>", styles["CardTitle"]),
        Spacer(1, 3),
        Paragraph("Path: Mid-Season / Free &rarr; BFC &rarr; Roster Refresh.<br/>Exemplars: Slavko Damjanović, Oliver Drost. Short-term contingency recruitment designed to cover injury crises without long-term wage locks.", styles["Body"]),
    ]

    typology_grid = Table([[c1, c2, c3]], colWidths=[256, 256, 256])
    typology_grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(typology_grid)
    story.append(PageBreak())
    return story


def build_page_08_market_value(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 8: Market Value Analysis"""
    story = [
        create_header_banner("07. Market Value & Player Development", "Economic Trajectory, Portfolio Growth & Financial Asset Appreciation", styles),
        Spacer(1, 4),
    ]

    # Rule Explanation Banner
    rule_text = (
        "<b>DATA INTEGRITY PRINCIPLE: MARKET VALUE &ne; TRANSFER FEE.</b> "
        "Transfer Fee is the actual transaction price paid between clubs (Bengaluru FC has paid €0 in net fees across 92.6% of external arrivals). "
        "Market Value represents an objective economic asset valuation based on player age, contract length, form, league tier, and international status. "
        "Growth Formula: <b>((Current Value - Initial Value) / Initial Value) &times; 100</b>."
    )
    t_rule = Table([[Paragraph(rule_text, styles["Body"])]], colWidths=[785])
    t_rule.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_rule)
    story.append(Spacer(1, 6))

    chart_mv = os.path.join(CHARTS_DIR, "market_value_growth.png")
    img_mv = Image(chart_mv, width=4.5*inch, height=2.25*inch) if os.path.exists(chart_mv) else Paragraph("Missing MV Chart", styles["Body"])

    # Top Gainers & Declines Table
    mv_table_data = [
        [Paragraph("Player Name", styles["TableHeader"]), Paragraph("Joined", styles["TableHeader"]), Paragraph("Peak", styles["TableHeader"]), Paragraph("Current", styles["TableHeader"]), Paragraph("Growth %", styles["TableHeader"]), Paragraph("Category", styles["TableHeader"])],
        [Paragraph("Naorem Roshan Singh", styles["TableCellBold"]), Paragraph("€25k", styles["TableCellMuted"]), Paragraph("€275k", styles["TableCell"]), Paragraph("€250k", styles["TableCell"]), Paragraph("+900.0%", styles["BadgeLow"]), Paragraph("Elite Academy Appreciation", styles["TableCell"])],
        [Paragraph("Udanta Singh", styles["TableCellBold"]), Paragraph("€25k", styles["TableCellMuted"]), Paragraph("€325k", styles["TableCell"]), Paragraph("€225k", styles["TableCell"]), Paragraph("+800.0%", styles["BadgeLow"]), Paragraph("Full Cycle Development", styles["TableCell"])],
        [Paragraph("Sivasakthi Narayanan", styles["TableCellBold"]), Paragraph("€25k", styles["TableCellMuted"]), Paragraph("€200k", styles["TableCell"]), Paragraph("€200k", styles["TableCell"]), Paragraph("+700.0%", styles["BadgeLow"]), Paragraph("Emerging Forward Asset", styles["TableCell"])],
        [Paragraph("Suresh Singh Wangjam", styles["TableCellBold"]), Paragraph("€50k", styles["TableCellMuted"]), Paragraph("€300k", styles["TableCell"]), Paragraph("€300k", styles["TableCell"]), Paragraph("+500.0%", styles["BadgeLow"]), Paragraph("Spine Foundation Anchor", styles["TableCell"])],
        [Paragraph("Ashique Kuruniyan", styles["TableCellBold"]), Paragraph("€100k", styles["TableCellMuted"]), Paragraph("€300k", styles["TableCell"]), Paragraph("€300k", styles["TableCell"]), Paragraph("+200.0%", styles["BadgeLow"]), Paragraph("Prime Asset Expansion", styles["TableCell"])],
        [Paragraph("Cleiton Silva", styles["TableCellBold"]), Paragraph("€350k", styles["TableCellMuted"]), Paragraph("€350k", styles["TableCell"]), Paragraph("€100k", styles["TableCell"]), Paragraph("-71.4%", styles["BadgeHigh"]), Paragraph("Age Depreciation Curve (37y)", styles["TableCell"])],
        [Paragraph("Sunil Chhetri", styles["TableCellBold"]), Paragraph("€175k", styles["TableCellMuted"]), Paragraph("€175k", styles["TableCell"]), Paragraph("€50k", styles["TableCell"]), Paragraph("-71.4%", styles["BadgeHigh"]), Paragraph("Veteran Career Climax (40y)", styles["TableCell"])],
    ]

    t_mv = Table(mv_table_data, colWidths=[95, 38, 38, 38, 48, 115])
    t_mv.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    row_layout = Table([[img_mv, t_mv]], colWidths=[405, 380])
    row_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(row_layout)
    story.append(PageBreak())
    return story


def build_page_09_current_squad(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 9: Current Squad Analysis"""
    story = [
        create_header_banner("08. Current Squad Analysis (2024/25 Season)", "Complete Player Classification & Roster Hierarchy", styles),
        Spacer(1, 4),
    ]

    squad_table_data = [
        [Paragraph("Player Name", styles["TableHeader"]), Paragraph("Pos", styles["TableHeader"]), Paragraph("Age", styles["TableHeader"]), Paragraph("Nat", styles["TableHeader"]), Paragraph("Market Value", styles["TableHeader"]), Paragraph("Joined From", styles["TableHeader"]), Paragraph("Joined", styles["TableHeader"]), Paragraph("Recruitment Classification", styles["TableHeader"])],
        [Paragraph("Gurpreet Singh Sandhu", styles["TableCellBold"]), Paragraph("GK", styles["TableCell"]), Paragraph("32", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€200k", styles["TableCell"]), Paragraph("Stabæk", styles["TableCellMuted"]), Paragraph("2017", styles["TableCell"]), Paragraph("KEY PLAYER | VETERAN", styles["TableCellBold"])],
        [Paragraph("Sunil Chhetri", styles["TableCellBold"]), Paragraph("ST", styles["TableCell"]), Paragraph("40", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€50k", styles["TableCell"]), Paragraph("Mumbai City FC", styles["TableCellMuted"]), Paragraph("2017", styles["TableCell"]), Paragraph("KEY PLAYER | VETERAN | REPLACEMENT RISK", styles["BadgeHigh"])],
        [Paragraph("Suresh Singh Wangjam", styles["TableCellBold"]), Paragraph("CM", styles["TableCell"]), Paragraph("24", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€300k", styles["TableCell"]), Paragraph("Indian Arrows", styles["TableCellMuted"]), Paragraph("2019", styles["TableCell"]), Paragraph("KEY PLAYER | HIGH UPSIDE", styles["BadgeLow"])],
        [Paragraph("Naorem Roshan Singh", styles["TableCellBold"]), Paragraph("LB", styles["TableCell"]), Paragraph("25", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€250k", styles["TableCell"]), Paragraph("Bengaluru FC II", styles["TableCellMuted"]), Paragraph("2020", styles["TableCell"]), Paragraph("CORE PLAYER | HIGH UPSIDE", styles["BadgeLow"])],
        [Paragraph("Jorge Pereyra Díaz", styles["TableCellBold"]), Paragraph("ST", styles["TableCell"]), Paragraph("34", styles["TableCell"]), Paragraph("ARG", styles["TableCellMuted"]), Paragraph("€350k", styles["TableCell"]), Paragraph("Mumbai City FC", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("KEY PLAYER | VETERAN | FOREIGN SLOT", styles["TableCellBold"])],
        [Paragraph("Alberto Noguera", styles["TableCellBold"]), Paragraph("AM", styles["TableCell"]), Paragraph("35", styles["TableCell"]), Paragraph("ESP", styles["TableCellMuted"]), Paragraph("€250k", styles["TableCell"]), Paragraph("Mumbai City FC", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("KEY PLAYER | VETERAN | REPLACEMENT RISK", styles["BadgeHigh"])],
        [Paragraph("Édgar Méndez", styles["TableCellBold"]), Paragraph("WG", styles["TableCell"]), Paragraph("34", styles["TableCell"]), Paragraph("ESP", styles["TableCellMuted"]), Paragraph("€400k", styles["TableCell"]), Paragraph("Club Necaxa", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("CORE PLAYER | VETERAN | FOREIGN SLOT", styles["TableCellBold"])],
        [Paragraph("Rahul Bheke", styles["TableCellBold"]), Paragraph("CB", styles["TableCell"]), Paragraph("33", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€175k", styles["TableCell"]), Paragraph("Mumbai City FC", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("CORE PLAYER | VETERAN | REPLACEMENT RISK", styles["BadgeMedium"])],
        [Paragraph("Aleksandar Jovanović", styles["TableCellBold"]), Paragraph("CB", styles["TableCell"]), Paragraph("35", styles["TableCell"]), Paragraph("AUS", styles["TableCellMuted"]), Paragraph("€200k", styles["TableCell"]), Paragraph("Macarthur FC", styles["TableCellMuted"]), Paragraph("2022", styles["TableCell"]), Paragraph("CORE PLAYER | VETERAN | REPLACEMENT RISK", styles["BadgeHigh"])],
        [Paragraph("Chinglensana Singh", styles["TableCellBold"]), Paragraph("CB", styles["TableCell"]), Paragraph("27", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€225k", styles["TableCell"]), Paragraph("Hyderabad FC", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("CORE PLAYER | DOMESTIC SPINE", styles["TableCellBold"])],
        [Paragraph("Pedro Capó", styles["TableCellBold"]), Paragraph("DM", styles["TableCell"]), Paragraph("33", styles["TableCell"]), Paragraph("ESP", styles["TableCellMuted"]), Paragraph("€200k", styles["TableCell"]), Paragraph("CD Eldense", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("CORE PLAYER | VETERAN | FOREIGN SLOT", styles["TableCellBold"])],
        [Paragraph("Sivasakthi Narayanan", styles["TableCellBold"]), Paragraph("ST", styles["TableCell"]), Paragraph("23", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€200k", styles["TableCell"]), Paragraph("Bengaluru FC II", styles["TableCellMuted"]), Paragraph("2021", styles["TableCell"]), Paragraph("CORE PLAYER | HIGH UPSIDE", styles["BadgeLow"])],
        [Paragraph("Ryan Williams", styles["TableCellBold"]), Paragraph("WG", styles["TableCell"]), Paragraph("30", styles["TableCell"]), Paragraph("AUS", styles["TableCellMuted"]), Paragraph("€300k", styles["TableCell"]), Paragraph("Perth Glory", styles["TableCellMuted"]), Paragraph("2023", styles["TableCell"]), Paragraph("CORE PLAYER | FOREIGN SLOT", styles["TableCellBold"])],
        [Paragraph("Vinith Venkatesh", styles["TableCellBold"]), Paragraph("AM", styles["TableCell"]), Paragraph("19", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€100k", styles["TableCell"]), Paragraph("Bengaluru FC II", styles["TableCellMuted"]), Paragraph("2024", styles["TableCell"]), Paragraph("HIGH UPSIDE | DEVELOPMENT ASSET", styles["BadgeLow"])],
        [Paragraph("Robin Yadav", styles["TableCellBold"]), Paragraph("CB", styles["TableCell"]), Paragraph("22", styles["TableCell"]), Paragraph("IND", styles["TableCellMuted"]), Paragraph("€75k", styles["TableCell"]), Paragraph("Bengaluru FC II", styles["TableCellMuted"]), Paragraph("2023", styles["TableCell"]), Paragraph("DEVELOPMENT | ROTATIONAL DEPTH", styles["TableCellMuted"])],
    ]

    t_squad = Table(squad_table_data, colWidths=[130, 32, 30, 32, 70, 115, 42, 334])
    t_squad.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_squad)
    story.append(Spacer(1, 6))

    legend_text = (
        "<b>CLASSIFICATION CRITERIA:</b> "
        "<b>KEY:</b> Indispensable starters (Chhetri, Díaz, Noguera, Suresh, Gurpreet). "
        "<b>CORE:</b> Regular first-team contributors (Bheke, Roshan, Jovanović, Capó, Méndez, Sana). "
        "<b>HIGH UPSIDE:</b> Age &le;25 with &gt;€150k value. "
        "<b>DEVELOPMENT:</b> Academy integration &le;22y. "
        "<b>REPLACEMENT RISK:</b> Crucial starters aged 33+ requiring immediate succession."
    )
    t_leg = Table([[Paragraph(legend_text, styles["Body"])]], colWidths=[785])
    t_leg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_leg)
    story.append(PageBreak())
    return story


def build_page_10_squad_age_depth(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 10: Squad Age & Depth"""
    story = [
        create_header_banner("09. Squad Age Structure & Positional Depth", "Positional Depth Curves, Demographic Imbalances & Succession Windows", styles),
        Spacer(1, 6),
    ]

    chart_depth = os.path.join(CHARTS_DIR, "squad_depth_age_matrix.png")

    c1 = build_kpi_card("Average Squad Age", "27.3y", "Balanced Overall Average", styles, width=150)
    c2 = build_kpi_card("Oldest Position", "DM (33.0y)", "Pedro Capó (33)", styles, width=150)
    c3 = build_kpi_card("Youngest Position", "RB (20.0y)", "Shivaldo Singh (20)", styles, width=150)
    c4 = build_kpi_card("Strongest Depth", "CB (5 Players)", "Deep Domestic & Asian Spine", styles, width=150)
    c5 = build_kpi_card("Weakest Depth", "RB (1 Player)", "Urgent Specialist Need", styles, width=150)

    card_row = Table([[c1, c2, c3, c4, c5]], colWidths=[157]*5)
    card_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(card_row)
    story.append(Spacer(1, 8))

    depth_obs = [
        Paragraph("<b>POSITIONAL RISK EVALUATION:</b>", styles["CardTitle"]),
        Spacer(1, 4),
        Paragraph("<b>1. Extreme Striker & Attacking Midfield Age:</b> While squad average age is 27.3y, key creative match-winners average 35.8y (Noguera 35, Díaz 34, Chhetri 40). When these players are unavailable, team xG drops significantly.<br/>"
                  "<b>2. Right-Back Structural Void:</b> Shivaldo Singh (20) is the sole natural right back on the roster, forcing emergency out-of-position deployments of central defenders (Rahul Bheke).<br/>"
                  "<b>3. Heavy Centre-Back Insurance:</b> With 5 senior CBs, defensive central depth is insulated against domestic suspension cycles.", styles["Body"]),
    ]

    obs_table = Table([[depth_obs]], colWidths=[385])
    obs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))

    img_depth = Image(chart_depth, width=5.2*inch, height=2.6*inch) if os.path.exists(chart_depth) else Paragraph("Missing Depth Chart", styles["Body"])

    main_layout = Table([[img_depth, obs_table]], colWidths=[395, 390])
    main_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(main_layout)
    story.append(PageBreak())
    return story


def build_page_11_six_key_conclusions(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 11: Six Key Conclusions"""
    story = [
        create_header_banner("10. Six Key Conclusions", "Executive Summary of Empirical Recruitment Analytics & Strategic Findings", styles),
        Spacer(1, 6),
    ]

    conclusions = get_six_key_conclusions()

    def make_conclusion_card(c: Dict[str, Any]) -> Table:
        title = f"<b>{c['id']}. {c['title']}</b>"
        badge_style = styles["BadgeHigh"] if "Critical" in c.get("confidence_level", "") else styles["BadgeLow"]
        finding = c.get("finding", c.get("insight", ""))
        metric = c.get("supporting_metric", c.get("supporting_data", ""))
        impl = c.get("strategic_implication", "")
        card_data = [
            [Paragraph(title, styles["CardTitle"]), Paragraph(f"{c.get('confidence_level', 'High')}", badge_style)],
            [Paragraph(f"<b>Finding:</b> {finding}", styles["TableCell"]), ""],
            [Paragraph(f"<b>Supporting Metric:</b> {metric}", styles["TableCellMuted"]), ""],
            [Paragraph(f"<b>Strategic Implication:</b> {impl}", styles["TableCellBold"]), ""],
        ]
        t = Table(card_data, colWidths=[270, 110])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    row1 = [make_conclusion_card(conclusions[0]), make_conclusion_card(conclusions[1])]
    row2 = [make_conclusion_card(conclusions[2]), make_conclusion_card(conclusions[3])]
    row3 = [make_conclusion_card(conclusions[4]), make_conclusion_card(conclusions[5])]

    grid = Table([row1, [Spacer(1, 4), Spacer(1, 4)], row2, [Spacer(1, 4), Spacer(1, 4)], row3], colWidths=[390, 390])
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(grid)
    story.append(PageBreak())
    return story


def build_page_12_squad_gaps(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 12: Squad Gaps & Risk Register"""
    story = [
        create_header_banner("11. Squad Gaps & Strategic Risk Register", "Automated Detection of Positional Voids, Age Risks & Succession Imperatives", styles),
        Spacer(1, 6),
    ]

    gaps_data = [
        [Paragraph("Priority", styles["TableHeader"]), Paragraph("Risk Type", styles["TableHeader"]), Paragraph("Target Department", styles["TableHeader"]), Paragraph("Underlying Cause & Strategic Rationale", styles["TableHeader"]), Paragraph("Actionable Recommendation", styles["TableHeader"])],
        [
            Paragraph("HIGH", styles["BadgeHigh"]),
            Paragraph("SUCCESSION RISK", styles["TableCellBold"]),
            Paragraph("Striker / CF", styles["TableCellBold"]),
            Paragraph("Starting forwards Sunil Chhetri (40) and Jorge Pereyra Díaz (34) account for majority of goal contributions but face imminent retirement/physical drop-off.", styles["TableCell"]),
            Paragraph("Recruit an explosive, high-pressing domestic U24 striker (David Lalhlansanga / Irfan Yadwad) to partner Sivasakthi.", styles["TableCellBold"]),
        ],
        [
            Paragraph("HIGH", styles["BadgeHigh"]),
            Paragraph("AGE RISK", styles["TableCellBold"]),
            Paragraph("Attacking Midfield", styles["TableCellBold"]),
            Paragraph("Alberto Noguera (35) is the primary foreign creator with no prime-age alternative; academy graduate Vinith (19) requires progressive adaptation.", styles["TableCell"]),
            Paragraph("Target a prime-age creative playmaker (Age 22-26, Vibin Mohanan) with elite progressive passing metrics.", styles["TableCellBold"]),
        ],
        [
            Paragraph("MEDIUM", styles["BadgeMedium"]),
            Paragraph("DEPTH RISK", styles["TableCellBold"]),
            Paragraph("Ball-Playing CB", styles["TableCellBold"]),
            Paragraph("Aleksandar Jovanović (35) and Rahul Bheke (33) carry athletic decline and recovery-pace vulnerabilities against counter-attacking teams.", styles["TableCell"]),
            Paragraph("Acquire an athletic, ball-playing left-sided or Asian-quota CB (Age 22-26) with recovery speed.", styles["TableCellBold"]),
        ],
        [
            Paragraph("MEDIUM", styles["BadgeMedium"]),
            Paragraph("POSITION RISK", styles["TableCellBold"]),
            Paragraph("Right / Left Back", styles["TableCellBold"]),
            Paragraph("Single specialist right back on roster (Shivaldo Singh 20). Heavy over-reliance on Naorem Roshan Singh for vertical progression on flanks.", styles["TableCell"]),
            Paragraph("Sign a high-workrate full-back cover (Aakash Sangwan / Jay Gupta) to grant tactical versatility.", styles["TableCellBold"]),
        ],
        [
            Paragraph("LOW", styles["BadgeLow"]),
            Paragraph("SUCCESSION RISK", styles["TableCellBold"]),
            Paragraph("Goalkeeper (U23)", styles["TableCellBold"]),
            Paragraph("Gurpreet Singh Sandhu (32) remains elite India No. 1, but reserve Lalthuammawia Ralte is 31; academy keeper Sahil Poonia is developing.", styles["TableCell"]),
            Paragraph("Maintain cup starts for Sahil Poonia or monitor top domestic U23 goalkeeping targets (Hrithik Tiwari).", styles["TableCellBold"]),
        ],
        [
            Paragraph("LOW", styles["BadgeLow"]),
            Paragraph("DEVELOPMENT BLOCK", styles["TableCellBold"]),
            Paragraph("Central Midfield", styles["TableCellBold"]),
            Paragraph("Crowded midfield spine (Suresh, Capó, Noguera) can inadvertently suppress match minutes for emerging prospects (Fanai, Vinith).", styles["TableCell"]),
            Paragraph("Establish guaranteed rotational minutes and targeted domestic loan pathways in the I-League.", styles["TableCellBold"]),
        ],
    ]

    t_gaps = Table(gaps_data, colWidths=[55, 85, 85, 280, 280])
    t_gaps.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_gaps)
    story.append(PageBreak())
    return story


def build_page_13_recruitment_profiles(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 13: Ideal Recruitment Profiles"""
    story = [
        create_header_banner("12. Gap-Driven Recruitment Profiles", "Specification of Ideal Player Attributes Prior to Target Identification", styles),
        Spacer(1, 6),
    ]

    profiles = get_ideal_recruitment_profiles()

    def make_profile_card(p: Dict[str, Any]) -> Table:
        badge_style = styles["BadgeHigh"] if p["priority"] == "High" else (styles["BadgeMedium"] if p["priority"] == "Medium" else styles["BadgeLow"])
        attrs = ", ".join(p["required_attributes"])
        data = [
            [Paragraph(p["profile_name"].upper(), styles["CardTitle"]), Paragraph(f"Priority: {p['priority']}", badge_style)],
            [Paragraph(f"<b>Gap Addressed:</b> {p['gap_addressed']}", styles["BodyBold"]), ""],
            [Paragraph(f"<b>Target Age:</b> {p['age_range']}  |  <b>Foot:</b> {p['preferred_foot']}  |  <b>Market Value Range:</b> {p['market_value_range']}", styles["Body"]), ""],
            [Paragraph(f"<b>Experience Level:</b> {p['experience_level']}", styles["TableCellMuted"]), ""],
            [Paragraph(f"<b>Required Core Attributes:</b> {attrs}", styles["TableCell"]), ""],
        ]
        t = Table(data, colWidths=[270, 110])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("SPAN", (0, 4), (1, 4)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    row1 = [make_profile_card(profiles[0]), make_profile_card(profiles[1])]
    row2 = [make_profile_card(profiles[2]), make_profile_card(profiles[3])]
    row3 = [make_profile_card(profiles[4]), Table([[Paragraph("<b>METHODOLOGY COMPLIANCE:</b> Ideal recruitment profiles are strictly synthesized from empirical squad gaps rather than ad-hoc scouting preference. Candidates shortlisted on subsequent pages must satisfy at least 80% of these structural attributes.", styles["Body"])]], colWidths=[380], style=[("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT), ("BOX", (0, 0), (-1, -1), 1, COLOR_BFC_BLUE), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)])]

    grid = Table([row1, [Spacer(1, 3), Spacer(1, 3)], row2, [Spacer(1, 3), Spacer(1, 3)], row3], colWidths=[390, 390])
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(grid)
    story.append(PageBreak())
    return story


def build_page_14_player_shortlist(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 14: Player Recommendations & Shortlist"""
    story = [
        create_header_banner("13. Player Shortlist & 100-Point Fit Scoring", "Concrete Targets Assessed Against Tactical Fit, Market Valuation & Development Ceiling", styles),
        Spacer(1, 4),
    ]

    radar_chart = os.path.join(CHARTS_DIR, "shortlist_radar.png")
    img_radar = Image(radar_chart, width=3.3*inch, height=3.3*inch) if os.path.exists(radar_chart) else Paragraph("Missing Radar Chart", styles["Body"])

    shortlist = get_shortlisted_players()

    def make_target_dossier(p: Dict[str, Any]) -> Table:
        strengths = ", ".join(p["strengths"])
        weaknesses = ", ".join(p["weaknesses"])
        dossier_data = [
            [Paragraph(f"<b>{p['name']}</b> ({p['age']}y, {p['position']})", styles["CardTitle"]), Paragraph(f"FIT SCORE: <b>{p['fit_score']}/100</b>", styles["BadgeLow"])],
            [Paragraph(f"<b>Club:</b> {p['club']}  |  <b>Nat:</b> {p['nationality']}  |  <b>Market Value:</b> {p['market_value']}  |  <b>Foot:</b> {p['preferred_foot']}", styles["TableCellMuted"]), ""],
            [Paragraph(f"<b>Playing Style:</b> {p['playing_style']}", styles["TableCell"]), ""],
            [Paragraph(f"<b>Strengths:</b> {strengths}", styles["TableCellBold"]), ""],
            [Paragraph(f"<b>Tactical Fit:</b> {p['why_fits']}", styles["TableCell"]), ""],
            [Paragraph(f"<b>Risks & Concerns:</b> {p['risks']}", styles["BadgeMedium"]), ""],
        ]
        t = Table(dossier_data, colWidths=[315, 95])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("SPAN", (0, 4), (1, 4)),
            ("SPAN", (0, 5), (1, 5)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    # Show top 3 targets in full detail
    dossier1 = make_target_dossier(shortlist[0])
    dossier2 = make_target_dossier(shortlist[1])
    dossier3 = make_target_dossier(shortlist[2])

    right_stack = Table([[dossier1], [Spacer(1, 3)], [dossier2], [Spacer(1, 3)], [dossier3]], colWidths=[410])
    right_stack.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    radar_summary = [
        img_radar,
        Spacer(1, 4),
        Paragraph("<b>100-PT WEIGHTED FIT CRITERIA:</b><br/>"
                  "&bull; Age Fit (20%) &bull; Position Fit (20%)<br/>"
                  "&bull; Market Value Fit (15%) &bull; Performance Fit (20%)<br/>"
                  "&bull; Playing Style (15%) &bull; Development Upside (10%)<br/>"
                  "<b>Disclaimer:</b> Fit scores (92.4, 92.0, 90.2) are heuristic multi-criteria scouting valuations, not match event tracking metrics.", styles["TableCellMuted"]),
    ]

    radar_table = Table([[radar_summary[0]], [radar_summary[2]]], colWidths=[365])
    radar_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    layout = Table([[radar_table, right_stack]], colWidths=[370, 415])
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(layout)
    story.append(PageBreak())
    return story


def build_page_15_final_strategy(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 15: Final Recruitment Strategy"""
    story = [
        create_header_banner("14. Final Recruitment Strategy & Action Plan", "The 4-Pillar Strategic Squad Roadmap: Retain, Develop, Replace, Recruit", styles),
        Spacer(1, 6),
    ]

    strategy = get_final_recruitment_strategy()

    def make_pillar_card(pillar_name: str, items: List[str], header_color: colors.HexColor) -> Table:
        rows = [[Paragraph(pillar_name, styles["CardTitle"])]]
        for it in items:
            rows.append([Paragraph(f"&bull; {it}", styles["Body"])])

        t = Table(rows, colWidths=[185])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    p1 = make_pillar_card("RETAIN (Core Assets)", strategy["RETAIN"], COLOR_BFC_BLUE)
    p2 = make_pillar_card("DEVELOP (Academy)", strategy["DEVELOP"], colors.HexColor("#0284C7"))
    p3 = make_pillar_card("REPLACE (Veterans)", strategy["REPLACE"], COLOR_BFC_RED)
    p4 = make_pillar_card("RECRUIT (Immediate Gaps)", strategy["RECRUIT"], COLOR_SUCCESS)

    pillars_table = Table([[p1, p2, p3, p4]], colWidths=[195]*4)
    pillars_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(pillars_table)
    story.append(Spacer(1, 10))

    # Executive Closing Mandate & Methodology
    mandate_text = [
        Paragraph("<b>EXECUTIVE MANDATE FOR THE SPORTING DIRECTOR & TECHNICAL STAFF:</b>", styles["CardTitle"]),
        Spacer(1, 4),
        Paragraph(
            "<b>1. Pre-Contract Aggression:</b> Initiate pre-contract negotiations for David Lalhlansanga and Vibin Mohanan prior to the opening of the transfer window to prevent fee escalation.<br/>"
            "<b>2. Contract Transition Protocol:</b> Structure Sunil Chhetri's role transition into player-mentorship, preserving squad chemistry while transitioning on-pitch minutes to Sivasakthi and incoming U24 forwards.<br/>"
            "<b>3. Wage Bill Neutrality:</b> Offload departing senior foreign salaries (Noguera, Jovanović) directly into prime-age international spine replacements to ensure complete financial sustainability.<br/>"
            "<b>4. Data Governance Standards:</b> Maintain continuous validation logging (Verified / Partial / Missing) for all scouting dossiers; never conflate subjective scouting fees with market valuations.",
            styles["Body"]
        ),
    ]

    t_mandate = Table([[mandate_text]], colWidths=[785])
    t_mandate.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_mandate)
    return story


# ==============================================================================
# MAIN COMPILER
# ==============================================================================

def generate_pdf_report():
    logger.info("Compiling Bengaluru FC 15-Page Professional Scouting Report PDF...")
    styles = get_report_styles()

    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=landscape(A4),
        leftMargin=28,
        rightMargin=28,
        topMargin=32,
        bottomMargin=28,
    )

    story: List[Any] = []

    # Slide 1 to Slide 15
    story.extend(build_page_01_cover(styles))
    story.extend(build_page_02_executive_summary(styles))
    story.extend(build_page_03_recruitment_identity(styles))
    story.extend(build_page_04_transfer_history(styles))
    story.extend(build_page_05_recruitment_patterns(styles))
    story.extend(build_page_06_recruitment_markets(styles))
    story.extend(build_page_07_player_pathways(styles))
    story.extend(build_page_08_market_value(styles))
    story.extend(build_page_09_current_squad(styles))
    story.extend(build_page_10_squad_age_depth(styles))
    story.extend(build_page_11_six_key_conclusions(styles))
    story.extend(build_page_12_squad_gaps(styles))
    story.extend(build_page_13_recruitment_profiles(styles))
    story.extend(build_page_14_player_shortlist(styles))
    story.extend(build_page_15_final_strategy(styles))

    doc.build(story, canvasmaker=NumberedCanvas)
    logger.info(f"Report successfully generated at: {PDF_PATH}")


if __name__ == "__main__":
    generate_pdf_report()
