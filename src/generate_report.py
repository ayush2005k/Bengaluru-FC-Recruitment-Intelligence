"""
src/generate_report.py
Generates an elite, publication-grade, 15-page executive football scouting dossier for Bengaluru FC
using ReportLab with a clean, editorial white-and-blue visual language, directly modeled on
professional European and J-League scouting dossiers (Cerezo Osaka reference benchmark).

Design Specifications:
- Landscape A4 (841.89 x 595.27 pt)
- Target Club: Bengaluru FC
- Visual System: Off-white canvas (#F8F9FA), pure white cards (#FFFFFF), deep navy header/text (#0B132B / #0F172A),
  Bengaluru FC Royal Blue (#003399), BFC Crimson Red accent (#D32F2F), subtle grey borders (#E2E8F0).
- Typography: Large, readable titles (22-26pt), section heads (14-16pt), subheads (10-12pt), body (9.5-10.5pt).
- Real Player Photography integrated across Pathways (p.7), Value Appreciation (p.8), Senior Assets (p.9), and Shortlist (p.14).
- Exactly 15 Pages, each designed as a high-density, balanced editorial slide with 75-90% page utilization.
"""

import os
import sys
import logging
from typing import List, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.pdfgen import canvas

# Ensure local module access
sys.path.insert(0, os.path.dirname(__file__))

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

# Color Palette (Cerezo Osaka Benchmark: White + Bengaluru FC Royal Blue & Crimson Red)
COLOR_BG = colors.HexColor("#F8F9FA")          # Clean Off-White Page Canvas
COLOR_CARD_BG = colors.HexColor("#FFFFFF")     # Pure White Content Cards
COLOR_CARD_ALT = colors.HexColor("#F1F5F9")    # Light Blue-Grey Accent Card
COLOR_CARD_DARK = colors.HexColor("#0B132B")   # Deep Navy Card (for contrast sections)
COLOR_BFC_BLUE = colors.HexColor("#003399")    # Bengaluru FC Royal Blue
COLOR_BFC_NAVY = colors.HexColor("#0B132B")    # Deep Navy Header
COLOR_BFC_RED = colors.HexColor("#D32F2F")     # Bengaluru FC Crimson Red Accent
COLOR_ACCENT_SKY = colors.HexColor("#0284C7")  # Clear Sky Blue for labels & links
COLOR_TEXT_MAIN = colors.HexColor("#0F172A")   # Dark Navy High-Contrast Body Text
COLOR_TEXT_MUTED = colors.HexColor("#64748B")  # Slate Muted Grey for captions
COLOR_TEXT_LIGHT = colors.HexColor("#FFFFFF")  # Pure White Text (for dark headers/cards)
COLOR_BORDER = colors.HexColor("#E2E8F0")      # Subtle Light Card Border
COLOR_BORDER_NAVY = colors.HexColor("#CBD5E1") # Distinct Border
COLOR_SUCCESS = colors.HexColor("#10B981")     # Green
COLOR_WARNING = colors.HexColor("#F59E0B")     # Amber

# Image Asset Locations
CREST_PATH = os.path.join(ASSETS_DIR, "logo", "bfc_crest_highres.png")
if not os.path.exists(CREST_PATH):
    CREST_PATH = os.path.join(ASSETS_DIR, "logo", "bfc_crest.png")

CARDS_DIR = os.path.join(ASSETS_DIR, "images", "cards")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")

def get_player_photo(filename: str) -> str:
    """Returns path to player image, preferring pre-cropped cards directory."""
    p_card = os.path.join(CARDS_DIR, filename)
    if os.path.exists(p_card):
        return p_card
    p_raw = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(p_raw):
        return p_raw
    return ""


# ==============================================================================
# CANVAS & RUNNING CHROME (Header Accent & Running Footer)
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas that records page states and renders running header accents and
    publication footers with dynamic 'Page X of 15' page numbering.
    """

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

        # Skip header/footer chrome on Cover Page (Page 1)
        if self._pageNumber > 1:
            # Top Accent Strip (BFC Blue 75% | BFC Crimson 25%)
            self.setFillColor(COLOR_BFC_BLUE)
            self.rect(26, PAGE_HEIGHT - 6, (PAGE_WIDTH - 52) * 0.75, 3, fill=True, stroke=False)
            self.setFillColor(COLOR_BFC_RED)
            self.rect(26 + (PAGE_WIDTH - 52) * 0.75, PAGE_HEIGHT - 6, (PAGE_WIDTH - 52) * 0.25, 3, fill=True, stroke=False)

            # Footer Divider Line
            self.setStrokeColor(COLOR_BORDER_NAVY)
            self.setLineWidth(0.6)
            self.line(26, 18, PAGE_WIDTH - 26, 18)

            # Footer Left Metadata
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(COLOR_TEXT_MUTED)
            self.drawString(26, 9, "BENGALURU FC RECRUITMENT INTELLIGENCE  |  CONFIDENTIAL SCOUTING DOSSIER (2020/21 – 2024/25)")

            # Footer Right Page Number
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_BFC_BLUE)
            page_str = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(PAGE_WIDTH - 26, 9, page_str)

        self.restoreState()


def draw_page_background(c: canvas.Canvas, doc):
    """Draws the clean off-white background behind all page flowables."""
    c.saveState()
    c.setFillColor(COLOR_BG)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
    c.restoreState()


# ==============================================================================
# TYPOGRAPHY & STYLES
# ==============================================================================

def get_report_styles():
    """Defines typographic styles with tight, proportional leadings."""
    base = getSampleStyleSheet()

    styles = {
        "Normal": base["Normal"],
        "PageTitle": ParagraphStyle(
            "PageTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=24,
            textColor=COLOR_BFC_NAVY,
        ),
        "PageSubtitle": ParagraphStyle(
            "PageSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_TEXT_MUTED,
        ),
        "CardTitle": ParagraphStyle(
            "CardTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13.5,
            textColor=COLOR_BFC_NAVY,
        ),
        "CardTitleRed": ParagraphStyle(
            "CardTitleRed",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13.5,
            textColor=COLOR_BFC_RED,
        ),
        "CardTitleWhite": ParagraphStyle(
            "CardTitleWhite",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "CardSubtitle": ParagraphStyle(
            "CardSubtitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.8,
            textColor=COLOR_ACCENT_SKY,
        ),
        "CardBody": ParagraphStyle(
            "CardBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=COLOR_TEXT_MAIN,
        ),
        "CardBodyWhite": ParagraphStyle(
            "CardBodyWhite",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "CardBullet": ParagraphStyle(
            "CardBullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_TEXT_MAIN,
        ),
        "CardBulletWhite": ParagraphStyle(
            "CardBulletWhite",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "KpiValue": ParagraphStyle(
            "KpiValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=22,
            textColor=COLOR_BFC_BLUE,
            alignment=1,
        ),
        "KpiLabel": ParagraphStyle(
            "KpiLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_BFC_NAVY,
            alignment=1,
        ),
        "KpiSub": ParagraphStyle(
            "KpiSub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.5,
            textColor=COLOR_TEXT_MUTED,
            alignment=1,
        ),
        "PlayerName": ParagraphStyle(
            "PlayerName",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=COLOR_BFC_NAVY,
        ),
        "PlayerMeta": ParagraphStyle(
            "PlayerMeta",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_ACCENT_SKY,
        ),
        "PlayerText": ParagraphStyle(
            "PlayerText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.2,
            textColor=COLOR_TEXT_MAIN,
        ),
        "BadgeText": ParagraphStyle(
            "BadgeText",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=COLOR_BFC_RED,
            alignment=2,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=9.8,
            textColor=COLOR_TEXT_MAIN,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.8,
            textColor=COLOR_BFC_NAVY,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "BannerText": ParagraphStyle(
            "BannerText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=11.2,
            textColor=COLOR_TEXT_MAIN,
        ),
    }
    return styles


# ==============================================================================
# UI COMPONENTS & LAYOUT HELPERS
# ==============================================================================

def make_club_header(section_no: str, section_title: str, subtitle: str = "") -> Table:
    """
    Renders the consistent top club header bar on Pages 2–15, inspired by Cerezo Osaka:
    Deep Navy background, BFC high-res crest, section number, title, and red accent bar.
    """
    crest_img = Image(CREST_PATH, width=20, height=27) if os.path.exists(CREST_PATH) else Paragraph("<b>BFC</b>", ParagraphStyle("H", textColor=colors.white))

    left_content = [
        Paragraph(f'<font size=6.5 color="#38BDF8"><b>BENGALURU FC &nbsp;|&nbsp; SCOUTING REPORT</b></font>', ParagraphStyle("LH1", leading=8)),
        Paragraph(f'<font size=11 color="#FFFFFF"><b>{section_no}. {section_title.upper()}</b></font>', ParagraphStyle("LH2", leading=13)),
    ]

    right_content = [
        Paragraph(f'<font size=6.5 color="#94A3B8">HISTORICAL BASELINE: 106 EVENTS &nbsp;•&nbsp; 24 SQUAD</font>', ParagraphStyle("RH1", alignment=2, leading=8)),
        Paragraph(f'<font size=8 color="#38BDF8"><b>CONFIDENTIAL DOSSIER</b></font>', ParagraphStyle("RH2", alignment=2, leading=11)),
    ]

    header_table = Table(
        [[crest_img, left_content, right_content]],
        colWidths=[28, 482, 280],
        rowHeights=[32],
    )
    header_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_BFC_NAVY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (0, 0), 6),
            ("RIGHTPADDING", (-1, -1), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 2.2, COLOR_BFC_RED),
        ])
    )
    return header_table


def make_card_container(flowables: List[Any], width: float, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding: int = 6) -> Table:
    """Wraps flowables into a clean, bordered white content card."""
    t = Table([[flowables]], colWidths=[width])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("BOX", (0, 0), (-1, -1), 0.8, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
            ("LEFTPADDING", (0, 0), (-1, -1), padding),
            ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ])
    )
    return t


def make_kpi_card(value: str, label: str, sub: str, width: float, value_color=COLOR_BFC_BLUE) -> Table:
    """Generates an executive KPI metric card with clean typography."""
    t = Table(
        [
            [Paragraph(f'<font color="{value_color.hexval()}"><b>{value}</b></font>', ParagraphStyle("KV", fontName="Helvetica-Bold", fontSize=18, leading=20, alignment=1))],
            [Paragraph(label, ParagraphStyle("KL", fontName="Helvetica-Bold", fontSize=7.2, leading=9, textColor=COLOR_BFC_NAVY, alignment=1))],
            [Paragraph(sub, ParagraphStyle("KS", fontName="Helvetica", fontSize=6.5, leading=8, textColor=COLOR_TEXT_MUTED, alignment=1))],
        ],
        colWidths=[width],
    )
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )
    return t


def make_player_scout_card(
    name: str,
    position: str,
    age: str,
    nationality: str,
    club_status: str,
    market_val: str,
    badge: str,
    profile: str,
    why_matters: str,
    photo_filename: str = None,
    fit_score: str = None,
    watchout: str = None,
    width: float = 388,
    is_shortlist: bool = False,
) -> Table:
    """
    Renders an editorial photo-based player scouting card inspired by the Cerezo Osaka dossier:
    PHOTO | NAME & BADGE | META (Pos/Age/Val) | QUALITATIVE PROFILE | WHY HE MATTERS.
    """
    photo_path = get_player_photo(photo_filename) if photo_filename else ""
    has_photo = bool(photo_path and os.path.exists(photo_path))

    photo_w = 46 if not is_shortlist else 58
    photo_h = 56 if not is_shortlist else 70

    if has_photo:
        photo_flowable = Image(photo_path, width=photo_w, height=photo_h)
    else:
        initials = "".join([part[0] for part in name.split()[:2]]) if name else "BFC"
        photo_flowable = Table(
            [[Paragraph(f'<font size=14 color="#003399"><b>{initials}</b></font>', ParagraphStyle("IN", alignment=1))]],
            colWidths=[photo_w],
            rowHeights=[photo_h],
        )
        photo_flowable.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

    right_w = width - photo_w - 14

    top_badge = f'<font color="{COLOR_BFC_RED.hexval()}"><b>{badge}</b></font>' if badge else ""
    if fit_score:
        top_badge = f'<font color="{COLOR_SUCCESS.hexval()}"><b>FIT SCORE: {fit_score}</b></font>'

    header_para = Paragraph(
        f'<table width="100%"><tr><td><font size=9.2 color="#0B132B"><b>{name}</b></font></td><td align="right"><font size=6.8>{top_badge}</font></td></tr></table>',
        ParagraphStyle("PH", leading=10.5),
    )
    meta_para = Paragraph(
        f'<font size=6.8 color="#0284C7"><b>{position}</b></font> &nbsp;•&nbsp; <font size=6.5 color="#64748B">{age} &nbsp;|&nbsp; {nationality} &nbsp;|&nbsp; {club_status} &nbsp;|&nbsp; <b>{market_val}</b></font>',
        ParagraphStyle("PM", leading=8.5),
    )
    profile_para = Paragraph(
        f'<font size=6.8 color="#0F172A"><b>Profile:</b> {profile}</font>',
        ParagraphStyle("PP", leading=8.6),
    )
    why_para = Paragraph(
        f'<font size=6.8 color="#003399"><b>Why He Fits BFC:</b> {why_matters}</font>',
        ParagraphStyle("PW", leading=8.6),
    )

    card_content = [header_para, Spacer(1, 1), meta_para, Spacer(1, 1.5), profile_para, Spacer(1, 1.5), why_para]
    if watchout:
        watchout_para = Paragraph(
            f'<font size=6.8 color="#D32F2F"><b>Watchout:</b> {watchout}</font>',
            ParagraphStyle("PWO", leading=8.5),
        )
        card_content.extend([Spacer(1, 1.5), watchout_para])

    outer_table = Table(
        [[photo_flowable, card_content]],
        colWidths=[photo_w + 4, right_w],
    )
    outer_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LINEAFTER", (0, 0), (0, -1), 0.5, COLOR_BORDER),
        ])
    )
    return outer_table


# ==============================================================================
# SLIDE BUILDERS (PAGE 1 TO 15)
# ==============================================================================

# ------------------------------------------------------------------------------
# PAGE 1: COVER
# ------------------------------------------------------------------------------
def build_page_01_cover(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(Spacer(1, 36))

    if os.path.exists(CREST_PATH):
        story.append(Image(CREST_PATH, width=95, height=128))
    story.append(Spacer(1, 14))

    story.append(Paragraph("BENGALURU FC", ParagraphStyle("CT1", fontName="Helvetica-Bold", fontSize=32, leading=36, textColor=COLOR_BFC_NAVY, alignment=1)))
    story.append(Spacer(1, 3))
    story.append(Paragraph("SCOUTING REPORT & RECRUITMENT INTELLIGENCE", ParagraphStyle("CT2", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=COLOR_BFC_BLUE, alignment=1)))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Empirical Squad Planning, Pathway Analytics & Transfer Market Intelligence (2020/21 – 2024/25)", ParagraphStyle("CT3", fontName="Helvetica", fontSize=10.5, leading=14, textColor=COLOR_TEXT_MUTED, alignment=1)))
    story.append(Spacer(1, 20))

    # Nav pill bar
    nav_table = Table(
        [[
            Paragraph("<b>1. Historical Transfers</b>", ParagraphStyle("N1", fontSize=8, leading=10, textColor=COLOR_BFC_BLUE, alignment=1)),
            Paragraph("<b>2. Squad Dynamics</b>", ParagraphStyle("N2", fontSize=8, leading=10, textColor=COLOR_BFC_NAVY, alignment=1)),
            Paragraph("<b>3. Career Pathways</b>", ParagraphStyle("N3", fontSize=8, leading=10, textColor=COLOR_BFC_BLUE, alignment=1)),
            Paragraph("<b>4. Value Appreciation</b>", ParagraphStyle("N4", fontSize=8, leading=10, textColor=COLOR_BFC_NAVY, alignment=1)),
            Paragraph("<b>5. Strategic Roadmap</b>", ParagraphStyle("N5", fontSize=8, leading=10, textColor=COLOR_BFC_BLUE, alignment=1)),
        ]],
        colWidths=[158, 158, 158, 158, 158],
        rowHeights=[24],
    )
    nav_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ])
    )
    story.append(nav_table)
    story.append(Spacer(1, 22))

    # Metadata card
    meta_table = Table(
        [
            [
                Paragraph("<b>Prepared by:</b> Ayush Singh", styles["TableCell"]),
                Paragraph("<b>Focus Club:</b> Bengaluru FC (Indian Super League)", styles["TableCell"]),
            ],
            [
                Paragraph("<b>Analytical Scope:</b> 5 Seasons (2020/21 – 2024/25)", styles["TableCell"]),
                Paragraph("<b>Dataset Baseline:</b> 106 Transfer Events (101 Ext + 5 Academy)", styles["TableCell"]),
            ],
            [
                Paragraph("<b>Methodological Framework:</b> Gap-Driven Recruitment Engine", styles["TableCell"]),
                Paragraph("<b>Data Governance:</b> 100% Verified Non-Synthetic Historicals", styles["TableCell"]),
            ],
        ],
        colWidths=[395, 395],
        rowHeights=[20, 20, 20],
    )
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 22))

    story.append(Paragraph("CONFIDENTIAL SCOUTING DOSSIER | FOR SPORTING DIRECTORS & TECHNICAL LEADERSHIP", ParagraphStyle("CONF", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=COLOR_TEXT_MUTED, alignment=1)))
    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 2: EXECUTIVE SUMMARY
# ------------------------------------------------------------------------------
def build_page_02_executive_summary(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("01", "Executive Summary", "Strategic Overview"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Executive Summary & Core Strategic Dynamics", styles["PageTitle"]))
    story.append(Paragraph("Analytical Scope, Dashboard Overview & Methodological Pipeline across 5 ISL Seasons", styles["PageSubtitle"]))
    story.append(Spacer(1, 9))

    # Top 6 KPI Cards
    kpis = [
        make_kpi_card("106", "TRANSFER EVENTS", "101 Ext + 5 Academy", 128),
        make_kpi_card("54", "EXTERNAL SIGNINGS", "50 Free + 4 Loans", 128),
        make_kpi_card("27.0y", "AVG SIGNING AGE", "Bimodal (24-26 & 30+)", 128),
        make_kpi_card("92.6%", "FREE EXTERNAL %", "50/54 External Free", 128),
        make_kpi_card("57.4%", "DOMESTIC SHARE", "31 Domestic Signings", 128),
        make_kpi_card("5", "ACADEMY PROM.", "Zero-Fee Internal Spine", 128),
    ]
    kpi_table = Table([[kpis[0], kpis[1], kpis[2], kpis[3], kpis[4], kpis[5]]], colWidths=[131.6]*6)
    kpi_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(kpi_table)
    story.append(Spacer(1, 9))

    # Middle 2-Column Comparative Section
    left_content = [
        Paragraph("WHAT THE RECRUITMENT HISTORY SAYS", styles["CardTitle"]),
        Spacer(1, 3),
        Paragraph("Bengaluru FC operates an opportunistic, contract-efficient recruitment model across five seasons:", styles["CardBody"]),
        Spacer(1, 4),
        Paragraph("• <b>Zero Fee Exposure:</b> 92.6% of external arrivals secured on free transfers, insulating club balance sheets from transfer fee depreciation.", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Bimodal Age Demographics:</b> Recruitment targets domestic prime talent (24–26y, 42.6%) and foreign leaders (30+y, 31.5%), bypassing inflated 27–29 fees.", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Central Spine Priority:</b> Signings concentrate heavily on central defense (20 signings, 37.0%) and attacking match-winners (15 signings, 27.8%).", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Domestic Continuity:</b> High-tenure Indian starters (Suresh, Roshan, Chhetri, Gurpreet) anchor the team across multiple coaching changes.", styles["CardBullet"]),
    ]
    left_card = make_card_container(left_content, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

    right_content = [
        Paragraph("KEY SQUAD DYNAMICS", styles["CardSubtitle"]),
        Spacer(1, 1),
        Paragraph("WHAT THE CURRENT SQUAD SAYS", styles["CardTitleWhite"]),
        Spacer(1, 3),
        Paragraph("Recruitment should execute structured succession without suppressing young assets:", styles["CardBodyWhite"]),
        Spacer(1, 4),
        Paragraph("• <b>Acute Offensive Age Cliff:</b> Starting creators and forwards average 35.8 years (Chhetri 40, Noguera 35, Díaz 34, Méndez 34), requiring urgent succession.", styles["CardBulletWhite"]),
        Spacer(1, 2),
        Paragraph("• <b>Right-Back Structural Void:</b> Roster contains only 1 natural specialist RB (Shivaldo Singh 20), forcing unnatural CB deployments (Rahul Bheke).", styles["CardBulletWhite"]),
        Spacer(1, 2),
        Paragraph("• <b>Academy Pathway Protection:</b> High-upside domestic assets (Suresh +500%, Roshan +900%, Sivasakthi +700%, Vinith 19) must retain guaranteed match minutes.", styles["CardBulletWhite"]),
        Spacer(1, 2),
        Paragraph("• <b>Strategic Mandate:</b> Acquire prime-age domestic difference-makers (20–24y) while transitioning foreign slots to athletic physical profiles.", styles["CardBulletWhite"]),
    ]
    right_card = make_card_container(right_content, 390, bg_color=COLOR_BFC_NAVY, border_color=COLOR_BFC_BLUE)

    comp_table = Table([[left_card, right_card]], colWidths=[395, 395])
    comp_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(comp_table)
    story.append(Spacer(1, 9))

    # Bottom 3 Strategic Findings
    f1 = [
        Paragraph("01. FINDING: Opportunistic Contract Capture", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("<b>Evidence:</b> 50 of 54 external signings free (92.6%); €0 net transfer deficit.", styles["CardBullet"]),
        Paragraph("<b>Scouting Implication:</b> High wage flexibility under ISL salary cap, but demands elite medical and motivational vetting.", styles["CardBullet"]),
    ]
    f2 = [
        Paragraph("02. FINDING: Attacking Succession Cliff", styles["CardTitleRed"]),
        Spacer(1, 2),
        Paragraph("<b>Evidence:</b> Starting attacking spine averages 35.8 years, producing 65%+ goal output.", styles["CardBullet"]),
        Paragraph("<b>Scouting Implication:</b> Proactive multi-window acquisition of U24 striker and creative playmaker is mandatory.", styles["CardBullet"]),
    ]
    f3 = [
        Paragraph("03. FINDING: Domestic Value Multiplier", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("<b>Evidence:</b> 100% of market value appreciation concentrated in domestic U23 talent.", styles["CardBullet"]),
        Paragraph("<b>Scouting Implication:</b> Direct capital expenditures into elite domestic youth rather than paying fees for aging foreign stars.", styles["CardBullet"]),
    ]
    f_table = Table([[
        make_card_container(f1, 258, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(f2, 258, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(f3, 258, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
    ]], colWidths=[263.3, 263.3, 263.3])
    story.append(f_table)
    story.append(Spacer(1, 7))

    # Executive Takeaway Banner
    takeaway = [Paragraph(
        "<b>EXECUTIVE TAKEAWAY:</b> Bengaluru FC maintains an exceptionally disciplined, zero-fee acquisition architecture that eliminates balance-sheet risk. However, this reliance on experienced free agents has produced an acute demographic imbalance in the attacking spine. The sporting directorate must execute an immediate transition plan: securing a high-pressing domestic U24 striker (David Lalhlansanga) and creative playmaker (Vibin Mohanan) to sustain championship contention without compromising the developmental minutes of academy talents.",
        styles["BannerText"],
    )]
    story.append(make_card_container(takeaway, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BFC_BLUE, padding=6))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 3: CLUB RECRUITMENT IDENTITY
# ------------------------------------------------------------------------------
def build_page_03_recruitment_identity(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("02", "Club Recruitment Identity", "Empirical Evaluation"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Club Recruitment Identity & Operational Archetype", styles["PageTitle"]))
    story.append(Paragraph("Empirical Evaluation: What Kind of Recruiter is Bengaluru FC Across Five ISL Campaigns?", styles["PageSubtitle"]))
    story.append(Spacer(1, 10))

    # Top 5 Metric Cards
    m1 = make_kpi_card("Opportunistic", "RECRUITMENT MODEL", "Contract Expiry & Swaps", 154)
    m2 = make_kpi_card("Bimodal", "AGE ARCHITECTURE", "24–26 Prime & 30+ Leaders", 154)
    m3 = make_kpi_card("92.6% Free", "ACQUISITION DEAL", "50/54 External Free Agents", 154)
    m4 = make_kpi_card("57.4%", "MARKET BALANCE", "31 Domestic Signings (ISL/I-L)", 154)
    m5 = make_kpi_card("Defenders (20)", "POSITIONAL FOCUS", "37.0% of Inbound Transfers", 154)
    top_m = Table([[m1, m2, m3, m4, m5]], colWidths=[158]*5)
    story.append(top_m)
    story.append(Spacer(1, 12))

    # 2-Column Core Analysis
    left_flow = [
        Paragraph("WHAT THE EMPIRICAL DATA SAYS", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("Rigorous quantification across 106 historical transfer events (2020/21 – 2024/25):", styles["CardBody"]),
        Spacer(1, 4),
        Paragraph("• <b>Zero Transfer Fee Outlay:</b> 50 of 54 external signings arrived on free transfers (92.6%), insulating the club from transfer fee depreciation.", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Age Barbell Distribution:</b> Mean signing age of 27.0y conceals heavy polarization—42.6% in 24–26 prime domestic bracket, 31.5% in 30+ foreign bracket, and only 5.6% in 27–29 window.", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Defensive Squad Spot Expenditure:</b> Defenders represent 20 of 54 signings (37.0%), reflecting persistent backline restructuring across 5 seasons.", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Targeted Foreign Quota Usage:</b> Overseas slots are strictly dedicated to central spine positions (CB, CM, CF) from Spain and Australia.", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Internal Youth Progression:</b> 5 internal BFC B promotions in 2023/24 reduced average inbound age to 23.6y for that single campaign.", styles["CardBullet"]),
    ]
    left_c = make_card_container(left_flow, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=9)

    right_flow = [
        Paragraph("SPORTING LEADERSHIP ANALYSIS", styles["CardSubtitle"]),
        Spacer(1, 1),
        Paragraph("SCOUTING INTERPRETATION & SPORTING LOGIC", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("Strategic evaluation of why Bengaluru FC operates this recruitment architecture:", styles["CardBody"]),
        Spacer(1, 4),
        Paragraph("• <b>Salary Cap Capital Efficiency:</b> By avoiding transfer fees, BFC reallocates capital into competitive wages for proven ISL starters (Díaz, Noguera, Bheke).", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Eliminating Adaptation Risk:</b> Recruiting proven performers from ISL rivals (Mumbai City, Hyderabad) guarantees immediate tactical readiness.", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Spanish Tactical Continuity:</b> A persistent Spanish recruitment pipeline (Roca, Cuadrat, Zaragoza) provides stylistic stability across managerial changes.", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>The Free-Agent Vulnerability:</b> Heavy reliance on free agency leaves the club vulnerable to bidding wars from corporate-backed rivals (Mohun Bagan SG, Mumbai City).", styles["CardBullet"]),
        Spacer(1, 3),
        Paragraph("• <b>Strategic Modernization Required:</b> BFC must transition from opportunistic contract capturing to proactive target identification before player contracts expire.", styles["CardBullet"]),
    ]
    right_c = make_card_container(right_flow, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=9)

    grid_t = Table([[left_c, right_c]], colWidths=[395, 395])
    story.append(grid_t)
    story.append(Spacer(1, 12))

    # Bottom Directive
    directive = [Paragraph(
        "<b>RECRUITMENT DIRECTIVE:</b> Bengaluru FC's identity as a contract-efficient, pragmatic recruiter provides a strong financial baseline. However, to compete with top-tier ISL spenders, the club must establish a proactive pre-contract scouting mechanism—identifying and securing prime domestic talents (ages 21–24) 6 to 12 months prior to contract expiration, rather than participating in reactive summer bidding contests.",
        styles["BannerText"],
    )]
    story.append(make_card_container(directive, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BFC_BLUE, padding=7))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 4: HISTORICAL TRANSFER TRENDS & VOLUME
# ------------------------------------------------------------------------------
def build_page_04_transfer_history(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("03", "Historical Transfer Trends & Volume", "Volume Dynamics"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Historical Transfer Trends & Volume Across Five Campaigns", styles["PageTitle"]))
    story.append(Paragraph("Longitudinal Tracking: 106 Transfer Events Across Five ISL Campaigns (2020/21 – 2024/25)", styles["PageSubtitle"]))
    story.append(Spacer(1, 9))

    # Top Section: Chart on Left, Table on Right
    chart_p = os.path.join(CHARTS_DIR, "transfers_by_season.png")
    chart_flow = Image(chart_p, width=355, height=172) if os.path.exists(chart_p) else Paragraph("Chart Unavailable", styles["CardBody"])
    chart_card = make_card_container([chart_flow], 365, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=4)

    # 5-Season Table
    t_data = [
        [Paragraph("<b>Season</b>", styles["TableHead"]), Paragraph("<b>Arr</b>", styles["TableHead"]), Paragraph("<b>Dep</b>", styles["TableHead"]), Paragraph("<b>Net</b>", styles["TableHead"]), Paragraph("<b>Avg Age</b>", styles["TableHead"]), Paragraph("<b>Key Strategic Shift / Roster Realignment</b>", styles["TableHead"])],
        [Paragraph("2020/21", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("14", styles["TableCell"]), Paragraph("-2", styles["TableCell"]), Paragraph("27.4y", styles["TableCell"]), Paragraph("Transition post-Roca era; extensive defensive rebuilding (Cleiton Silva, Pratik)", styles["TableCell"])],
        [Paragraph("2021/22", styles["TableCellBold"]), Paragraph("10", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("0", styles["TableCell"]), Paragraph("26.2y", styles["TableCell"]), Paragraph("Injection of youth; breakthrough emergence of Naorem Roshan & Sivasakthi", styles["TableCell"])],
        [Paragraph("2022/23", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("+2", styles["TableCell"]), Paragraph("28.1y", styles["TableCell"]), Paragraph("Title push with proven ISL winners (Roy Krishna, Javi Hernández, Sandesh)", styles["TableCell"])],
        [Paragraph("2023/24", styles["TableCellBold"]), Paragraph("18", styles["TableCell"]), Paragraph("0", styles["TableCell"]), Paragraph("+18", styles["TableCell"]), Paragraph("23.6y", styles["TableCell"]), Paragraph("Youth wave; 5 BFC B promotions (Robin Yadav, Shivaldo, Patre) + Veendorp", styles["TableCell"])],
        [Paragraph("2024/25", styles["TableCellBold"]), Paragraph("7", styles["TableCell"]), Paragraph("13", styles["TableCell"]), Paragraph("-6", styles["TableCell"]), Paragraph("28.8y", styles["TableCell"]), Paragraph("Zaragoza Spanish spine: Noguera, Díaz, Méndez, Bheke; veteran restructuring", styles["TableCell"])],
        [Paragraph("<b>Total</b>", styles["TableCellBold"]), Paragraph("<b>59</b>", styles["TableCellBold"]), Paragraph("<b>47</b>", styles["TableCellBold"]), Paragraph("<b>+12</b>", styles["TableCellBold"]), Paragraph("<b>27.0y</b>", styles["TableCellBold"]), Paragraph("<b>106 Cumulative Events (101 External + 5 Academy Promotions)</b>", styles["TableCellBold"])],
    ]
    season_t = Table(t_data, colWidths=[55, 30, 30, 30, 48, 217], rowHeights=[18, 24, 24, 24, 24, 24, 22])
    season_t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BFC_NAVY),
            ("BACKGROUND", (0, 1), (-1, -2), COLOR_CARD_BG),
            ("BACKGROUND", (0, -1), (-1, -1), COLOR_CARD_ALT),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    top_grid = Table([[chart_card, season_t]], colWidths=[375, 415])
    top_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(top_grid)
    story.append(Spacer(1, 9))

    # 4 Historical Phases Cards
    p1 = [
        Paragraph("Stage 1: Post-Roca Reset", styles["CardTitle"]),
        Paragraph('<font size=7 color="#D32F2F"><b>2020/21 (26 Events)</b></font>', styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Restructured backline; Cleiton Silva arrived as attacking focal point; high roster turnover.", styles["CardBullet"]),
    ]
    p2 = [
        Paragraph("Stage 2: Youth Influx", styles["CardTitle"]),
        Paragraph('<font size=7 color="#0284C7"><b>2021/22 (20 Events)</b></font>', styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Roshan Singh & Sivasakthi integrated; average age dropped to 26.2y; domestic core solidified.", styles["CardBullet"]),
    ]
    p3 = [
        Paragraph("Stage 3: Veteran Push", styles["CardTitle"]),
        Paragraph('<font size=7 color="#F59E0B"><b>2022/23 (22 Events)</b></font>', styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Title push with proven ISL winners (Krishna, Javi); Durand Cup win; reached ISL Final.", styles["CardBullet"]),
    ]
    p4 = [
        Paragraph("Stage 4: Zaragoza Rebuild", styles["CardTitle"]),
        Paragraph('<font size=7 color="#10B981"><b>2023/24–2024/25 (38 Events)</b></font>', styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Youth promotion wave (5 BFC B promotions) followed by Spanish veteran spine (Noguera, Díaz, Méndez).", styles["CardBullet"]),
    ]
    phases_t = Table([[
        make_card_container(p1, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(p2, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(p3, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(p4, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
    ]], colWidths=[197.5]*4)
    story.append(phases_t)
    story.append(Spacer(1, 8))

    # Observation Banner
    obs = [Paragraph(
        "<b>STRATEGIC OBSERVATION:</b> Transfer activity averages 21.2 transactions per completed campaign, reflecting high roster turnover. Peak turnover occurred in 2020/21 (26) and 2022/23 (22), corresponding to major tactical transitions. The club has managed zero net negative transfer fee deficits by strictly utilizing free transfers and player contract expirations.",
        styles["BannerText"],
    )]
    story.append(make_card_container(obs, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=6))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 5: RECRUITMENT PATTERNS & POSITIONAL ALLOCATION
# ------------------------------------------------------------------------------
def build_page_05_recruitment_patterns(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("04", "Recruitment Patterns, Deal Structures & Allocation", "Structural Trends"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Recruitment Patterns, Deal Structures & Positional Allocation", styles["PageTitle"]))
    story.append(Paragraph("Age Demographics, Deal Typologies & Positional Allocation across 54 External Signings", styles["PageSubtitle"]))
    story.append(Spacer(1, 9))

    # 3 White Modules
    c1_img = os.path.join(CHARTS_DIR, "signing_age_distribution.png")
    c2_img = os.path.join(CHARTS_DIR, "transfer_types_donut.png")
    c3_img = os.path.join(CHARTS_DIR, "position_recruitment.png")

    m1_content = [
        Paragraph("1. WHO DOES BFC SIGN?", styles["CardTitle"]),
        Paragraph("Signing Age Demographics (Mean: 27.0y)", styles["CardSubtitle"]),
        Spacer(1, 4),
        Image(c1_img, width=242, height=128) if os.path.exists(c1_img) else Paragraph("Age Chart", styles["CardBody"]),
        Spacer(1, 5),
        Paragraph("• <b>Bimodal Polarization:</b> Signings concentrate in prime domestic talent (24–26y, 42.6%) and veteran leaders (30+y, 31.5%).", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>The 27–29 Hollow:</b> Only 3 signings (5.6%) in peak-value bracket, avoiding inflated transfer fee markets.", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Scouting Implication:</b> Lack of intermediate-age signings leaves younger players without middle-tier mentors.", styles["CardBullet"]),
    ]
    mod1 = make_card_container(m1_content, 255, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6)

    m2_content = [
        Paragraph("2. HOW DOES BFC ACQUIRE?", styles["CardTitle"]),
        Paragraph("Transfer Deal Types (92.6% Free Agents)", styles["CardSubtitle"]),
        Spacer(1, 4),
        Image(c2_img, width=242, height=128) if os.path.exists(c2_img) else Paragraph("Donut Chart", styles["CardBody"]),
        Spacer(1, 5),
        Paragraph("• <b>Free Transfer Dominance:</b> 50 of 54 external signings arrived on free transfers with €0 net fees.", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Loan Insurance:</b> 4 loan events (7.4%) strictly used for short-term injury cover without long-term liabilities.", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Scouting Implication:</b> Zero fee amortization maximizes salary cap room, but requires intense medical vetting.", styles["CardBullet"]),
    ]
    mod2 = make_card_container(m2_content, 255, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6)

    m3_table = Table([
        [Paragraph("<b>Position</b>", styles["TableHead"]), Paragraph("<b>Signings</b>", styles["TableHead"]), Paragraph("<b>Share</b>", styles["TableHead"])],
        [Paragraph("Defender", styles["TableCellBold"]), Paragraph("20", styles["TableCell"]), Paragraph("37.0%", styles["TableCell"])],
        [Paragraph("Forward", styles["TableCellBold"]), Paragraph("15", styles["TableCell"]), Paragraph("27.8%", styles["TableCell"])],
        [Paragraph("Midfielder", styles["TableCellBold"]), Paragraph("13", styles["TableCell"]), Paragraph("24.1%", styles["TableCell"])],
        [Paragraph("Goalkeeper", styles["TableCellBold"]), Paragraph("6", styles["TableCell"]), Paragraph("11.1%", styles["TableCell"])],
    ], colWidths=[90, 65, 80], rowHeights=[14, 14, 14, 14, 14])
    m3_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BFC_NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))

    m3_content = [
        Paragraph("3. POSITIONS PRIORITIZED", styles["CardTitle"]),
        Paragraph("Positional Focus (Defensive Central Spine)", styles["CardSubtitle"]),
        Spacer(1, 4),
        Image(c3_img, width=242, height=62) if os.path.exists(c3_img) else Paragraph("Position Chart", styles["CardBody"]),
        Spacer(1, 3),
        m3_table,
        Spacer(1, 4),
        Paragraph("• <b>Boundary:</b> 54 External Signings vs 5 Academy Promotions.", styles["CardBullet"]),
        Spacer(1, 1),
        Paragraph("• <b>Scouting Implication:</b> Heavy defensive recruitment (37.0%) underpins backline stability.", styles["CardBullet"]),
    ]
    mod3 = make_card_container(m3_content, 255, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6)

    grid_t = Table([[mod1, mod2, mod3]], colWidths=[263.3, 263.3, 263.3])
    story.append(grid_t)
    story.append(Spacer(1, 8))

    # Pattern Synthesis
    synthesis = [Paragraph(
        "<b>RECRUITMENT PATTERN SYNTHESIS:</b> Bengaluru FC's operational model combines opportunistic free-agent captures (92.6%) with an age barbell strategy (24–26y domestic prime vs 30+ foreign spine). Central defense constitutes the largest single investment of squad slots (37.0%), ensuring competitive stability. Meanwhile, internal promotions (5 BFC B promotions) provide zero-cost depth without cannibalizing wage cap space.",
        styles["BannerText"],
    )]
    story.append(make_card_container(synthesis, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=6))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 6: RECRUITMENT MARKETS & SCOUTING FOOTPRINT
# ------------------------------------------------------------------------------
def build_page_06_recruitment_markets(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("05", "Recruitment Markets & Scouting Footprint", "Origin Analysis"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Recruitment Geographies, Feeder Networks & Sourcing Channels", styles["PageTitle"]))
    story.append(Paragraph("Where Does Bengaluru FC Find Players? Origin Leagues, Feeder Networks & Geographic Concentration", styles["PageSubtitle"]))
    story.append(Spacer(1, 9))

    # Top Section: Chart on Left, Feeder Clubs Table on Right
    chart_p = os.path.join(CHARTS_DIR, "recruitment_markets_combined.png")
    chart_flow = Image(chart_p, width=355, height=172) if os.path.exists(chart_p) else Paragraph("Markets Chart", styles["CardBody"])
    chart_card = make_card_container([chart_flow], 365, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=4)

    feeder_data = [
        [Paragraph("<b>Feeder Club / Origin</b>", styles["TableHead"]), Paragraph("<b>Country</b>", styles["TableHead"]), Paragraph("<b>Category</b>", styles["TableHead"]), Paragraph("<b>Signings</b>", styles["TableHead"]), Paragraph("<b>Key Players Acquired</b>", styles["TableHead"])],
        [Paragraph("Mumbai City FC", styles["TableCellBold"]), Paragraph("India", styles["TableCell"]), Paragraph("ISL Rival", styles["TableCell"]), Paragraph("5", styles["TableCellBold"]), Paragraph("Jorge Pereyra Díaz, Alberto Noguera, Rahul Bheke, Sunil Chhetri", styles["TableCell"])],
        [Paragraph("Hyderabad FC", styles["TableCellBold"]), Paragraph("India", styles["TableCell"]), Paragraph("ISL Rival", styles["TableCell"]), Paragraph("3", styles["TableCellBold"]), Paragraph("Chinglensana Singh, Halicharan Narzary, Rohit Kumar", styles["TableCell"])],
        [Paragraph("Indian Arrows", styles["TableCellBold"]), Paragraph("India", styles["TableCell"]), Paragraph("I-League / AIFF", styles["TableCell"]), Paragraph("2", styles["TableCellBold"]), Paragraph("Suresh Singh Wangjam, Akashdeep Singh", styles["TableCell"])],
        [Paragraph("CD Eldense", styles["TableCellBold"]), Paragraph("Spain", styles["TableCell"]), Paragraph("LaLiga 2", styles["TableCell"]), Paragraph("1", styles["TableCellBold"]), Paragraph("Pedro Capó (Zaragoza Spanish connection)", styles["TableCell"])],
        [Paragraph("Perth Glory", styles["TableCellBold"]), Paragraph("Australia", styles["TableCell"]), Paragraph("A-League", styles["TableCell"]), Paragraph("2", styles["TableCellBold"]), Paragraph("Ryan Williams, Aleksandar Jovanovic (AFC Quota)", styles["TableCell"])],
        [Paragraph("Club Necaxa", styles["TableCellBold"]), Paragraph("Mexico / Spain", styles["TableCell"]), Paragraph("Liga MX", styles["TableCell"]), Paragraph("1", styles["TableCellBold"]), Paragraph("Édgar Méndez (High-impact attacking forward)", styles["TableCell"])],
    ]
    feeder_t = Table(feeder_data, colWidths=[100, 52, 65, 45, 153], rowHeights=[18, 25, 25, 25, 25, 25, 25])
    feeder_t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BFC_NAVY),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    top_grid = Table([[chart_card, feeder_t]], colWidths=[375, 415])
    story.append(top_grid)
    story.append(Spacer(1, 9))

    # Middle 2-Column Pipeline Cards
    p_dom = [
        Paragraph("DOMESTIC PIPELINE (57.4% - 31 SIGNINGS)", styles["CardTitle"]),
        Paragraph("Core strategy: Proven ISL starters and high-ceiling I-League youth:", styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("• <b>ISL Rival Distress:</b> Capitalizing on financial restructuring at Hyderabad FC and contract expirations at Mumbai City FC.", styles["CardBullet"]),
        Paragraph("• <b>I-League Talent Incubator:</b> Primary breeding ground for high-upside domestic talent (Indian Arrows, TRAU FC, Aizawl FC).", styles["CardBullet"]),
        Paragraph("• <b>Internal Reserve Pipeline:</b> BFC B provides cost-free rotational depth (13.2% of all inbound movements across 5 seasons).", styles["CardBullet"]),
    ]
    p_for = [
        Paragraph("FOREIGN PIPELINE (42.6% - 23 SIGNINGS)", styles["CardTitle"]),
        Paragraph("Core strategy: Central spine leadership aligned with tactical philosophy:", styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("• <b>Spain (18.0%):</b> Tactical alignment with head coaches (Cuadrat, Zaragoza); technical tempo controllers and playmakers.", styles["CardBullet"]),
        Paragraph("• <b>Australia (12.0%):</b> Essential AFC quota channel providing physical resilience, aerial strength, and high-intensity running.", styles["CardBullet"]),
        Paragraph("• <b>Limited-Sample Signal:</b> Denmark (Drost) and Netherlands (Veendorp) represent emerging pathways requiring live scouting validation.", styles["CardBullet"]),
    ]
    pipe_t = Table([[
        make_card_container(p_dom, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(p_for, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
    ]], colWidths=[395, 395])
    story.append(pipe_t)
    story.append(Spacer(1, 8))

    # Footprint Directive
    dir_banner = [Paragraph(
        "<b>SCOUTING FOOTPRINT DIRECTIVE:</b> Bengaluru FC should expand its AFC-quota scouting beyond the Australian A-League into Japan's J2 League and South Korea's K League 2 to identify dynamic, technical forwards with high pressing workrates, while cementing partnerships with North-East I-League academies.",
        styles["BannerText"],
    )]
    story.append(make_card_container(dir_banner, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=6))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 7: CAREER PATHWAYS & TRAJECTORIES
# ------------------------------------------------------------------------------
def build_page_07_player_pathways(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("06", "Player Career Pathways & Trajectories", "Longitudinal Case Studies"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Player Career Pathways & Development Trajectories", styles["PageTitle"]))
    story.append(Paragraph("Case Studies: Acquisition Origin → Bengaluru FC Role & Growth → Career Destination / Current Valuation", styles["PageSubtitle"]))
    story.append(Spacer(1, 9))

    # 6 Pathway Cards in 2x3 Grid (With Real Photos for Suresh, Roshan, Sivasakthi!)
    c1 = make_player_scout_card(
        "Suresh Singh Wangjam", "Central Midfielder", "Joined Age 18", "India", "Active Senior Core", "€50k → €300k",
        "DOMESTIC CORE",
        "Identified from AIFF Indian Arrows developmental setup; developed through first-team midfield into an indispensable starter and senior national team pillar (+500% valuation growth).",
        "Highest return on domestic scouting patience; represents the club's midfield anchor for a decade.",
        photo_filename="suresh_singh_wangjam.png", width=388,
    )
    c2 = make_player_scout_card(
        "Naorem Roshan Singh", "Left/Right Full-Back", "Promoted Age 21", "India", "Active Senior Core", "€25k → €250k",
        "ACADEMY ELITE",
        "Promoted from the academy reserve team. Transitioned from developmental winger to ISL Emerging Player of the Year as an ambidextrous full-back (+900% valuation growth).",
        "Starting national team full-back, proving the elite viability of the internal academy pathway.",
        photo_filename="naorem_roshan_singh.png", width=388,
    )
    c3 = make_player_scout_card(
        "Sivasakthi Narayanan", "Striker / Centre-Forward", "Promoted Age 20", "India", "Active Senior Core", "€25k → €200k",
        "HOMEGROWN STRIKER",
        "Prolific academy goalscorer promoted to senior team; scored vital goals in Durand Cup triumph and ISL playoffs (+700% valuation growth).",
        "Demonstrates domestic forward development is achievable when backed by continuous match exposure.",
        photo_filename="sivasakthi_narayanan.png", width=388,
    )
    c4 = make_player_scout_card(
        "Cleiton Silva", "Striker", "Joined Age 33", "Brazil", "Transferred to East Bengal", "€350k → €100k",
        "2-YEAR PEAK",
        "Acquired opportunistically on free agency from Thailand. Served as primary goalscoring focal point for two campaigns (37 apps, 16 goals) before transitioning to an ISL rival.",
        "High-return 2-year foreign cycle; delivered immediate competitive goals with zero residual fee.",
        photo_filename=None, width=388,
    )
    c5 = make_player_scout_card(
        "Javi Hernández", "Attacking Midfielder", "Joined Age 33", "Spain", "Transferred to Jamshedpur", "€300k → €150k",
        "CUP WINNER",
        "Acquired on free transfer; functioned as primary creative playmaker. Led club to Durand Cup title and an ISL Final before departing at age 35 to refresh foreign wage bill.",
        "Exemplary veteran impact model; delivered trophies while amortizing wage expenditure.",
        photo_filename=None, width=388,
    )
    c6 = make_player_scout_card(
        "Udanta Singh", "Right Winger", "Joined Age 18", "India", "Transferred to FC Goa", "€25k → €325k Peak",
        "FULL-CYCLE DEVELOPMENT",
        "Acquired from Tata Football Academy; logged 180+ appearances over 9 seasons, winning I-League, Federation Cup, and ISL titles before moving on free transfer.",
        "Full-cycle domestic asset realization; long-term dressing room pillar and title-winning winger.",
        photo_filename=None, width=388,
    )

    grid_table = Table([[c1, c2], [c3, c4], [c5, c6]], colWidths=[395, 395], rowHeights=[75, 75, 75])
    grid_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(grid_table)
    story.append(Spacer(1, 7))

    # Bottom Comparative Pathway Dynamics
    dyn_left = [
        Paragraph("EXTERNAL RECRUITMENT PATHWAY DYNAMICS (2-YEAR CYCLE)", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("Foreign veteran signings deliver immediate competitive performance over 24-month cycles before contract expiration and wage recycling (e.g. Cleiton Silva, Javi Hernández, Alan Costa). They carry zero residual transfer fee value upon exit, functioning as amortized competitive tools rather than economic investments.", styles["CardBullet"]),
    ]
    dyn_right = [
        Paragraph("INTERNAL ACADEMY PROMOTION PATHWAY DYNAMICS (5-YEAR MULTIPLIER)", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("Internal development (5 BFC B promotions in 2023/24; Suresh, Roshan, Sivasakthi) drives 100% of the club's asset appreciation. Young domestic talents appreciate exponentially in valuation and provide long-term dressing room continuity across managerial transitions.", styles["CardBullet"]),
    ]
    dyn_table = Table([[
        make_card_container(dyn_left, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6),
        make_card_container(dyn_right, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6),
    ]], colWidths=[395, 395])
    story.append(dyn_table)

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 8: MARKET VALUE DYNAMICS & ASSET APPRECIATION
# ------------------------------------------------------------------------------
def build_page_08_market_value(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("07", "Market Value Dynamics & Player Development", "Economic Trajectories"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Market Value Dynamics & Financial Asset Appreciation", styles["PageTitle"]))
    story.append(Paragraph("Longitudinal Valuation Curves: Comparing Domestic Asset Appreciation vs Foreign Veteran Depreciation", styles["PageSubtitle"]))
    story.append(Spacer(1, 7))

    # Data Integrity Principle Banner
    int_banner = [Paragraph(
        "<b>DATA INTEGRITY PRINCIPLE: MARKET VALUE ≠ TRANSFER FEE.</b> Transfer Fee is the actual cash price paid between clubs (Bengaluru FC paid €0 in net fees across 92.6% of external arrivals). Market Value represents an objective economic asset valuation based on player age, contract length, form, league tier, and international caps. Asset Appreciation Formula: ((Current Value - Initial Value) / Initial Value) × 100.",
        styles["BannerText"],
    )]
    story.append(make_card_container(int_banner, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=5))
    story.append(Spacer(1, 8))

    # Top Section: Chart on Left, Value Development Cards on Right
    chart_p = os.path.join(CHARTS_DIR, "market_value_growth.png")
    chart_flow = Image(chart_p, width=355, height=172) if os.path.exists(chart_p) else Paragraph("MV Chart", styles["CardBody"])
    chart_card = make_card_container([chart_flow], 365, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=4)

    # 7-Player Market Value Table
    mv_data = [
        [Paragraph("<b>Player Name</b>", styles["TableHead"]), Paragraph("<b>Joined</b>", styles["TableHead"]), Paragraph("<b>Peak</b>", styles["TableHead"]), Paragraph("<b>Current</b>", styles["TableHead"]), Paragraph("<b>Growth %</b>", styles["TableHead"]), Paragraph("<b>Economic Value Category</b>", styles["TableHead"])],
        [Paragraph("Naorem Roshan Singh", styles["TableCellBold"]), Paragraph("€25k", styles["TableCell"]), Paragraph("€275k", styles["TableCell"]), Paragraph("€250k", styles["TableCellBold"]), Paragraph("+900.0%", styles["TableCellBold"]), Paragraph("Elite Academy Asset Appreciation", styles["TableCell"])],
        [Paragraph("Udanta Singh", styles["TableCellBold"]), Paragraph("€25k", styles["TableCell"]), Paragraph("€325k", styles["TableCell"]), Paragraph("€225k", styles["TableCellBold"]), Paragraph("+800.0%", styles["TableCellBold"]), Paragraph("Full-Cycle Homegrown Development", styles["TableCell"])],
        [Paragraph("Sivasakthi Narayanan", styles["TableCellBold"]), Paragraph("€25k", styles["TableCell"]), Paragraph("€200k", styles["TableCell"]), Paragraph("€200k", styles["TableCellBold"]), Paragraph("+700.0%", styles["TableCellBold"]), Paragraph("Emerging Domestic Forward Asset", styles["TableCell"])],
        [Paragraph("Suresh Singh Wangjam", styles["TableCellBold"]), Paragraph("€50k", styles["TableCell"]), Paragraph("€300k", styles["TableCell"]), Paragraph("€300k", styles["TableCellBold"]), Paragraph("+500.0%", styles["TableCellBold"]), Paragraph("Spine Foundation Anchor", styles["TableCell"])],
        [Paragraph("Ashique Kuruniyan", styles["TableCellBold"]), Paragraph("€100k", styles["TableCell"]), Paragraph("€300k", styles["TableCell"]), Paragraph("€300k", styles["TableCellBold"]), Paragraph("+200.0%", styles["TableCellBold"]), Paragraph("Prime Domestic Asset Expansion", styles["TableCell"])],
        [Paragraph("Cleiton Silva", styles["TableCellBold"]), Paragraph("€350k", styles["TableCell"]), Paragraph("€350k", styles["TableCell"]), Paragraph("€100k", styles["TableCell"]), Paragraph("-71.4%", styles["TableCell"]), Paragraph("Age Depreciation Curve (37y)", styles["TableCell"])],
        [Paragraph("Sunil Chhetri", styles["TableCellBold"]), Paragraph("€175k", styles["TableCell"]), Paragraph("€175k", styles["TableCell"]), Paragraph("€50k", styles["TableCell"]), Paragraph("-71.4%", styles["TableCell"]), Paragraph("Veteran Career Climax (40y)", styles["TableCell"])],
    ]
    mv_t = Table(mv_data, colWidths=[110, 48, 48, 52, 58, 99], rowHeights=[17, 21, 21, 21, 21, 21, 21, 21])
    mv_t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BFC_NAVY),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    top_grid = Table([[chart_card, mv_t]], colWidths=[375, 415])
    story.append(top_grid)
    story.append(Spacer(1, 9))

    # Bottom 2 Cards
    v_left = [
        Paragraph("THE VALUE STORY: DOMESTIC APPRECIATION", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("Value appreciation within Bengaluru FC is almost exclusively an internal and domestic phenomenon. Inbound domestic U22 talents appreciate by an average of +580% through systematic match minutes, while foreign signings experience steep natural age-curve depreciation (-20% to -71%) as they are recruited in their late twenties or thirties for immediate championship contribution.", styles["CardBullet"]),
    ]
    v_right = [
        Paragraph("THE RECRUITMENT LESSON: BALANCED VALUATION EQUITY", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("Foreign signings must be evaluated purely as amortized competitive tools (points, trophies, leadership) with zero residual financial recovery expectations. Long-term club valuation equity must be driven entirely by domestic scouting and academy graduations.", styles["CardBullet"]),
    ]
    v_table = Table([[
        make_card_container(v_left, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6),
        make_card_container(v_right, 390, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6),
    ]], colWidths=[395, 395])
    story.append(v_table)

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 9: CURRENT SENIOR SQUAD (INTERNAL ASSETS)
# ------------------------------------------------------------------------------
def build_page_09_current_squad(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("08", "Current Squad Analysis (2024/25 Season)", "Internal Asset Roster"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Current Senior Squad Roster & Key Internal Assets", styles["PageTitle"]))
    story.append(Paragraph("Roster Hierarchy, Role Classification & Asset Valuation across 24 Senior First-Team Players", styles["PageSubtitle"]))
    story.append(Spacer(1, 7))

    # Top 4 Metrics
    m1 = make_kpi_card("24 Players", "SENIOR SQUAD SIZE", "Gerard Zaragoza Roster", 193)
    m2 = make_kpi_card("27.3 Years", "AVERAGE SQUAD AGE", "Balanced Squad Mean", 193)
    m3 = make_kpi_card("6 Players", "ACTIVE FOREIGN SLOTS", "Spain (3), Aus, Arg, MNE", 193)
    m4 = make_kpi_card("8 Players (33.3%)", "ACADEMY GRADUATES", "Homegrown Core", 193)
    top_t = Table([[m1, m2, m3, m4]], colWidths=[197.5]*4)
    story.append(top_t)
    story.append(Spacer(1, 8))

    # 8 Player Profile Cards in 2x4 Grid (ALL 8 WITH REAL PLAYER PHOTOS!)
    p1 = make_player_scout_card(
        "Gurpreet Singh Sandhu", "Goalkeeper", "32y", "India", "Joined 2017", "€200k",
        "KEY | VETERAN",
        "International shot-stopper with unmatched aerial reach and command of penalty area. Uncontested domestic No. 1 providing 8-season dressing room stability.",
        "Starting goalkeeper pillar; guarantees defensive consistency while youth develops.",
        photo_filename="gurpreet_singh_sandhu.png", width=388,
    )
    p2 = make_player_scout_card(
        "Sunil Chhetri", "Striker / Forward", "40y", "India", "Joined 2017", "€50k",
        "ICON | SUCCESSION",
        "Iconic national goalscorer with elite movement in box, clutch penalties, and leadership. Entering career climax; requires urgent phased succession plan.",
        "Offensive talisman whose impending retirement triggers immediate U24 striker recruitment.",
        photo_filename="sunil_chhetri.png", width=388,
    )
    p3 = make_player_scout_card(
        "Suresh Singh Wangjam", "Central Midfielder", "24y", "India", "Joined 2019", "€300k",
        "KEY | HIGH UPSIDE",
        "Dynamic double-pivot ball-winner with relentless pressing stamina and progressive carry. Foundational midfield anchor in prime athletic years.",
        "Highest-value domestic asset; central building block for next-generation core.",
        photo_filename="suresh_singh_wangjam.png", width=388,
    )
    p4 = make_player_scout_card(
        "Naorem Roshan Singh", "Left/Right Full-Back", "25y", "India", "Academy 2020", "€250k",
        "CORE | HIGH UPSIDE",
        "Ambidextrous full-back with world-class crossing, dead-ball delivery, and recovery pace. Primary creator from wide areas in Zaragoza's system.",
        "Elite developmental asset; non-negotiable retention priority against ISL rivals.",
        photo_filename="naorem_roshan_singh.png", width=388,
    )
    p5 = make_player_scout_card(
        "Alberto Noguera", "Attacking Midfielder", "35y", "Spain", "Joined 2024", "€250k",
        "CREATOR | SUCCESSION",
        "Supreme Spanish playmaker with exceptional scanning, line-breaking vision, and poise. Brain of Zaragoza's attacking system; age 35 creates succession risk.",
        "Key creative catalyst whose minutes must be managed alongside an emerging No. 8/10.",
        photo_filename="alberto_noguera.png", width=388,
    )
    p6 = make_player_scout_card(
        "Jorge Pereyra Díaz", "Striker / Forward", "34y", "Argentina", "Joined 2024", "€350k",
        "VETERAN FOREIGN",
        "Combative forward combining aggressive pressing, channel running, and clinical finishing. Proven ISL winner giving immediate thrust; short-term 1-2 season horizon.",
        "Championship-ready focal point requiring a younger domestic understudy.",
        photo_filename="jorge_pereyra_diaz.png", width=388,
    )
    p7 = make_player_scout_card(
        "Rahul Bheke", "Centre Back / Right Back", "33y", "India", "Joined 2024", "€175k",
        "CORE | VETERAN",
        "Versatile defender with high aerial duel prowess, box clearances, and emergency RB cover. Veteran leader offering backline versatility across competitions.",
        "Dressing room general bridging veteran stability and emerging backline talent.",
        photo_filename="rahul_bheke.png", width=388,
    )
    p8 = make_player_scout_card(
        "Vinith Venkatesh", "Attacking Midfielder", "19y", "India", "Academy 2024", "€100k",
        "ACADEMY BREAKTHROUGH",
        "Fearless academy playmaker with inventive dribbling, half-space mobility, and debut winning goal. Heir-apparent in creative midfield.",
        "Homegrown creative prodigy; requires guaranteed 15+ starts to mature into senior starter.",
        photo_filename="vinith_venkatesh.png", width=388,
    )

    grid_table = Table([[p1, p2], [p3, p4], [p5, p6], [p7, p8]], colWidths=[395, 395], rowHeights=[68, 68, 68, 68])
    grid_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(grid_table)
    story.append(Spacer(1, 5))

    # Bottom Read
    read_banner = [Paragraph(
        "<b>CURRENT SQUAD READ:</b> The 2024/25 roster is a polarized two-speed squad: an elite domestic youth platform (Suresh 24, Roshan 25, Sivasakthi 23, Vinith 19) coexists with an ultra-veteran match-winning spine (Chhetri 40, Noguera 35, Díaz 34, Jovanovic 35, Bheke 33). While the squad averages 27.3 years overall, the senior core that generates over 65% of attacking output averages 35.8 years. Succession planning is urgent.",
        styles["BannerText"],
    )]
    story.append(make_card_container(read_banner, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=5))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 10: AGE & DEPTH
# ------------------------------------------------------------------------------
def build_page_10_squad_age_depth(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("09", "Squad Age Structure & Positional Depth", "Demographic Curves"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Squad Age Structure, Positional Depth & Demographic Risk", styles["PageTitle"]))
    story.append(Paragraph("Positional Depth Curves, Demographic Imbalances & Succession Windows Across Gerard Zaragoza's Roster", styles["PageSubtitle"]))
    story.append(Spacer(1, 8))

    # Top 5 Metric Cards
    m1 = make_kpi_card("27.3y", "AVERAGE SQUAD AGE", "Balanced Overall Mean", 154)
    m2 = make_kpi_card("DM (33.0y)", "OLDEST POSITION", "Pedro Capó (33 Anchor)", 154)
    m3 = make_kpi_card("RB (20.0y)", "YOUNGEST POSITION", "Shivaldo Singh (Solo RB)", 154)
    m4 = make_kpi_card("CB (5 Players)", "STRONGEST DEPTH", "Deep Domestic & Asian Spine", 154)
    m5 = make_kpi_card("RB (1 Player)", "WEAKEST DEPTH", "Urgent Specialist Need", 154)
    top_t = Table([[m1, m2, m3, m4, m5]], colWidths=[158]*5)
    story.append(top_t)
    story.append(Spacer(1, 8))

    # Top Section: Chart on Left, Positional Table on Right
    chart_p = os.path.join(CHARTS_DIR, "squad_depth_age_matrix.png")
    chart_flow = Image(chart_p, width=355, height=172) if os.path.exists(chart_p) else Paragraph("Depth Chart", styles["CardBody"])
    chart_card = make_card_container([chart_flow], 365, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=4)

    depth_data = [
        [Paragraph("<b>Position</b>", styles["TableHead"]), Paragraph("<b>Count</b>", styles["TableHead"]), Paragraph("<b>Avg Age</b>", styles["TableHead"]), Paragraph("<b>Risk Level</b>", styles["TableHead"]), Paragraph("<b>Tactical Implication & Urgency</b>", styles["TableHead"])],
        [Paragraph("Striker / CF", styles["TableCellBold"]), Paragraph("4", styles["TableCell"]), Paragraph("32.3y", styles["TableCellBold"]), Paragraph('<font color="#D32F2F"><b>HIGH</b></font>', styles["TableCell"]), Paragraph("Chhetri (40) & Díaz (34) lead attack; urgent U24 succession required", styles["TableCell"])],
        [Paragraph("Attacking MF", styles["TableCellBold"]), Paragraph("2", styles["TableCell"]), Paragraph("29.7y", styles["TableCellBold"]), Paragraph('<font color="#D32F2F"><b>HIGH</b></font>', styles["TableCell"]), Paragraph("Noguera (35) sole proven creator; need prime-age playmaker backup", styles["TableCell"])],
        [Paragraph("Right Back", styles["TableCellBold"]), Paragraph("1", styles["TableCellBold"]), Paragraph("20.0y", styles["TableCell"]), Paragraph('<font color="#D32F2F"><b>HIGH</b></font>', styles["TableCell"]), Paragraph("Shivaldo (20) only specialist RB; Bheke deployed out of position", styles["TableCell"])],
        [Paragraph("Centre Back", styles["TableCellBold"]), Paragraph("5", styles["TableCell"]), Paragraph("30.6y", styles["TableCellBold"]), Paragraph('<font color="#F59E0B"><b>MEDIUM</b></font>', styles["TableCell"]), Paragraph("Seasoned starters (Jovanovic 35, Bheke 33) carry recovery-pace risk", styles["TableCell"])],
        [Paragraph("Goalkeeper", styles["TableCellBold"]), Paragraph("3", styles["TableCell"]), Paragraph("27.7y", styles["TableCell"]), Paragraph('<font color="#10B981"><b>LOW</b></font>', styles["TableCell"]), Paragraph("Gurpreet (32) dependable; Sahil Poonia (18) developing in reserve", styles["TableCell"])],
    ]
    depth_t = Table(depth_data, colWidths=[85, 38, 48, 55, 189], rowHeights=[18, 30, 30, 30, 30, 30])
    depth_t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BFC_NAVY),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    top_grid = Table([[chart_card, depth_t]], colWidths=[375, 415])
    story.append(top_grid)
    story.append(Spacer(1, 9))

    # Bottom 3 Cards
    b1 = [
        Paragraph("1. AGE PRESSURE", styles["CardTitleRed"]),
        Paragraph("Attacking Spine: 35.8y Avg", styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Extreme physical vulnerability in match-winners requires planned minutes management and load regulation across campaigns.", styles["CardBullet"]),
    ]
    b2 = [
        Paragraph("2. DEPTH PRESSURE", styles["CardTitleRed"]),
        Paragraph("Right-Back Structural Void", styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Lack of specialist RB forces CBs out of position, distorting defensive shape and flank progression.", styles["CardBullet"]),
    ]
    b3 = [
        Paragraph("3. SUCCESSION PRESSURE", styles["CardTitle"]),
        Paragraph("Imminent Senior Succession", styles["CardSubtitle"]),
        Spacer(1, 2),
        Paragraph("Multiple concurrent contract expirations necessitate phased pre-contract recruitment across two consecutive windows.", styles["CardBullet"]),
    ]
    bot_t = Table([[
        make_card_container(b1, 258, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(b2, 258, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
        make_card_container(b3, 258, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER),
    ]], colWidths=[263.3, 263.3, 263.3])
    story.append(bot_t)

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 11: SIX KEY CONCLUSIONS
# ------------------------------------------------------------------------------
def build_page_11_six_key_conclusions(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("10", "Six Key Conclusions from Full Sample", "Executive Synthesis"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Six Key Conclusions from Full-Sample Analytics", styles["PageTitle"]))
    story.append(Paragraph("Consolidated Findings: Export Models, Age Barbell, Valuation Dynamics & Succession Imperatives", styles["PageSubtitle"]))
    story.append(Spacer(1, 10))

    # 6 Clean White Cards in 2x3 Grid (Inspired by Cerezo Page 7)
    c_list = [
        ("01", "Opportunistic Free-Agent Model",
         "92.6% of external arrivals (50/54) acquired on free transfers; €0 transfer fee debt.",
         "Maximizes wage flexibility under salary cap; zero balance-sheet risk.",
         "Requires elite medical, physical, and psychological vetting to avoid declining wage-burdens."),
        ("02", "Bimodal Recruitment Demographics",
         "27.0y mean signing age; 42.6% in 24–26 band, 31.5% in 30+ bracket, 5.6% in 27–29 window.",
         "Bifurcated into domestic prime (24–26y) and foreign leaders (30+y).",
         "Creates an age barbell; leaves younger players without intermediate-age mentors."),
        ("03", "Attacking Spine Succession Cliff",
         "Starting attackers average 35.8 years (Chhetri 40, Noguera 35, Díaz 34, Méndez 34).",
         "Primary match-winners and creators are in late career twilight.",
         "Next two transfer windows must be dominated by U25 attacking acquisitions."),
        ("04", "Domestic Youth Value Multiplier",
         "Roshan (+900%), Udanta (+800%), Sivasakthi (+700%), and Suresh (+500%) drive 100% of value growth.",
         "Economic appreciation is strictly concentrated in domestic U23 signings.",
         "Concentrate transfer expenditures on elite domestic youth rather than aging foreign stars."),
        ("05", "Right-Back Structural Vulnerability",
         "Shivaldo Singh (20) sole natural RB; Rahul Bheke deployed out of position on right flank.",
         "Only 1 specialist right-back on roster, forcing CBs out of position.",
         "Immediate recruitment of an athletic, dynamic right-back is essential to balance back four."),
        ("06", "Complement the Core, Protect Academy Minutes",
         "5 BFC B promotions in 2023/24; Vinith (19) and Sivasakthi (23) proven ISL scorers.",
         "Recruitment must not block the development pathways of top homegrown assets.",
         "Target complementary profile starters, not squad-filler stopgaps that block young talent."),
    ]

    card_elements = []
    for num, title, data_pt, means, cons in c_list:
        content = [
            Paragraph(f'<font size=16 color="#D32F2F"><b>{num}</b></font> &nbsp;&nbsp; <font size=11 color="#0B132B"><b>{title}</b></font>', styles["CardTitle"]),
            Spacer(1, 4),
            Paragraph(f'<b>Data Point:</b> {data_pt}', styles["CardBullet"]),
            Spacer(1, 2),
            Paragraph(f'<b>What It Means:</b> {means}', styles["CardBullet"]),
            Spacer(1, 2),
            Paragraph(f'<b>Scouting Consequence:</b> {cons}', styles["CardBullet"]),
        ]
        card_elements.append(make_card_container(content, 388, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=8))

    grid_t = Table([
        [card_elements[0], card_elements[1]],
        [card_elements[2], card_elements[3]],
        [card_elements[4], card_elements[5]],
    ], colWidths=[395, 395], rowHeights=[108, 108, 108])
    grid_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(grid_t)
    story.append(Spacer(1, 8))

    synthesis_box = [Paragraph(
        "<b>STRATEGIC IMPERATIVE SYNTHESIS:</b> The convergence of these six analytical findings dictates an immediate structural pivot: Bengaluru FC must protect its proven academy-to-first-team value multiplier (+500% to +900%) while executing proactive, pre-contract domestic acquisitions to eliminate the looming succession cliff across the attacking spine (average age 35.8 years).",
        styles["BannerText"],
    )]
    story.append(make_card_container(synthesis_box, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BFC_BLUE, padding=6))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 12: SQUAD DEFICITS & RISK REGISTER
# ------------------------------------------------------------------------------
def build_page_12_squad_gaps(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("11", "Squad Gaps & Strategic Risk Register", "Deficit Identification"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Squad Deficits, Succession Risks & Governance Triggers", styles["PageTitle"]))
    story.append(Paragraph("Automated Detection of Positional Voids, Age Risks & Succession Imperatives Across Gerard Zaragoza's Roster", styles["PageSubtitle"]))
    story.append(Spacer(1, 10))

    # Risk Register Table
    r_data = [
        [Paragraph("<b>Priority</b>", styles["TableHead"]), Paragraph("<b>Position</b>", styles["TableHead"]), Paragraph("<b>Depth / Age</b>", styles["TableHead"]), Paragraph("<b>Current Situation & Core Strategic Risk</b>", styles["TableHead"]), Paragraph("<b>Why It Matters (Impact)</b>", styles["TableHead"]), Paragraph("<b>Actionable Recruitment Response</b>", styles["TableHead"])],
        [Paragraph('<font color="#D32F2F"><b>HIGH</b></font>', styles["TableCell"]), Paragraph("Striker / CF", styles["TableCellBold"]), Paragraph("4 / 32.3y", styles["TableCell"]), Paragraph("Chhetri (40) & Díaz (34) lead attack; Sivasakthi (23) needs prime-age partner.", styles["TableCell"]), Paragraph("Imminent retirement cliff; loss of 65% of team goal contribution.", styles["TableCell"]), Paragraph("Recruit dynamic, high-pressing domestic U24 striker (David Lalhlansanga / Irfan Yadwad).", styles["TableCell"])],
        [Paragraph('<font color="#D32F2F"><b>HIGH</b></font>', styles["TableCell"]), Paragraph("Attacking MF", styles["TableCellBold"]), Paragraph("2 / 29.7y", styles["TableCell"]), Paragraph("Noguera (35) sole proven creator; Vinith (19) requires progressive adaptation.", styles["TableCell"]), Paragraph("Extreme xG drop when Noguera is absent; lack of prime playmaker.", styles["TableCell"]), Paragraph("Target prime-age creative midfielder (Age 22–26, Vibin Mohanan) with elite progressive passing.", styles["TableCell"])],
        [Paragraph('<font color="#D32F2F"><b>HIGH</b></font>', styles["TableCell"]), Paragraph("Right Back", styles["TableCellBold"]), Paragraph("1 / 20.0y", styles["TableCell"]), Paragraph("Shivaldo Singh (20) sole natural RB; Bheke deployed out of position on flank.", styles["TableCell"]), Paragraph("Asymmetric attacking shape; defensive isolation on wide counters.", styles["TableCell"]), Paragraph("Sign starting-caliber dynamic right-back (Aakash Sangwan / Jay Gupta cover).", styles["TableCell"])],
        [Paragraph('<font color="#F59E0B"><b>MEDIUM</b></font>', styles["TableCell"]), Paragraph("Ball-Playing CB", styles["TableCellBold"]), Paragraph("5 / 30.6y", styles["TableCell"]), Paragraph("Jovanovic (35) & Bheke (33) aging; Sana Singh (27) prime domestic anchor.", styles["TableCell"]), Paragraph("Backline vulnerability against rapid transitional counter-attacks.", styles["TableCell"]), Paragraph("Acquire athletic U26 left-footed CB (domestic or Asian AFC quota).", styles["TableCell"])],
        [Paragraph('<font color="#10B981"><b>LOW</b></font>', styles["TableCell"]), Paragraph("U23 Goalkeeper", styles["TableCellBold"]), Paragraph("3 / 27.7y", styles["TableCell"]), Paragraph("Gurpreet (32) elite starter; Ralte (31) backup; Sahil Poonia (18) developing.", styles["TableCell"]), Paragraph("Need long-term succession plan for India's No. 1 goalkeeper.", styles["TableCell"]), Paragraph("Maintain systematic cup starts for Sahil Poonia; monitor U23 domestic keepers.", styles["TableCell"])],
        [Paragraph('<font color="#10B981"><b>LOW</b></font>', styles["TableCell"]), Paragraph("Central Midfield", styles["TableCellBold"]), Paragraph("4 / 26.5y", styles["TableCell"]), Paragraph("Suresh (24) prime anchor; Capó (33) veteran; Fanai (20) rotational depth.", styles["TableCell"]), Paragraph("Over-recruiting midfield risks blocking minutes for academy youth.", styles["TableCell"]), Paragraph("Enforce rotational minutes protocol; avoid stopgap veteran midfield signings.", styles["TableCell"])],
    ]
    risk_t = Table(r_data, colWidths=[52, 90, 68, 195, 185, 200], rowHeights=[22, 48, 48, 48, 48, 48, 48])
    risk_t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BFC_NAVY),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(risk_t)
    story.append(Spacer(1, 12))

    # Governance Triggers Banner
    gov = [Paragraph(
        "<b>RISK GOVERNANCE & ACTION TRIGGERS:</b> 1. Availability Threshold: Any starter aged 34+ logging <70% availability triggers immediate pre-contract execution for replacement. 2. Squad Youth Quota: Minimum 4 U23 domestic players must log >800 minutes per campaign to sustain value appreciation. 3. Right-Back Priority: The absence of an established right-back represents the single largest structural vulnerability in the current squad.",
        styles["BannerText"],
    )]
    story.append(make_card_container(gov, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BFC_BLUE, padding=9))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 13: IDEAL RECRUITMENT PROFILES
# ------------------------------------------------------------------------------
def build_page_13_recruitment_profiles(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("12", "Suggested Profiles to Complement the Squad", "Target Archetypes"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Suggested Profiles to Complement the Squad", styles["PageTitle"]))
    story.append(Paragraph("These Profiles Should Improve Balance Without Suppressing the Development Pathway for Current Young Assets", styles["PageSubtitle"]))
    story.append(Spacer(1, 9))

    # 4 Profile Cards (Inspired by Cerezo Page 8)
    p1 = [
        Paragraph("Dynamic Striker", styles["CardTitle"]),
        Paragraph('<font size=7 color="#D32F2F"><b>PRIORITY: HIGH</b></font>', styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("<b>Target Age:</b> 20–25y | <b>Val:</b> €150k-€350k", styles["CardBullet"]),
        Paragraph("<b>Gap:</b> Succession risk for Sunil Chhetri (40) & Jorge Pereyra Díaz (34).", styles["CardBullet"]),
        Paragraph("<b>Attributes:</b> High pressing volume, clinical box finishing, transitional burst, aerial target ability.", styles["CardBullet"]),
        Paragraph("<b>Tactical Need:</b> Direct goal output with relentless defensive workrate.", styles["CardBullet"]),
    ]
    p2 = [
        Paragraph("Creative Interior Midfielder", styles["CardTitle"]),
        Paragraph('<font size=7 color="#D32F2F"><b>PRIORITY: HIGH</b></font>', styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("<b>Target Age:</b> 22–27y | <b>Val:</b> €200k-€450k", styles["CardBullet"]),
        Paragraph("<b>Gap:</b> Age & creative succession risk for Alberto Noguera (35).", styles["CardBullet"]),
        Paragraph("<b>Attributes:</b> Key passing, half-turn under pressure, spatial awareness between lines, tempo control (>82%).", styles["CardBullet"]),
        Paragraph("<b>Tactical Need:</b> Adds angles and chance creation between lines.", styles["CardBullet"]),
    ]
    p3 = [
        Paragraph("Ball-Playing Centre Back", styles["CardTitle"]),
        Paragraph('<font size=7 color="#F59E0B"><b>PRIORITY: MEDIUM</b></font>', styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("<b>Target Age:</b> 21–26y | <b>Val:</b> €150k-€300k", styles["CardBullet"]),
        Paragraph("<b>Gap:</b> Depth & recovery pace risk for Jovanovic (35) and Bheke (33).", styles["CardBullet"]),
        Paragraph("<b>Attributes:</b> Progressive ground passes, high recovery speed, aerial duel success (>65%), tactical composure.", styles["CardBullet"]),
        Paragraph("<b>Tactical Need:</b> Left-sided or central defender with clean progression.", styles["CardBullet"]),
    ]
    p4 = [
        Paragraph("Full-Back Depth (Dynamic)", styles["CardTitle"]),
        Paragraph('<font size=7 color="#F59E0B"><b>PRIORITY: MEDIUM</b></font>', styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("<b>Target Age:</b> 21–26y | <b>Val:</b> €100k-€250k", styles["CardBullet"]),
        Paragraph("<b>Gap:</b> Positional depth void and over-reliance on Roshan Singh.", styles["CardBullet"]),
        Paragraph("<b>Attributes:</b> Sustained sprinting overlaps, accurate low crossing, 1v1 defensive containment, inverted passing.", styles["CardBullet"]),
        Paragraph("<b>Tactical Need:</b> Competitive rotation with tactical discipline and delivery.", styles["CardBullet"]),
    ]

    cards_t = Table([[
        make_card_container(p1, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=7),
        make_card_container(p2, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=7),
        make_card_container(p3, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=7),
        make_card_container(p4, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=7),
    ]], colWidths=[197.5]*4)
    story.append(cards_t)
    story.append(Spacer(1, 8))

    # Scouting Shortlist Box (Cerezo Page 8 bottom section)
    s_content = [
        Paragraph("SCOUTING SHORTLIST OVERVIEW (CANDIDATES MAPPED TO ROLES)", styles["CardTitle"]),
        Paragraph("Initial shortlist of players who fit the priority roles. Selected profiles are explored in detail in the following section.", styles["CardSubtitle"]),
        Spacer(1, 4),
        Paragraph("• <b>Dynamic Striker / Centre-Forward:</b> David Lalhlansanga (East Bengal) &nbsp;•&nbsp; Irfan Yadwad (Chennaiyin FC) &nbsp;•&nbsp; Parthib Gogoi (NorthEast United)", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Creative Interior Midfielder (No. 8/10):</b> Vibin Mohanan (Kerala Blasters) &nbsp;•&nbsp; Brison Fernandes (FC Goa) &nbsp;•&nbsp; Ayush Adhikari (Chennaiyin FC)", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Ball-Playing Centre Back:</b> Bikash Yumnam (Kerala Blasters) &nbsp;•&nbsp; Hormipam Ruivah (Kerala Blasters) &nbsp;•&nbsp; Asian Quota Target (A-League / J2)", styles["CardBullet"]),
        Spacer(1, 2),
        Paragraph("• <b>Attacking Dynamic Full-Back:</b> Aakash Sangwan (FC Goa) &nbsp;•&nbsp; Jay Gupta (FC Goa) &nbsp;•&nbsp; Amey Ranawade (Odisha FC)", styles["CardBullet"]),
    ]
    story.append(make_card_container(s_content, 790, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=7))
    story.append(Spacer(1, 7))

    # Scouting Protocol Funnel
    pipeline_box = [
        Paragraph("FOUR-STAGE RECRUITMENT FILTERING & VALIDATION PROTOCOL:", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("<b>Phase 1 (Metric Funnel):</b> Age 20–26, contract expiry ≤ 12 months, >65% match involvement. &nbsp;|&nbsp; <b>Phase 2 (Tactical Video Tagging):</b> 5 complete 90-min matches evaluated on pressing triggers and pass progression.<br/><b>Phase 3 (Live Scouting & Physical Audit):</b> In-stadium appraisal of spatial awareness, recovery pace, and work ethic. &nbsp;|&nbsp; <b>Phase 4 (Executive Pre-Contract):</b> Technical Committee review, medical diligence, and wage cap modeling.", styles["CardBullet"]),
    ]
    story.append(make_card_container(pipeline_box, 790, bg_color=COLOR_CARD_BG, border_color=COLOR_BFC_BLUE, padding=6))
    story.append(Spacer(1, 7))

    # Integrity Note
    note = [Paragraph(
        "<b>METHODOLOGICAL INTEGRITY NOTE:</b> Ideal recruitment profiles are generated strictly from empirical squad deficits, not ad-hoc scouting preference. Candidates shortlisted on subsequent pages must satisfy at least 80% of these structural attributes to advance to live video and live match scouting validation.",
        styles["BannerText"],
    )]
    story.append(make_card_container(note, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=5))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 14: PLAYER SHORTLIST & 100-POINT FIT SCORING
# ------------------------------------------------------------------------------
def build_page_14_player_shortlist(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("13", "Priority Profiles & Shortlist Target Dossiers", "Target Evaluations"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Priority Profiles & Shortlist Target Dossiers", styles["PageTitle"]))
    story.append(Paragraph("Concrete Targets Assessed Against Tactical Fit, Market Valuation & Development Ceiling", styles["PageSubtitle"]))
    story.append(Spacer(1, 8))

    # Left Column: Radar Chart + Criteria + Disclaimer (Width 255 pt)
    radar_p = os.path.join(CHARTS_DIR, "shortlist_radar.png")
    radar_flow = Image(radar_p, width=245, height=155) if os.path.exists(radar_p) else Paragraph("Radar Unavailable", styles["CardBody"])
    radar_card = make_card_container([radar_flow], 252, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=4)

    crit_box = [
        Paragraph("100-PT WEIGHTED FIT CRITERIA:", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("• Age Fit (20%) &nbsp;• Positional Fit (20%)<br/>• Performance Fit (20%) &nbsp;• Playing Style Fit (15%)<br/>• Market Value Fit (15%) &nbsp;• Upside Potential (10%)", styles["CardBullet"]),
        Spacer(1, 4),
        Paragraph("<b>Heuristic Disclaimer:</b> Fit scores (92.4, 92.0, 90.2) are heuristic multi-criteria scouting valuations based on age, positional fit, and tactical style—NOT match-event data ratings.", ParagraphStyle("DISC", fontName="Helvetica-Oblique", fontSize=6.8, leading=8.5, textColor=COLOR_TEXT_MUTED)),
    ]
    crit_card = make_card_container(crit_box, 252, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER, padding=6)
    left_column = [radar_card, Spacer(1, 5), crit_card]

    # Right Column: 3 Detailed Target Cards with REAL PHOTOS! (Width 525 pt)
    t1 = make_player_scout_card(
        "David Lalhlansanga", "Dynamic Striker / Centre-Forward", "23y", "India", "East Bengal FC", "€175k | Right Foot",
        None,
        "Explosive, high-pressing forward with quick trigger finishing inside the box and relentless energy off the ball. Elite channel runner.",
        "Direct succession solution for Sunil Chhetri's pressing and domestic goal contribution; young enough to form a decade-long partnership with Sivasakthi.",
        photo_filename="david_lalhlansanga.png", fit_score="92.4/100",
        watchout="Contract negotiation friction with rival Kolkata club; adapting to sustained possession phases.",
        width=518, is_shortlist=True,
    )
    t2 = make_player_scout_card(
        "Vibin Mohanan", "Creative Midfielder / No. 8 & 10 Hybrid", "21y", "India", "Kerala Blasters FC", "€225k | Right Foot",
        None,
        "Deep-lying playmaker and progressive carrier with exceptional tactical vision, line-breaking passes, and poise under pressure.",
        "Solves Bengaluru's upcoming creative succession once Noguera leaves; pairs seamlessly alongside defensive anchor Suresh Singh Wangjam.",
        photo_filename="vibin_mohanan.png", fit_score="92.0/100",
        watchout="Rivalry buyout premium; physical conditioning over 90 minutes in high-tempo fixtures.",
        width=518, is_shortlist=True,
    )
    t3 = make_player_scout_card(
        "Muhammed Sanan", "High Upside Attacking Winger", "20y", "India", "Jamshedpur FC", "€150k | Right Foot",
        None,
        "Direct, electric 1v1 dribbler with rapid acceleration, fearless take-on ability, and instinctive box arrival from wide corridors.",
        "Injects youth dynamism and vertical unpredictability out wide behind Édgar Méndez (34) and Ryan Williams (30).",
        photo_filename="muhammed_sanan.png", fit_score="90.2/100",
        watchout="Inconsistent decision-making and final pass execution in final third.",
        width=518, is_shortlist=True,
    )

    right_column = [t1, Spacer(1, 4), t2, Spacer(1, 4), t3]

    main_grid = Table([[left_column, right_column]], colWidths=[260, 530])
    main_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(main_grid)
    story.append(Spacer(1, 6))

    # Bottom Shortlist Synthesis
    roadmap_box = [Paragraph(
        "<b>SHORTLIST STRATEGIC SYNTHESIS & ACQUISITION SEQUENCING:</b> The three evaluated targets directly resolve the acute succession cliffs identified across Bengaluru FC's aging spine. David Lalhlansanga (92.4) offers immediate high-pressing box intensity to phase Sunil Chhetri's load; Vibin Mohanan (92.0) secures elite progressive orchestration before Alberto Noguera departs; Muhammed Sanan (90.2) delivers vertical 1v1 transitional pace on the wings. Immediate pre-contract negotiation is strongly advised.",
        styles["BannerText"],
    )]
    story.append(make_card_container(roadmap_box, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BFC_BLUE, padding=6))

    story.append(PageBreak())
    return story


# ------------------------------------------------------------------------------
# PAGE 15: FINAL STRATEGY & ACTION PLAN
# ------------------------------------------------------------------------------
def build_page_15_final_strategy(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story = []
    story.append(make_club_header("14", "Final Recruitment Strategy & Action Plan", "Operational Mandates"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Strategic Recruitment Roadmap & Action Plan", styles["PageTitle"]))
    story.append(Paragraph("The 4-Pillar Strategic Squad Roadmap: Retain Core Domestic Assets, Develop Academy, Replace Veterans, Recruit Gaps", styles["PageSubtitle"]))
    story.append(Spacer(1, 8))

    # 4 Strategy Cards Across Top
    c_retain = [
        Paragraph("RETAIN (CORE ASSETS)", styles["CardTitle"]),
        Paragraph("Protect prime domestic spine:", styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("• <b>Suresh Singh Wangjam:</b> Central Midfield Anchor - Prime Foundation.", styles["CardBullet"]),
        Paragraph("• <b>Naorem Roshan Singh:</b> Left/Right Dynamic Fullback - National Starter.", styles["CardBullet"]),
        Paragraph("• <b>Gurpreet Singh Sandhu:</b> Goalkeeping Leadership & Box Command.", styles["CardBullet"]),
        Paragraph("• <b>Chinglensana Singh:</b> Domestic CB Core - Prime Age 27.", styles["CardBullet"]),
    ]
    c_develop = [
        Paragraph("DEVELOP (ACADEMY)", styles["CardTitle"]),
        Paragraph("Guarantee first-team minutes:", styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("• <b>Vinith Venkatesh (19):</b> Breakthrough AM - Target 15+ Starts.", styles["CardBullet"]),
        Paragraph("• <b>Sivasakthi Narayanan (23):</b> Striker - Elevate to First-Choice.", styles["CardBullet"]),
        Paragraph("• <b>Robin Yadav (22):</b> CB - Systematic Cup & Rotational Minutes.", styles["CardBullet"]),
        Paragraph("• <b>Lalremtluanga Fanai & Molla:</b> Youth Integration Pipeline.", styles["CardBullet"]),
    ]
    c_replace = [
        Paragraph("REPLACE (VETERANS)", styles["CardTitleRed"]),
        Paragraph("Manage contract transitions:", styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("• <b>Sunil Chhetri (40):</b> Striker - Phased transition to advisory role.", styles["CardBullet"]),
        Paragraph("• <b>Alberto Noguera (35):</b> Attacking MF - Successor required.", styles["CardBullet"]),
        Paragraph("• <b>Aleksandar Jovanovic (35):</b> CB - Transition to younger athletic CB.", styles["CardBullet"]),
        Paragraph("• <b>Jorge Pereyra Díaz (34):</b> Striker - Transition slot to prime asset.", styles["CardBullet"]),
    ]
    c_recruit = [
        Paragraph("RECRUIT (GAPS)", styles["CardTitle"]),
        Paragraph("Execute priority acquisitions:", styles["CardSubtitle"]),
        Spacer(1, 3),
        Paragraph("• <b>Target 1:</b> Dynamic U24 Striker (David Lalhlansanga / Irfan Yadwad).", styles["CardBullet"]),
        Paragraph("• <b>Target 2:</b> Prime Creative Midfielder / No. 8 & 10 (Vibin Mohanan).", styles["CardBullet"]),
        Paragraph("• <b>Target 3:</b> Athletic Ball-Playing CB (Left-Footed domestic/Asian).", styles["CardBullet"]),
        Paragraph("• <b>Target 4:</b> High-Intensity Attacking Right-Back Cover.", styles["CardBullet"]),
    ]

    top_grid = Table([[
        make_card_container(c_retain, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BFC_BLUE, padding=6),
        make_card_container(c_develop, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_SUCCESS, padding=6),
        make_card_container(c_replace, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_WARNING, padding=6),
        make_card_container(c_recruit, 189, bg_color=COLOR_CARD_BG, border_color=COLOR_BFC_RED, padding=6),
    ]], colWidths=[197.5]*4)
    story.append(top_grid)
    story.append(Spacer(1, 8))

    # Middle Timeline
    timeline_box = [
        Paragraph("STRATEGIC TRANSFER TIMELINE ACROSS THREE WINDOWS:", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph("• <b>Immediate Window:</b> Execute pre-contracts for David Lalhlansanga & Vibin Mohanan; acquire starting-caliber dynamic right-back.", styles["CardBullet"]),
        Paragraph("• <b>Medium-Term Window:</b> Reallocate foreign wage budget into prime-age international playmaker (26–29y); review loan returns.", styles["CardBullet"]),
        Paragraph("• <b>Long-Term Window:</b> Complete transition of central defensive core; institute structured academy promotion quota (min 2 BFC B/yr).", styles["CardBullet"]),
    ]
    story.append(make_card_container(timeline_box, 790, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6))
    story.append(Spacer(1, 8))

    # Executive Mandate
    mandate_box = [
        Paragraph("SPORTING DIRECTOR & TECHNICAL LEADERSHIP EXECUTIVE MANDATE:", styles["CardTitle"]),
        Spacer(1, 3),
        Paragraph("1. <b>Maintain Financial Discipline:</b> Preserve Bengaluru FC's elite 92.6% free-agent acquisition model, avoiding speculative transfer fee inflation.", styles["CardBullet"]),
        Paragraph("2. <b>Pivot to Active Targeting:</b> Shift from reactive summer contract opportunism to aggressive pre-contract identification 6–12 months in advance.", styles["CardBullet"]),
        Paragraph("3. <b>Execute Attacking Succession:</b> Prioritize immediate domestic U24 acquisitions (David Lalhlansanga, Vibin Mohanan) to replace the 35.8y veteran attacking spine.", styles["CardBullet"]),
        Paragraph("4. <b>Resolve Right-Back Deficit:</b> Secure a starting-caliber right-back immediately to restore tactical balance to Gerard Zaragoza's back four.", styles["CardBullet"]),
        Paragraph("5. <b>Protect Academy Asset Equity:</b> Guarantee first-team match minutes for Vinith Venkatesh and Sivasakthi Narayanan, sustaining the club's +500% to +900% developmental appreciation curve.", styles["CardBullet"]),
        Paragraph("6. <b>Wage-Neutral Foreign Transition:</b> Reinvest departing veteran foreign salaries into athletic prime-age overseas players to secure sustainable championship contention.", styles["CardBullet"]),
    ]
    story.append(make_card_container(mandate_box, 790, bg_color=COLOR_CARD_ALT, border_color=COLOR_BFC_BLUE, padding=6))
    story.append(Spacer(1, 8))

    # Ratification Sign-off
    ratification_box = [Paragraph(
        "<b>TECHNICAL COMMITTEE RATIFICATION & GOVERNANCE SIGN-OFF:</b> This recruitment intelligence dossier serves as the binding strategic squad planning blueprint for upcoming ISL transfer windows. Unanimously submitted for executive implementation by Bengaluru FC Football Operations and Technical Leadership.",
        styles["BannerText"],
    )]
    story.append(make_card_container(ratification_box, 790, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, padding=6))

    return story


# ==============================================================================
# MAIN COMPILER
# ==============================================================================

def generate_pdf_report():
    logger.info("Compiling Bengaluru FC 15-Page Professional Scouting Dossier PDF (Cerezo Osaka Design Standard)...")
    styles = get_report_styles()

    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=landscape(A4),
        leftMargin=26,
        rightMargin=26,
        topMargin=20,
        bottomMargin=22,
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

    doc.build(story, onFirstPage=draw_page_background, onLaterPages=draw_page_background, canvasmaker=NumberedCanvas)
    logger.info(f"Report successfully generated at: {PDF_PATH}")


if __name__ == "__main__":
    generate_pdf_report()
