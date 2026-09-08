"""
src/generate_report.py
Generates an elite, presentation-grade, 15-page executive football scouting dossier for Bengaluru FC
using ReportLab with a dark football intelligence theme, directly modeled on professional European
and J-League scouting dossiers (Cerezo Osaka reference benchmark).

Design Specifications:
- Landscape A4 (841.89 x 595.27 pt)
- Target Club: Bengaluru FC
- Palette: Dark Navy (#0B111E / #0B192C), BFC Royal Blue (#003B95), Crimson Red (#DC2626 / #EF4444), Accent Sky (#38BDF8), White (#F8FAFC), Slate Grey (#94A3B8 / #334155)
- Core Storytelling Arc: QUESTION -> DATA -> WHAT IT MEANS -> SCOUTING IMPLICATION -> DECISION
- Exactly 15 Pages, each designed as a high-density, editorial slide with 75-90% page utilization.
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

# Color Palette (Bengaluru FC Dossier Theme)
COLOR_BG = colors.HexColor("#0B111E")          # Pitch Dark Navy
COLOR_CARD_BG = colors.HexColor("#0F172A")     # Rich Dark Slate Card
COLOR_CARD_ALT = colors.HexColor("#1E293B")    # Medium Slate Card
COLOR_CARD_DARK = colors.HexColor("#070D18")   # Deep Charcoal Navy
COLOR_BFC_BLUE = colors.HexColor("#003B95")    # BFC Royal Blue
COLOR_BFC_NAVY = colors.HexColor("#002244")    # BFC Deep Navy
COLOR_BFC_RED = colors.HexColor("#DC2626")     # BFC Crimson Red
COLOR_ACCENT_SKY = colors.HexColor("#38BDF8")  # Electric Cyan / Sky
COLOR_TEXT_LIGHT = colors.HexColor("#F8FAFC")  # Crisp Off-White
COLOR_TEXT_MUTED = colors.HexColor("#94A3B8")  # Slate Muted Grey
COLOR_BORDER = colors.HexColor("#334155")      # Card Boundary Slate
COLOR_BORDER_SUBTLE = colors.HexColor("#1E3E62")# Subtle Navy Accent
COLOR_SUCCESS = colors.HexColor("#10B981")     # Green
COLOR_WARNING = colors.HexColor("#F59E0B")     # Amber


class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas that renders the dark pitch background, top accent gradient strips,
    and bottom dossier running footer with dynamic total page count.
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

        # 1. Base Dark Pitch Background
        self.setFillColor(COLOR_BG)
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)

        # Skip header/footer chrome on Cover Page (Page 1)
        if self._pageNumber > 1:
            # Top Accent Strip (BFC Blue 72% | BFC Crimson 28%)
            self.setFillColor(COLOR_BFC_BLUE)
            self.rect(0, PAGE_HEIGHT - 5, PAGE_WIDTH * 0.72, 5, fill=True, stroke=False)
            self.setFillColor(COLOR_BFC_RED)
            self.rect(PAGE_WIDTH * 0.72, PAGE_HEIGHT - 5, PAGE_WIDTH * 0.28, 5, fill=True, stroke=False)

            # Footer Divider Line
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.6)
            self.line(26, 22, PAGE_WIDTH - 26, 22)

            # Footer Metadata
            self.setFont("Helvetica-Bold", 7)
            self.setFillColor(COLOR_TEXT_MUTED)
            self.drawString(26, 12, "BENGALURU FC RECRUITMENT INTELLIGENCE  |  CONFIDENTIAL SCOUTING DOSSIER (2020/21 – 2024/25)")

            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(COLOR_ACCENT_SKY)
            page_str = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(PAGE_WIDTH - 26, 12, page_str)

        self.restoreState()


def get_report_styles():
    """Defines typographic styles with tight, proportional leadings."""
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
            fontSize=9.5,
            leading=13,
            textColor=COLOR_TEXT_MUTED,
            alignment=1,
        ),
        "HeaderKicker": ParagraphStyle(
            "HeaderKicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=8,
            textColor=COLOR_ACCENT_SKY,
        ),
        "HeaderClubName": ParagraphStyle(
            "HeaderClubName",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=15,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "SlideTitle": ParagraphStyle(
            "SlideTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "SlideSubtitle": ParagraphStyle(
            "SlideSubtitle",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_ACCENT_SKY,
        ),
        "CardTitle": ParagraphStyle(
            "CardTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=COLOR_ACCENT_SKY,
        ),
        "CardTitleWhite": ParagraphStyle(
            "CardTitleWhite",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "CardTitleRed": ParagraphStyle(
            "CardTitleRed",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=COLOR_BFC_RED,
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
            fontSize=6.8,
            leading=8.5,
            textColor=COLOR_TEXT_MUTED,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "BodyMuted": ParagraphStyle(
            "BodyMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.8,
            textColor=COLOR_TEXT_MUTED,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=COLOR_ACCENT_SKY,
            alignment=0,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.8,
            leading=8.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
        "TableCellMuted": ParagraphStyle(
            "TableCellMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.4,
            leading=8,
            textColor=COLOR_TEXT_MUTED,
        ),
        "BadgeHigh": ParagraphStyle(
            "BadgeHigh",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=7.5,
            textColor=COLOR_BFC_RED,
        ),
        "BadgeMedium": ParagraphStyle(
            "BadgeMedium",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=7.5,
            textColor=COLOR_WARNING,
        ),
        "BadgeLow": ParagraphStyle(
            "BadgeLow",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=7.5,
            textColor=COLOR_SUCCESS,
        ),
        "BadgeSky": ParagraphStyle(
            "BadgeSky",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=7.5,
            textColor=COLOR_ACCENT_SKY,
        ),
        "ConclusionNum": ParagraphStyle(
            "ConclusionNum",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=COLOR_BFC_RED,
        ),
        "ConclusionTitle": ParagraphStyle(
            "ConclusionTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=COLOR_TEXT_LIGHT,
        ),
    }
    return styles


def create_header_banner(title: str, subtitle: str, styles: Dict[str, ParagraphStyle]) -> Table:
    """
    Standardized, compact header banner modeled directly on the Cerezo Osaka report.
    Displays club insignia, club identity, section title, and editorial framing question.
    """
    crest_path = os.path.join(ASSETS_DIR, "logo", "bfc_crest.png")
    if os.path.exists(crest_path):
        crest_img = Image(crest_path, width=24, height=24)
    else:
        crest_img = Paragraph("<b>BFC</b>", styles["TableHeader"])

    left_block = Table(
        [
            [crest_img, Table([[Paragraph("SCOUTING REPORT", styles["HeaderKicker"])],
                               [Paragraph("Bengaluru FC", styles["HeaderClubName"])]],
                              colWidths=[130])]
        ],
        colWidths=[28, 134]
    )
    left_block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    right_block = Table(
        [
            [Paragraph(title.upper(), styles["SlideTitle"])],
            [Paragraph(subtitle, styles["SlideSubtitle"])],
        ],
        colWidths=[618]
    )
    right_block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    banner_table = Table([[left_block, right_block]], colWidths=[166, 620])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER_SUBTLE),
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, COLOR_BFC_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return banner_table


def build_kpi_card(title: str, value: str, note: str, styles: Dict[str, ParagraphStyle], width: float = 127) -> Table:
    """Builds a compact, pitch-dark KPI card."""
    content = [
        [Paragraph(title.upper(), styles["CardTitle"])],
        [Paragraph(value, styles["CardValue"])],
        [Paragraph(note, styles["CardText"])],
    ]
    t = Table(content, colWidths=[width], rowHeights=[11, 20, 12])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def build_editorial_box(title: str, subtitle: str, bullets: List[str], styles: Dict[str, ParagraphStyle],
                         width: float = 388, is_dark: bool = False, kicker: str = "") -> Table:
    """Builds a 2-column style editorial card modeled on Cerezo Image 2."""
    rows = []
    if kicker:
        rows.append([Paragraph(kicker.upper(), styles["BadgeHigh"])])
    rows.append([Paragraph(f"<b>{title}</b>", styles["CardTitleWhite"] if is_dark else styles["CardTitle"])])
    if subtitle:
        rows.append([Paragraph(subtitle, styles["TableCellMuted"])])
    
    bullet_items = []
    for b in bullets:
        bullet_items.append([Paragraph(f"&bull; {b}", styles["Body"])])
    
    b_table = Table(bullet_items, colWidths=[width - 16])
    b_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    rows.append([b_table])

    t = Table(rows, colWidths=[width])
    bg_color = COLOR_CARD_DARK if is_dark else COLOR_CARD_BG
    border_color = COLOR_BFC_BLUE if is_dark else COLOR_BORDER
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 0.75, border_color),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ==============================================================================
# SLIDE BUILDERS (15 PAGES)
# ==============================================================================

def build_page_01_cover(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 1: Cover Page — Clean, Premium Football Scouting Dossier"""
    story = [
        Spacer(1, 36),
    ]

    crest_path = os.path.join(ASSETS_DIR, "logo", "bfc_crest.png")
    if os.path.exists(crest_path):
        story.append(Image(crest_path, width=1.6 * inch, height=1.6 * inch))
        story.append(Spacer(1, 16))

    story.append(Paragraph("BENGALURU FC", styles["CoverTitle"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("SCOUTING & RECRUITMENT DOSSIER", styles["CoverSubtitle"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("RECRUITMENT INTELLIGENCE & SQUAD PLANNING (2020/21 – 2024/25)", styles["CoverMeta"]))
    story.append(Spacer(1, 14))

    # Scope Pills
    scope_pills = [
        [
            Paragraph("<b>1. Historical Transfers</b>", styles["TableHeader"]),
            Paragraph("<b>2. Squad Dynamics</b>", styles["TableHeader"]),
            Paragraph("<b>3. Career Pathways</b>", styles["TableHeader"]),
            Paragraph("<b>4. Value Appreciation</b>", styles["TableHeader"]),
            Paragraph("<b>5. Strategic Roadmap</b>", styles["TableHeader"]),
        ]
    ]
    t_pills = Table(scope_pills, colWidths=[150, 150, 150, 150, 150])
    t_pills.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_pills)
    story.append(Spacer(1, 24))

    # Metadata Card
    details_data = [
        [
            Paragraph("<b>Prepared by:</b> Ayush Singh", styles["Body"]),
            Paragraph("<b>Focus Club:</b> Bengaluru FC (Indian Super League)", styles["Body"]),
        ],
        [
            Paragraph("<b>Analytical Scope:</b> 5 Seasons (2020/21 – 2024/25)", styles["Body"]),
            Paragraph("<b>Dataset Baseline:</b> 106 Transfer Events (101 Ext + 5 Academy)", styles["Body"]),
        ],
        [
            Paragraph("<b>Methodological Framework:</b> Gap-Driven Recruitment Engine", styles["Body"]),
            Paragraph("<b>Data Governance:</b> 100% Verified Non-Synthetic Historicals", styles["Body"]),
        ],
    ]
    t_det = Table(details_data, colWidths=[375, 375])
    t_det.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_det)
    story.append(Spacer(1, 24))
    story.append(Paragraph("CONFIDENTIAL SCOUTING DOSSIER  |  FOR SPORTING DIRECTORS & TECHNICAL LEADERSHIP", styles["CoverMeta"]))
    story.append(PageBreak())
    return story


def build_page_02_executive_summary(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 2: Executive Summary — Cerezo Osaka KPI & Editorial Structure"""
    story = [
        create_header_banner("01. Executive Summary", "Analytical Scope, Dashboard Overview & Methodological Pipeline", styles),
        Spacer(1, 6),
    ]

    # Top Row: 6 KPI Cards (Width 130 each = 780 pt)
    card1 = build_kpi_card("Transfer Events", "106", "101 Ext + 5 Academy", styles, width=128)
    card2 = build_kpi_card("External Signings", "54", "50 Free + 4 Loans", styles, width=128)
    card3 = build_kpi_card("Avg Signing Age", "27.0y", "Bimodal (24-26 & 30+)", styles, width=128)
    card4 = build_kpi_card("Free External %", "92.6%", "50/54 External Free", styles, width=128)
    card5 = build_kpi_card("Domestic Share", "57.4%", "31 Domestic Signings", styles, width=128)
    card6 = build_kpi_card("Academy Prom.", "5", "Zero-Fee Internal Spine", styles, width=128)

    kpi_table = Table([[card1, card2, card3, card4, card5, card6]], colWidths=[131] * 6)
    kpi_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6))

    # Middle: 2 Editorial Callout Cards (Cerezo Image 2 pattern)
    history_bullets = [
        "<b>Zero Fee Exposure:</b> 92.6% of external arrivals secured on free transfers, insulating club balance sheets from transfer fee depreciation.",
        "<b>Bimodal Age Demographics:</b> Recruitment targets domestic prime talent (24–26y, 42.6%) and foreign leaders (30+y, 31.5%), bypassing inflated 27–29 fees.",
        "<b>Central Spine Priority:</b> Signings concentrate heavily on central defense (20 signings, 37.0%) and attacking match-winners (15 signings, 27.8%).",
        "<b>Domestic Continuity:</b> High-tenure Indian starters (Suresh, Roshan, Chhetri, Gurpreet) anchor the team across multiple coaching changes.",
    ]
    squad_bullets = [
        "<b>Acute Offensive Age Cliff:</b> Starting creators and forwards average 35.8 years (Chhetri 40, Noguera 35, Díaz 34, Méndez 34), requiring urgent succession.",
        "<b>Right-Back Structural Void:</b> Roster contains only 1 natural specialist RB (Shivaldo Singh 20), forcing unnatural CB deployments (Rahul Bheke).",
        "<b>Academy Pathway Protection:</b> High-upside domestic assets (Suresh +500%, Roshan +900%, Sivasakthi +700%, Vinith 19) must retain guaranteed match minutes.",
        "<b>Strategic Mandate:</b> Acquire prime-age domestic difference-makers (20–24y) while transitioning foreign slots to athletic physical profiles.",
    ]

    card_left = build_editorial_box(
        "WHAT THE RECRUITMENT HISTORY SAYS",
        "Bengaluru FC operates an opportunistic, contract-efficient recruitment model across five seasons:",
        history_bullets,
        styles,
        width=390,
        is_dark=False
    )
    card_right = build_editorial_box(
        "WHAT THE CURRENT SQUAD SAYS",
        "Recruitment should execute structured succession without suppressing young assets:",
        squad_bullets,
        styles,
        width=390,
        is_dark=True,
        kicker="KEY SQUAD DYNAMICS"
    )

    editorial_row = Table([[card_left, card_right]], colWidths=[393, 393])
    editorial_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(editorial_row)
    story.append(Spacer(1, 6))

    # Bottom: 3 Strategic Takeaways (Finding / Evidence / Implication)
    def make_takeaway_card(num: str, finding: str, evidence: str, impl: str) -> Table:
        data = [
            [Paragraph(f"<b>{num}. FINDING: {finding}</b>", styles["CardTitle"])],
            [Paragraph(f"<b>Evidence:</b> {evidence}", styles["TableCellMuted"])],
            [Paragraph(f"<b>Scouting Implication:</b> {impl}", styles["Body"])],
        ]
        t = Table(data, colWidths=[258])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    t1 = make_takeaway_card("01", "Opportunistic Contract Capture", "50 of 54 external signings free (92.6%); €0 net transfer deficit.", "High wage flexibility under ISL salary cap, but demands elite medical and motivational vetting.")
    t2 = make_takeaway_card("02", "Attacking Succession Cliff", "Starting attacking spine averages 35.8 years, producing 65%+ goal output.", "Proactive multi-window acquisition of U24 striker and creative playmaker is mandatory.")
    t3 = make_takeaway_card("03", "Domestic Value Multiplier", "100% of market value appreciation concentrated in domestic U23 talent.", "Direct capital expenditures into elite domestic youth rather than paying fees for aging foreign stars.")

    takeaways_table = Table([[t1, t2, t3]], colWidths=[262, 262, 262])
    takeaways_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(takeaways_table)
    story.append(Spacer(1, 5))

    # Executive Takeaway Footer Box
    exec_text = (
        "<b>EXECUTIVE TAKEAWAY:</b> Bengaluru FC maintains an exceptionally disciplined, zero-fee acquisition architecture that eliminates balance-sheet risk. "
        "However, this reliance on experienced free agents has produced an acute demographic imbalance in the attacking spine. "
        "The sporting directorate must execute an immediate transition plan: securing a high-pressing domestic U24 striker (David Lalhlansanga) and creative playmaker (Vibin Mohanan) "
        "to sustain championship contention without compromising the developmental minutes of academy talents."
    )
    t_exec = Table([[Paragraph(exec_text, styles["Body"])]], colWidths=[786])
    t_exec.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_exec)
    story.append(PageBreak())
    return story


def build_page_03_recruitment_identity(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 3: Club Recruitment Identity — What Kind of Recruiter is Bengaluru FC?"""
    story = [
        create_header_banner("02. Club Recruitment Identity", "Empirical Evaluation: What Kind of Recruiter is Bengaluru FC?", styles),
        Spacer(1, 6),
    ]

    # Top: 5 Analytical Dimension Cards (Width ~155 each = 775 pt)
    c1 = build_kpi_card("Recruitment Model", "Opportunistic", "Contract Expiry & Swaps", styles, width=153)
    c2 = build_kpi_card("Age Architecture", "Bimodal", "24–26 Prime & 30+ Leaders", styles, width=153)
    c3 = build_kpi_card("Acquisition Deal", "Free Agent (92.6%)", "50/54 External Free", styles, width=153)
    c4 = build_kpi_card("Market Balance", "57.4% Domestic", "ISL Rivals & I-League", styles, width=153)
    c5 = build_kpi_card("Positional Focus", "Defenders (20)", "37.0% of All Inbound", styles, width=153)

    dim_table = Table([[c1, c2, c3, c4, c5]], colWidths=[157] * 5)
    dim_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(dim_table)
    story.append(Spacer(1, 7))

    # 2-Column Deep Dive: What the Data Says vs Scouting Interpretation
    left_data_points = [
        "<b>Zero Transfer Fee Outlay:</b> 50 of 54 external signings arrived on free transfers (92.6%), insulating the club from transfer fee depreciation.",
        "<b>Age Barbell Distribution:</b> Mean signing age of 27.0y conceals heavy polarization—42.6% in 24–26 prime domestic bracket, 31.5% in 30+ foreign bracket, and only 5.6% in 27–29 window.",
        "<b>Defensive Squad Spot Expenditure:</b> Defenders represent 20 of 54 signings (37.0%), reflecting persistent backline restructuring.",
        "<b>Targeted Foreign Quota Usage:</b> Overseas slots are strictly dedicated to central spine positions (CB, CM, CF) from Spain and Australia.",
        "<b>Internal Youth Progression:</b> 5 internal BFC B promotions in 2023/24 reduced average inbound age to 23.6y for that single campaign.",
    ]
    left_card = build_editorial_box(
        "WHAT THE EMPIRICAL DATA SAYS",
        "Rigorous quantification across 106 historical transfer events (2020/21 – 2024/25):",
        left_data_points,
        styles,
        width=390,
        is_dark=False
    )

    right_interpretations = [
        "<b>Salary Cap Capital Efficiency:</b> By avoiding transfer fees, BFC reallocates capital into competitive wages for proven ISL starters (Díaz, Noguera, Bheke).",
        "<b>Eliminating Adaptation Risk:</b> Recruiting proven performers from ISL rivals (Mumbai City, Hyderabad) guarantees immediate tactical readiness.",
        "<b>Spanish Tactical Continuity:</b> A persistent Spanish recruitment pipeline (Roca, Cuadrat, Zaragoza) provides stylistic stability across managerial changes.",
        "<b>The Free-Agent Vulnerability:</b> Heavy reliance on free agency leaves the club vulnerable to bidding wars from corporate-backed rivals (Mohun Bagan SG, Mumbai City).",
        "<b>Strategic Modernization Required:</b> BFC must transition from opportunistic contract capturing to proactive target identification before player contracts expire.",
    ]
    right_card = build_editorial_box(
        "SCOUTING INTERPRETATION & SPORTING LOGIC",
        "Strategic evaluation of why Bengaluru FC operates this recruitment architecture:",
        right_interpretations,
        styles,
        width=390,
        is_dark=True,
        kicker="SPORTING LEADERSHIP ANALYSIS"
    )

    main_grid = Table([[left_card, right_card]], colWidths=[393, 393])
    main_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(main_grid)
    story.append(Spacer(1, 7))

    # Bottom Directive Card
    directive_text = (
        "<b>RECRUITMENT DIRECTIVE:</b> Bengaluru FC's identity as a contract-efficient, pragmatic recruiter provides a strong financial baseline. "
        "However, to compete with top-tier ISL spenders, the club must establish a proactive pre-contract scouting mechanism—identifying and securing "
        "prime domestic talents (ages 21–24) 6 to 12 months prior to contract expiration, rather than participating in reactive summer bidding contests."
    )
    t_dir = Table([[Paragraph(directive_text, styles["Body"])]], colWidths=[786])
    t_dir.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_dir)
    story.append(PageBreak())
    return story


def build_page_04_transfer_history(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 4: Historical Transfer Trends & Movement Volume"""
    story = [
        create_header_banner("03. Historical Transfer Trends & Volume", "Longitudinal Tracking: 106 Transfer Events Across Five ISL Campaigns", styles),
        Spacer(1, 6),
    ]

    chart_path = os.path.join(CHARTS_DIR, "transfers_by_season.png")
    chart_img = Image(chart_path, width=4.9 * inch, height=2.45 * inch) if os.path.exists(chart_path) else Paragraph("Chart Missing", styles["Body"])

    history_table_data = [
        [Paragraph("Season", styles["TableHeader"]), Paragraph("Arr", styles["TableHeader"]), Paragraph("Dep", styles["TableHeader"]), Paragraph("Net", styles["TableHeader"]), Paragraph("Avg Age", styles["TableHeader"]), Paragraph("Key Strategic Shift / Roster Realignment", styles["TableHeader"])],
        [Paragraph("2020/21", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("14", styles["TableCell"]), Paragraph("-2", styles["TableCellBold"]), Paragraph("27.4y", styles["TableCellMuted"]), Paragraph("Transition post-Roca era; extensive defensive rebuilding (Cleiton Silva, Pratik)", styles["TableCell"])],
        [Paragraph("2021/22", styles["TableCellBold"]), Paragraph("10", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("0", styles["TableCellBold"]), Paragraph("26.2y", styles["TableCellMuted"]), Paragraph("Injection of youth; breakthrough emergence of Naorem Roshan & Sivasakthi", styles["TableCell"])],
        [Paragraph("2022/23", styles["TableCellBold"]), Paragraph("12", styles["TableCell"]), Paragraph("10", styles["TableCell"]), Paragraph("+2", styles["TableCellBold"]), Paragraph("28.1y", styles["TableCellMuted"]), Paragraph("Title push with proven ISL winners (Roy Krishna, Javi Hernández, Sandesh)", styles["TableCell"])],
        [Paragraph("2023/24", styles["TableCellBold"]), Paragraph("18", styles["TableCell"]), Paragraph("0", styles["TableCell"]), Paragraph("+18", styles["TableCellBold"]), Paragraph("23.6y", styles["TableCellMuted"]), Paragraph("Youth wave; 5 BFC B promotions (Robin Yadav, Shivaldo, Patre) + Veendorp", styles["TableCell"])],
        [Paragraph("2024/25", styles["TableCellBold"]), Paragraph("7", styles["TableCell"]), Paragraph("13", styles["TableCell"]), Paragraph("-6", styles["TableCellBold"]), Paragraph("28.8y", styles["TableCellMuted"]), Paragraph("Zaragoza Spanish spine: Noguera, Díaz, Méndez, Bheke; veteran restructuring", styles["TableCell"])],
        [Paragraph("Total", styles["TableHeader"]), Paragraph("59", styles["TableHeader"]), Paragraph("47", styles["TableHeader"]), Paragraph("+12", styles["TableHeader"]), Paragraph("27.0y", styles["TableHeader"]), Paragraph("<b>106 Cumulative Events (101 External + 5 Academy Promotions)</b>", styles["TableCellBold"])],
    ]

    t_hist = Table(history_table_data, colWidths=[48, 26, 26, 26, 44, 218])
    t_hist.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -2), COLOR_CARD_BG),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_BFC_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    row_layout = Table([[chart_img, t_hist]], colWidths=[392, 394])
    row_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(row_layout)
    story.append(Spacer(1, 6))

    # 4-Stage Recruitment Cycle Cards
    def make_cycle_card(title: str, years: str, desc: str) -> Table:
        data = [
            [Paragraph(f"<b>{title}</b>", styles["CardTitle"])],
            [Paragraph(years, styles["BadgeSky"])],
            [Paragraph(desc, styles["BodyMuted"])],
        ]
        t = Table(data, colWidths=[192])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    c1 = make_cycle_card("Stage 1: Post-Roca Reset", "2020/21 (26 Events)", "Restructured backline; Cleiton Silva arrived as attacking focal point; high roster turnover.")
    c2 = make_cycle_card("Stage 2: Youth Influx", "2021/22 (20 Events)", "Roshan Singh & Sivasakthi integrated; average age dropped to 26.2y; domestic core solidified.")
    c3 = make_cycle_card("Stage 3: Veteran Push", "2022/23 (22 Events)", "Title push with proven ISL winners (Krishna, Javi); Durand Cup win; reached ISL Final.")
    c4 = make_cycle_card("Stage 4: Zaragoza Rebuild", "2023/24–2024/25 (38 Events)", "Youth promotion wave (5 BFC B promotions) followed by Spanish veteran spine (Noguera, Díaz, Méndez).")

    cycle_table = Table([[c1, c2, c3, c4]], colWidths=[196] * 4)
    cycle_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(cycle_table)
    story.append(Spacer(1, 5))

    # Bottom Observation
    obs_text = (
        "<b>STRATEGIC OBSERVATION:</b> Transfer activity averages 21.2 transactions per completed campaign, reflecting high roster turnover. "
        "Peak turnover occurred in 2020/21 (26) and 2022/23 (22), corresponding to major tactical transitions. "
        "The club has managed zero net negative transfer fee deficits by strictly utilizing free transfers and player contract expirations."
    )
    t_obs = Table([[Paragraph(obs_text, styles["Body"])]], colWidths=[786])
    t_obs.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_obs)
    story.append(PageBreak())
    return story


def build_page_05_recruitment_patterns(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 5: Recruitment Patterns — Three Structured Analytical Modules"""
    story = [
        create_header_banner("04. Recruitment Patterns, Deal Structures & Positional Allocation", "Age Demographics, Deal Structures & Positional Allocation (54 External Signings)", styles),
        Spacer(1, 4),
    ]

    age_chart_path = os.path.join(CHARTS_DIR, "signing_age_distribution.png")
    donut_chart_path = os.path.join(CHARTS_DIR, "transfer_types_donut.png")
    pos_chart_path = os.path.join(CHARTS_DIR, "position_recruitment.png")

    img_age = Image(age_chart_path, width=3.35 * inch, height=1.9 * inch) if os.path.exists(age_chart_path) else Paragraph("Missing Age Chart", styles["Body"])
    img_donut = Image(donut_chart_path, width=3.35 * inch, height=1.9 * inch) if os.path.exists(donut_chart_path) else Paragraph("Missing Donut Chart", styles["Body"])
    img_pos = Image(pos_chart_path, width=3.35 * inch, height=1.9 * inch) if os.path.exists(pos_chart_path) else Paragraph("Missing Position Chart", styles["Body"])

    # Module 1: Age
    box_age = [
        Paragraph("<b>1. WHO DOES BFC SIGN?</b>", styles["CardTitle"]),
        Paragraph("Signing Age Demographics (Mean: 27.0y)", styles["TableCellMuted"]),
        Spacer(1, 2),
        img_age,
        Spacer(1, 2),
        Paragraph("<b>Bimodal Polarization:</b> Signings concentrate in prime domestic talent (24–26y, 42.6%) and veteran leaders (30+y, 31.5%).", styles["TableCell"]),
        Paragraph("<b>The 27–29 Hollow:</b> Only 3 signings (5.6%) in peak-value bracket, avoiding inflated transfer fee markets.", styles["TableCellMuted"]),
        Paragraph("<b>Scouting Implication:</b> Lack of intermediate-age signings leaves younger players without middle-tier mentors.", styles["TableCellBold"]),
    ]

    # Module 2: Deal Types
    box_deal = [
        Paragraph("<b>2. HOW DOES BFC ACQUIRE?</b>", styles["CardTitle"]),
        Paragraph("Transfer Deal Types (92.6% Free Agents)", styles["TableCellMuted"]),
        Spacer(1, 2),
        img_donut,
        Spacer(1, 2),
        Paragraph("<b>Free Transfer Dominance:</b> 50 of 54 external signings arrived on free transfers with €0 net fees.", styles["TableCell"]),
        Paragraph("<b>Loan Insurance:</b> 4 loan events (7.4%) strictly used for short-term injury cover without long-term liabilities.", styles["TableCellMuted"]),
        Paragraph("<b>Scouting Implication:</b> Zero fee amortization maximizes salary cap room, but requires intense medical vetting.", styles["TableCellBold"]),
    ]

    # Module 3: Positional Allocation
    pos_summary_table = Table([
        [Paragraph("Position", styles["TableHeader"]), Paragraph("Signings", styles["TableHeader"]), Paragraph("Share", styles["TableHeader"])],
        [Paragraph("Defender", styles["TableCellBold"]), Paragraph("20", styles["TableCell"]), Paragraph("37.0%", styles["TableCellBold"])],
        [Paragraph("Forward", styles["TableCellBold"]), Paragraph("15", styles["TableCell"]), Paragraph("27.8%", styles["TableCellBold"])],
        [Paragraph("Midfielder", styles["TableCellBold"]), Paragraph("13", styles["TableCell"]), Paragraph("24.1%", styles["TableCellBold"])],
        [Paragraph("Goalkeeper", styles["TableCellBold"]), Paragraph("6", styles["TableCell"]), Paragraph("11.1%", styles["TableCellBold"])],
    ], colWidths=[90, 60, 60])
    pos_summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    box_pos = [
        Paragraph("<b>3. POSITIONS PRIORITIZED</b>", styles["CardTitle"]),
        Paragraph("Positional Focus (Defensive Central Spine)", styles["TableCellMuted"]),
        Spacer(1, 2),
        img_pos,
        Spacer(1, 2),
        pos_summary_table,
        Spacer(1, 2),
        Paragraph("<b>Boundary:</b> 54 External Signings vs 5 Academy Promotions.", styles["TableCellMuted"]),
        Paragraph("<b>Scouting Implication:</b> Heavy defensive recruitment (37.0%) underpins backline stability.", styles["TableCellBold"]),
    ]

    three_col = Table([[box_age, box_deal, box_pos]], colWidths=[260, 260, 266])
    three_col.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(three_col)
    story.append(Spacer(1, 5))

    # Bottom Synthesis Card
    synthesis_text = (
        "<b>RECRUITMENT PATTERN SYNTHESIS:</b> Bengaluru FC's operational model combines opportunistic free-agent captures (92.6%) "
        "with an age barbell strategy (24–26y domestic prime vs 30+ foreign spine). Central defense constitutes the largest single investment of squad slots (37.0%), "
        "ensuring competitive stability. Meanwhile, internal promotions (5 BFC B promotions) provide zero-cost depth without cannibalizing wage cap space."
    )
    t_synth = Table([[Paragraph(synthesis_text, styles["Body"])]], colWidths=[786])
    t_synth.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_synth)
    story.append(PageBreak())
    return story


def build_page_06_recruitment_markets(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 6: Recruitment Markets & Feeder Networks"""
    story = [
        create_header_banner("05. Recruitment Markets & Scouting Footprint", "Where Does Bengaluru FC Find Players? Origin Leagues, Feeder Networks & Geographic Concentration", styles),
        Spacer(1, 5),
    ]

    markets_chart = os.path.join(CHARTS_DIR, "recruitment_markets_combined.png")
    img_markets = Image(markets_chart, width=4.9 * inch, height=2.45 * inch) if os.path.exists(markets_chart) else Paragraph("Missing Markets Chart", styles["Body"])

    market_table_data = [
        [Paragraph("Feeder Club / Origin", styles["TableHeader"]), Paragraph("Country", styles["TableHeader"]), Paragraph("Category", styles["TableHeader"]), Paragraph("Signings", styles["TableHeader"]), Paragraph("Key Players Acquired", styles["TableHeader"])],
        [Paragraph("Mumbai City FC", styles["TableCellBold"]), Paragraph("India", styles["TableCellMuted"]), Paragraph("ISL Rival", styles["TableCell"]), Paragraph("5", styles["TableCellBold"]), Paragraph("Jorge Pereyra Díaz, Alberto Noguera, Rahul Bheke, Sunil Chhetri", styles["TableCellMuted"])],
        [Paragraph("Hyderabad FC", styles["TableCellBold"]), Paragraph("India", styles["TableCellMuted"]), Paragraph("ISL Rival", styles["TableCell"]), Paragraph("3", styles["TableCellBold"]), Paragraph("Chinglensana Singh, Halicharan Narzary, Rohit Kumar", styles["TableCellMuted"])],
        [Paragraph("Indian Arrows", styles["TableCellBold"]), Paragraph("India", styles["TableCellMuted"]), Paragraph("I-League / AIFF", styles["TableCell"]), Paragraph("2", styles["TableCellBold"]), Paragraph("Suresh Singh Wangjam, Akashdeep Singh", styles["TableCellMuted"])],
        [Paragraph("CD Eldense", styles["TableCellBold"]), Paragraph("Spain", styles["TableCellMuted"]), Paragraph("LaLiga 2", styles["TableCell"]), Paragraph("1", styles["TableCellBold"]), Paragraph("Pedro Capó (Zaragoza Spanish connection)", styles["TableCellMuted"])],
        [Paragraph("Perth Glory", styles["TableCellBold"]), Paragraph("Australia", styles["TableCellMuted"]), Paragraph("A-League", styles["TableCell"]), Paragraph("2", styles["TableCellBold"]), Paragraph("Ryan Williams, Aleksandar Jovanović (AFC Quota)", styles["TableCellMuted"])],
        [Paragraph("Club Necaxa", styles["TableCellBold"]), Paragraph("Mexico / Spain", styles["TableCellMuted"]), Paragraph("Liga MX", styles["TableCell"]), Paragraph("1", styles["TableCellBold"]), Paragraph("Édgar Méndez (High-impact attacking forward)", styles["TableCellMuted"])],
    ]

    t_mkt = Table(market_table_data, colWidths=[100, 50, 68, 36, 134])
    t_mkt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    row_layout = Table([[img_markets, t_mkt]], colWidths=[392, 394])
    row_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(row_layout)
    story.append(Spacer(1, 6))

    # 2 Analytical Pipeline Cards
    dom_bullets = [
        "<b>ISL Rival Distress:</b> Capitalizing on financial restructuring at Hyderabad FC and contract expirations at Mumbai City FC.",
        "<b>I-League Talent Incubator:</b> Primary breeding ground for high-upside domestic talent (Indian Arrows, TRAU FC, Aizawl FC).",
        "<b>Internal Reserve Pipeline:</b> BFC B provides cost-free rotational depth (13.2% of all inbound movements across 5 seasons).",
    ]
    for_bullets = [
        "<b>Spain (18.0%):</b> Tactical alignment with head coaches (Cuadrat, Zaragoza); technical tempo controllers and playmakers.",
        "<b>Australia (12.0%):</b> Essential AFC quota channel providing physical resilience, aerial strength, and high-intensity running.",
        "<b>Limited-Sample Signal:</b> Denmark (Drost) and Netherlands (Veendorp) represent emerging pathways requiring live scouting validation.",
    ]

    c_dom = build_editorial_box("DOMESTIC PIPELINE (57.4% - 31 SIGNINGS)", "Core strategy: Proven ISL starters and high-ceiling I-League youth:", dom_bullets, styles, width=390, is_dark=False)
    c_for = build_editorial_box("FOREIGN PIPELINE (42.6% - 23 SIGNINGS)", "Core strategy: Central spine leadership aligned with tactical philosophy:", for_bullets, styles, width=390, is_dark=True, kicker="INTERNATIONAL NETWORK")

    pipe_row = Table([[c_dom, c_for]], colWidths=[393, 393])
    pipe_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(pipe_row)
    story.append(Spacer(1, 5))

    footprint_text = (
        "<b>SCOUTING FOOTPRINT DIRECTIVE:</b> Bengaluru FC should expand its AFC-quota scouting beyond the Australian A-League into Japan's J2 League "
        "and South Korea's K League 2 to identify dynamic, technical forwards with high pressing workrates, while cementing partnerships with North-East I-League academies."
    )
    t_fp = Table([[Paragraph(footprint_text, styles["Body"])]], colWidths=[786])
    t_fp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_fp)
    story.append(PageBreak())
    return story


def build_page_07_player_pathways(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 7: Player Career Pathways — Cerezo Osaka Case Study Layout"""
    story = [
        create_header_banner("06. Player Career Pathways & Trajectories", "Case Studies: Previous Club &rarr; Bengaluru FC &rarr; Destination Club", styles),
        Spacer(1, 5),
    ]

    # 4 Player Pathway Dossier Cards (2x2 Grid)
    def make_pathway_card(name: str, pos_info: str, traj_from: str, bfc_info: str, traj_to: str,
                          story_text: str, badge_text: str, badge_style: ParagraphStyle) -> Table:
        card_data = [
            [
                Paragraph(f"<b>{name}</b>", styles["CardTitleWhite"]),
                Paragraph(badge_text, badge_style),
            ],
            [
                Paragraph(pos_info, styles["TableCellMuted"]),
                "",
            ],
            [
                Paragraph(f"<b>Path:</b> {traj_from} &rarr; <b>BFC ({bfc_info})</b> &rarr; {traj_to}", styles["BodyBold"]),
                "",
            ],
            [
                Paragraph(story_text, styles["Body"]),
                "",
            ],
        ]
        t = Table(card_data, colWidths=[310, 70])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    pw1 = make_pathway_card(
        "Cleiton Silva",
        "Striker · Brazil · Joined Age 33 · 2020–2022",
        "Suphanburi FC (Thai L1)",
        "2.0y | 37 Apps | 16 Goals",
        "East Bengal FC (ISL)",
        "Acquired opportunistically on free agency from Thailand. Served as the primary goalscoring focal point for two campaigns, delivering clinical finishing before transitioning to a league rival as a veteran. High-return 2-year foreign cycle.",
        "2-YEAR PEAK",
        styles["BadgeSky"]
    )

    pw2 = make_pathway_card(
        "Javi Hernández",
        "Attacking Midfielder · Spain · Joined Age 33 · 2022–2024",
        "Odisha FC (ISL)",
        "2.0y | 44 Apps | 13G 9A",
        "Jamshedpur FC (ISL)",
        "Acquired on free transfer; functioned as the primary creative playmaker. Led club to the Durand Cup title and an ISL Final before departing on free transfer at age 35 to refresh the foreign wage bill. Exemplary veteran impact model.",
        "CUP WINNER",
        styles["BadgeSky"]
    )

    pw3 = make_pathway_card(
        "Suresh Singh Wangjam",
        "Central Midfielder · India · Joined Age 18 · 2019–Present",
        "Indian Arrows (I-League)",
        "6.0y+ | 100+ Apps | €50k &rarr; €300k",
        "Active Senior Core (IND)",
        "Identified from AIFF developmental structure; developed through first-team midfield into an indispensable starter and senior national team pillar (+500% valuation growth). Represents the club's highest return on domestic scouting patience.",
        "DOMESTIC CORE",
        styles["BadgeLow"]
    )

    pw4 = make_pathway_card(
        "Naorem Roshan Singh",
        "Left/Right Full-Back · India · Promoted Age 21 · 2020–Present",
        "Bengaluru FC II (2nd Div)",
        "5.0y+ | 70+ Apps | €25k &rarr; €250k",
        "Active Senior Core (IND)",
        "Promoted from the academy reserve team. Transitioned from developmental winger to ISL Emerging Player of the Year as an ambidextrous full-back (+900% valuation growth). Starting national team full-back, proving the internal academy model.",
        "ACADEMY ELITE",
        styles["BadgeLow"]
    )

    grid_pw = Table([[pw1, pw2], [pw3, pw4]], colWidths=[392, 392])
    grid_pw.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(grid_pw)
    story.append(Spacer(1, 6))

    # Bottom: External vs Academy Structural Contrast
    ext_story = (
        "<b>EXTERNAL RECRUITMENT PATHWAY DYNAMICS (2-YEAR CYCLE):</b> "
        "Foreign veteran signings deliver immediate competitive performance over 24-month cycles before contract expiration and wage recycling (e.g. Cleiton Silva, Javi Hernández, Alan Costa). "
        "They carry zero residual transfer fee value upon exit, functioning as amortized competitive tools rather than economic investments."
    )
    acad_story = (
        "<b>INTERNAL ACADEMY PROMOTION PATHWAY DYNAMICS (5-YEAR MULTIPLIER):</b> "
        "Internal development (5 BFC B promotions in 2023/24; Suresh, Roshan, Sivasakthi) drives 100% of the club's asset appreciation. "
        "Young domestic talents appreciate exponentially in valuation and provide long-term dressing room continuity across managerial transitions."
    )

    c_ext = Table([[Paragraph(ext_story, styles["Body"])]], colWidths=[390])
    c_ext.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))

    c_acad = Table([[Paragraph(acad_story, styles["Body"])]], colWidths=[390])
    c_acad.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))

    story_row = Table([[c_ext, c_acad]], colWidths=[393, 393])
    story_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(story_row)
    story.append(PageBreak())
    return story


def build_page_08_market_value(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 8: Player Market Value Analysis & Economic Trajectory"""
    story = [
        create_header_banner("07. Market Value & Player Development", "Economic Trajectory, Portfolio Growth & Financial Asset Appreciation", styles),
        Spacer(1, 4),
    ]

    # Data Integrity Principle Banner
    rule_text = (
        "<b>DATA INTEGRITY PRINCIPLE: MARKET VALUE &ne; TRANSFER FEE.</b> "
        "Transfer Fee is the actual cash price paid between clubs (Bengaluru FC paid €0 in net fees across 92.6% of external arrivals). "
        "Market Value represents an objective economic asset valuation based on player age, contract length, form, league tier, and international caps. "
        "Asset Appreciation Formula: <b>((Current Value - Initial Value) / Initial Value) &times; 100</b>."
    )
    t_rule = Table([[Paragraph(rule_text, styles["Body"])]], colWidths=[786])
    t_rule.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_rule)
    story.append(Spacer(1, 5))

    chart_mv = os.path.join(CHARTS_DIR, "market_value_growth.png")
    img_mv = Image(chart_mv, width=4.9 * inch, height=2.4 * inch) if os.path.exists(chart_mv) else Paragraph("Missing MV Chart", styles["Body"])

    mv_table_data = [
        [Paragraph("Player Name", styles["TableHeader"]), Paragraph("Joined", styles["TableHeader"]), Paragraph("Peak", styles["TableHeader"]), Paragraph("Current", styles["TableHeader"]), Paragraph("Growth %", styles["TableHeader"]), Paragraph("Economic Value Category", styles["TableHeader"])],
        [Paragraph("Naorem Roshan Singh", styles["TableCellBold"]), Paragraph("€25k", styles["TableCellMuted"]), Paragraph("€275k", styles["TableCell"]), Paragraph("€250k", styles["TableCellBold"]), Paragraph("+900.0%", styles["BadgeLow"]), Paragraph("Elite Academy Asset Appreciation", styles["TableCell"])],
        [Paragraph("Udanta Singh", styles["TableCellBold"]), Paragraph("€25k", styles["TableCellMuted"]), Paragraph("€325k", styles["TableCell"]), Paragraph("€225k", styles["TableCellBold"]), Paragraph("+800.0%", styles["BadgeLow"]), Paragraph("Full-Cycle Homegrown Development", styles["TableCell"])],
        [Paragraph("Sivasakthi Narayanan", styles["TableCellBold"]), Paragraph("€25k", styles["TableCellMuted"]), Paragraph("€200k", styles["TableCell"]), Paragraph("€200k", styles["TableCellBold"]), Paragraph("+700.0%", styles["BadgeLow"]), Paragraph("Emerging Domestic Forward Asset", styles["TableCell"])],
        [Paragraph("Suresh Singh Wangjam", styles["TableCellBold"]), Paragraph("€50k", styles["TableCellMuted"]), Paragraph("€300k", styles["TableCell"]), Paragraph("€300k", styles["TableCellBold"]), Paragraph("+500.0%", styles["BadgeLow"]), Paragraph("Spine Foundation Anchor", styles["TableCell"])],
        [Paragraph("Ashique Kuruniyan", styles["TableCellBold"]), Paragraph("€100k", styles["TableCellMuted"]), Paragraph("€300k", styles["TableCell"]), Paragraph("€300k", styles["TableCellBold"]), Paragraph("+200.0%", styles["BadgeLow"]), Paragraph("Prime Domestic Asset Expansion", styles["TableCell"])],
        [Paragraph("Cleiton Silva", styles["TableCellBold"]), Paragraph("€350k", styles["TableCellMuted"]), Paragraph("€350k", styles["TableCell"]), Paragraph("€100k", styles["TableCellBold"]), Paragraph("-71.4%", styles["BadgeHigh"]), Paragraph("Age Depreciation Curve (37y)", styles["TableCell"])],
        [Paragraph("Sunil Chhetri", styles["TableCellBold"]), Paragraph("€175k", styles["TableCellMuted"]), Paragraph("€175k", styles["TableCell"]), Paragraph("€50k", styles["TableCellBold"]), Paragraph("-71.4%", styles["BadgeHigh"]), Paragraph("Veteran Career Climax (40y)", styles["TableCell"])],
    ]

    t_mv = Table(mv_table_data, colWidths=[96, 38, 38, 38, 48, 134])
    t_mv.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    row_layout = Table([[img_mv, t_mv]], colWidths=[392, 394])
    row_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(row_layout)
    story.append(Spacer(1, 5))

    # Bottom: Value Story & Recruitment Lesson
    val_story = (
        "<b>THE VALUE STORY:</b> Value appreciation within Bengaluru FC is almost exclusively an internal and domestic phenomenon. "
        "Inbound domestic U22 talents appreciate by an average of +580% through systematic match minutes, while foreign signings experience steep natural "
        "age-curve depreciation (-20% to -71%) as they are recruited in their late twenties or thirties for immediate championship contribution."
    )
    rec_lesson = (
        "<b>THE RECRUITMENT LESSON:</b> Foreign signings must be evaluated purely as amortized competitive tools (points, trophies, leadership) "
        "with zero residual financial recovery expectations. Long-term club valuation equity must be driven entirely by domestic scouting and academy graduations."
    )

    c_val = Table([[Paragraph(val_story, styles["Body"])]], colWidths=[390])
    c_val.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))

    c_rec = Table([[Paragraph(rec_lesson, styles["Body"])]], colWidths=[390])
    c_rec.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))

    story_row = Table([[c_val, c_rec]], colWidths=[393, 393])
    story_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(story_row)
    story.append(PageBreak())
    return story


def build_page_09_current_squad(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 9: Current Squad Analysis — Cerezo Osaka Internal Assets Layout (8 Player Cards)"""
    story = [
        create_header_banner("08. Current Squad Analysis (2024/25 Season)", "Roster Hierarchy, Role Classification & Key Internal Assets (24 Senior Players)", styles),
        Spacer(1, 4),
    ]

    # Top KPI Strip
    kpi_strip = Table([
        [
            Paragraph("<b>Senior Squad Size:</b> 24 Players", styles["TableCellBold"]),
            Paragraph("<b>Average Squad Age:</b> 27.3 Years", styles["TableCellBold"]),
            Paragraph("<b>Active Foreign Slots:</b> 6 Players", styles["TableCellBold"]),
            Paragraph("<b>Academy Graduates:</b> 8 Players (33.3%)", styles["TableCellBold"]),
        ]
    ], colWidths=[196] * 4)
    kpi_strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_strip)
    story.append(Spacer(1, 4))

    # 8 Player Cards in 2x4 Grid (Cerezo Image 3 pattern)
    def make_squad_player_card(initials: str, name: str, badge: str, badge_style: ParagraphStyle,
                               meta: str, qual_profile: str, why_fits: str) -> Table:
        avatar_box = Table(
            [
                [Paragraph(f"<b>{initials}</b>", styles["CardTitleWhite"])],
            ],
            colWidths=[36],
            rowHeights=[36]
        )
        avatar_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_BFC_NAVY),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BFC_BLUE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        info_rows = [
            [Paragraph(f"<b>{name}</b>", styles["CardTitleWhite"]), Paragraph(badge, badge_style)],
            [Paragraph(meta, styles["TableCellMuted"]), ""],
            [Paragraph(qual_profile, styles["TableCell"]), ""],
            [Paragraph(f"<i>{why_fits}</i>", styles["TableCellMuted"]), ""],
        ]
        info_table = Table(info_rows, colWidths=[262, 80])
        info_table.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        card_table = Table([[avatar_box, info_table]], colWidths=[40, 346])
        card_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return card_table

    p1 = make_squad_player_card("GSS", "Gurpreet Singh Sandhu", "KEY | VETERAN", styles["BadgeSky"], "GK · 32y · IND · €200k · Joined 2017", "International shot-stopper with unmatched aerial reach and command of penalty area.", "Uncontested domestic No. 1 providing 8-season dressing room stability.")
    p2 = make_squad_player_card("SC", "Sunil Chhetri", "REPLACEMENT RISK", styles["BadgeHigh"], "ST · 40y · IND · €50k · Joined 2017", "Iconic national goalscorer with elite movement in box, clutch penalties, and leadership.", "Entering career climax; requires urgent phased succession plan.")
    p3 = make_squad_player_card("SSW", "Suresh Singh Wangjam", "KEY | HIGH UPSIDE", styles["BadgeLow"], "CM · 24y · IND · €300k · Joined 2019", "Dynamic double-pivot ball-winner with relentless pressing stamina and progressive carry.", "Foundational midfield anchor in prime athletic years; highest-value domestic asset.")
    p4 = make_squad_player_card("NRS", "Naorem Roshan Singh", "CORE | HIGH UPSIDE", styles["BadgeLow"], "LB · 25y · IND · €250k · Academy 2020", "Ambidextrous full-back with world-class crossing, dead-ball delivery, and recovery pace.", "Primary creator from wide areas; essential to defensive-to-offensive transitions.")
    p5 = make_squad_player_card("AN", "Alberto Noguera", "REPLACEMENT RISK", styles["BadgeHigh"], "AM · 35y · ESP · €250k · Joined 2024", "Supreme Spanish playmaker with exceptional scanning, line-breaking vision, and poise.", "Brain of Zaragoza's attacking system; age 35 creates high creative succession risk.")
    p6 = make_squad_player_card("JPD", "Jorge Pereyra Díaz", "VETERAN FOREIGN", styles["BadgeSky"], "ST · 34y · ARG · €350k · Joined 2024", "Combative forward combining aggressive pressing, channel running, and clinical finishing.", "Proven ISL winner giving immediate thrust; short-term 1-2 season horizon.")
    p7 = make_squad_player_card("RB", "Rahul Bheke", "CORE | VETERAN", styles["BadgeMedium"], "CB/RB · 33y · IND · €175k · Joined 2024", "Versatile defender with high aerial duel prowess, box clearances, and emergency RB cover.", "Veteran leader offering backline versatility; bridge between old and new core.")
    p8 = make_squad_player_card("VV", "Vinith Venkatesh", "DEVELOPMENT", styles["BadgeLow"], "AM · 19y · IND · €100k · Academy 2024", "Fearless academy playmaker with inventive dribbling, half-space mobility, and debut goal.", "Heir-apparent in creative midfield; requires guaranteed 15+ starts to mature.")

    squad_grid = Table([[p1, p2], [p3, p4], [p5, p6], [p7, p8]], colWidths=[392, 392])
    squad_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(squad_grid)
    story.append(Spacer(1, 4))

    # Bottom: Current Squad Read
    squad_read_text = (
        "<b>CURRENT SQUAD READ:</b> The 2024/25 roster is a polarized two-speed squad: an elite domestic youth platform (Suresh 24, Roshan 25, Sivasakthi 23, Vinith 19) "
        "coexists with an ultra-veteran match-winning spine (Chhetri 40, Noguera 35, Díaz 34, Jovanović 35, Bheke 33). "
        "While the squad averages 27.3 years overall, the senior core that generates over 65% of attacking output averages 35.8 years. Succession planning is urgent."
    )
    t_sq_read = Table([[Paragraph(squad_read_text, styles["Body"])]], colWidths=[786])
    t_sq_read.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sq_read)
    story.append(PageBreak())
    return story


def build_page_10_squad_age_depth(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 10: Squad Age & Positional Depth"""
    story = [
        create_header_banner("09. Squad Age Structure & Positional Depth", "Positional Depth Curves, Demographic Imbalances & Succession Windows", styles),
        Spacer(1, 5),
    ]

    chart_depth = os.path.join(CHARTS_DIR, "squad_depth_age_matrix.png")

    c1 = build_kpi_card("Average Squad Age", "27.3y", "Balanced Overall Mean", styles, width=153)
    c2 = build_kpi_card("Oldest Position", "DM (33.0y)", "Pedro Capó (33 Anchor)", styles, width=153)
    c3 = build_kpi_card("Youngest Position", "RB (20.0y)", "Shivaldo Singh (Solo RB)", styles, width=153)
    c4 = build_kpi_card("Strongest Depth", "CB (5 Players)", "Deep Domestic & Asian Spine", styles, width=153)
    c5 = build_kpi_card("Weakest Depth", "RB (1 Player)", "Urgent Specialist Need", styles, width=153)

    card_row = Table([[c1, c2, c3, c4, c5]], colWidths=[157] * 5)
    card_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(card_row)
    story.append(Spacer(1, 6))

    img_depth = Image(chart_depth, width=4.9 * inch, height=2.45 * inch) if os.path.exists(chart_depth) else Paragraph("Missing Depth Chart", styles["Body"])

    pos_risk_data = [
        [Paragraph("Position", styles["TableHeader"]), Paragraph("Count", styles["TableHeader"]), Paragraph("Avg Age", styles["TableHeader"]), Paragraph("Risk Level", styles["TableHeader"]), Paragraph("Tactical Implication & Urgency", styles["TableHeader"])],
        [Paragraph("Striker / CF", styles["TableCellBold"]), Paragraph("4", styles["TableCell"]), Paragraph("32.3y", styles["TableCell"]), Paragraph("HIGH", styles["BadgeHigh"]), Paragraph("Chhetri (40) & Díaz (34) lead attack; urgent U24 succession required", styles["TableCell"])],
        [Paragraph("Attacking MF", styles["TableCellBold"]), Paragraph("2", styles["TableCell"]), Paragraph("29.7y", styles["TableCell"]), Paragraph("HIGH", styles["BadgeHigh"]), Paragraph("Noguera (35) sole proven creator; need prime-age playmaker backup", styles["TableCell"])],
        [Paragraph("Right Back", styles["TableCellBold"]), Paragraph("1", styles["TableCell"]), Paragraph("20.0y", styles["TableCell"]), Paragraph("HIGH", styles["BadgeHigh"]), Paragraph("Shivaldo (20) only specialist RB; Bheke deployed out of position", styles["TableCell"])],
        [Paragraph("Centre Back", styles["TableCellBold"]), Paragraph("5", styles["TableCell"]), Paragraph("30.6y", styles["TableCell"]), Paragraph("MEDIUM", styles["BadgeMedium"]), Paragraph("Seasoned starters (Jovanović 35, Bheke 33) carry recovery-pace risk", styles["TableCell"])],
        [Paragraph("Goalkeeper", styles["TableCellBold"]), Paragraph("3", styles["TableCell"]), Paragraph("27.7y", styles["TableCell"]), Paragraph("LOW", styles["BadgeLow"]), Paragraph("Gurpreet (32) dependable; Sahil Poonia (18) developing in reserve", styles["TableCell"])],
    ]
    t_pos_risk = Table(pos_risk_data, colWidths=[70, 26, 38, 48, 206])
    t_pos_risk.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    mid_layout = Table([[img_depth, t_pos_risk]], colWidths=[392, 394])
    mid_layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(mid_layout)
    story.append(Spacer(1, 6))

    # Bottom 3 Pressure Pillars
    def make_pressure_card(title: str, subtitle: str, body: str) -> Table:
        data = [
            [Paragraph(f"<b>{title}</b>", styles["CardTitle"])],
            [Paragraph(subtitle, styles["BadgeSky"])],
            [Paragraph(body, styles["BodyMuted"])],
        ]
        t = Table(data, colWidths=[258])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    p_age = make_pressure_card("1. AGE PRESSURE", "Attacking Spine: 35.8y Avg", "Extreme physical vulnerability in match-winners requires planned minutes management and load regulation.")
    p_dep = make_pressure_card("2. DEPTH PRESSURE", "Right-Back Structural Void", "Lack of specialist RB forces CBs out of position, distorting defensive shape and flank progression.")
    p_suc = make_pressure_card("3. SUCCESSION PRESSURE", "Imminent Senior Succession", "Multiple concurrent contract expirations necessitate phased pre-contract recruitment across two windows.")

    press_row = Table([[p_age, p_dep, p_suc]], colWidths=[262, 262, 262])
    press_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(press_row)
    story.append(PageBreak())
    return story


def build_page_11_six_key_conclusions(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 11: Six Key Conclusions — Cerezo Osaka 6-Card Executive Layout"""
    story = [
        create_header_banner("10. Six Key Conclusions from the Full Sample", "Executive Summary of Empirical Recruitment Analytics & Strategic Findings", styles),
        Spacer(1, 6),
    ]

    conclusions = get_six_key_conclusions()

    def make_conclusion_card(num: str, title: str, finding: str, metric: str, impl: str) -> Table:
        data = [
            [
                Paragraph(num, styles["ConclusionNum"]),
                Paragraph(f"<b>{title}</b>", styles["ConclusionTitle"]),
            ],
            [
                "",
                Paragraph(f"<b>Data Point:</b> {metric}", styles["TableCellMuted"]),
            ],
            [
                "",
                Paragraph(f"<b>What It Means:</b> {finding}", styles["TableCell"]),
            ],
            [
                "",
                Paragraph(f"<b>Scouting Consequence:</b> {impl}", styles["BodyBold"]),
            ],
        ]
        t = Table(data, colWidths=[32, 350])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (0, 3)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("LINEBELOW", (1, 0), (1, 0), 0.75, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    c1 = make_conclusion_card("01", "Opportunistic Free-Agent Model", "Maximizes wage flexibility under salary cap; zero fee deficit.", "92.6% of external arrivals (50/54) acquired on free transfers; 0 transfer fee debt.", "Requires elite medical, physical, and psychological vetting to avoid declining wage-burdens.")
    c2 = make_conclusion_card("02", "Bimodal Recruitment Demographics", "Bifurcated into domestic prime (24–26y) and foreign leaders (30+y).", "27.0y mean signing age; 42.6% in 24–26 band, 31.5% in 30+ bracket, 5.6% in 27–29 window.", "Creates an age barbell; leaves younger players without intermediate-age mentors.")
    c3 = make_conclusion_card("03", "Attacking Spine Succession Cliff", "Primary match-winners and creators are in late career twilight.", "Starting attackers average 35.8 years (Chhetri 40, Noguera 35, Díaz 34, Méndez 34).", "Next two transfer windows must be dominated by U25 attacking acquisitions.")
    c4 = make_conclusion_card("04", "Domestic Youth Value Multiplier", "Economic appreciation is strictly concentrated in domestic U23 signings.", "Roshan (+900%), Udanta (+800%), Sivasakthi (+700%), and Suresh (+500%) drive 100% of value growth.", "Concentrate transfer expenditures on elite domestic youth rather than aging foreign stars.")
    c5 = make_conclusion_card("05", "Right-Back Structural Vulnerability", "Only 1 specialist right-back on roster, forcing CBs out of position.", "Shivaldo Singh (20) sole natural RB; Rahul Bheke deployed out of position on right flank.", "Immediate recruitment of an athletic, dynamic right-back is essential to balance Zaragoza's back four.")
    c6 = make_conclusion_card("06", "Complement the Core, Protect Academy Minutes", "5 BFC B promotions in 2023/24; Vinith (19) and Sivasakthi (23) proven ISL scorers.", "Recruitment must not block the development pathways of top homegrown assets.", "Target complementary profile starters, not squad-filler stopgaps that block young talent.")

    row1 = [c1, c2]
    row2 = [c3, c4]
    row3 = [c5, c6]

    grid = Table([row1, [Spacer(1, 4), Spacer(1, 4)], row2, [Spacer(1, 4), Spacer(1, 4)], row3], colWidths=[392, 392])
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
    """Page 12: Squad Gaps & Strategic Risk Register"""
    story = [
        create_header_banner("11. Squad Gaps & Strategic Risk Register", "Automated Detection of Positional Voids, Age Risks & Succession Imperatives", styles),
        Spacer(1, 5),
    ]

    gaps_data = [
        [Paragraph("Priority", styles["TableHeader"]), Paragraph("Position", styles["TableHeader"]), Paragraph("Depth / Age", styles["TableHeader"]), Paragraph("Current Situation & Core Strategic Risk", styles["TableHeader"]), Paragraph("Why It Matters (Impact)", styles["TableHeader"]), Paragraph("Actionable Recruitment Response", styles["TableHeader"])],
        [
            Paragraph("HIGH", styles["BadgeHigh"]),
            Paragraph("Striker / CF", styles["TableCellBold"]),
            Paragraph("4 / 32.3y", styles["TableCell"]),
            Paragraph("Chhetri (40) & Díaz (34) lead attack; Sivasakthi (23) needs prime-age partner.", styles["TableCell"]),
            Paragraph("Imminent retirement cliff; loss of 65% of team goal contribution.", styles["TableCellMuted"]),
            Paragraph("Recruit dynamic, high-pressing domestic U24 striker (David Lalhlansanga / Irfan Yadwad).", styles["TableCellBold"]),
        ],
        [
            Paragraph("HIGH", styles["BadgeHigh"]),
            Paragraph("Attacking MF", styles["TableCellBold"]),
            Paragraph("2 / 29.7y", styles["TableCell"]),
            Paragraph("Noguera (35) sole proven creator; Vinith (19) requires progressive adaptation.", styles["TableCell"]),
            Paragraph("Extreme xG drop when Noguera is absent; lack of prime playmaker.", styles["TableCellMuted"]),
            Paragraph("Target prime-age creative midfielder (Age 22–26, Vibin Mohanan) with elite progressive passing.", styles["TableCellBold"]),
        ],
        [
            Paragraph("HIGH", styles["BadgeHigh"]),
            Paragraph("Right Back", styles["TableCellBold"]),
            Paragraph("1 / 20.0y", styles["TableCell"]),
            Paragraph("Shivaldo Singh (20) sole natural RB; Bheke deployed out of position on flank.", styles["TableCell"]),
            Paragraph("Asymmetric attacking shape; defensive isolation on wide counters.", styles["TableCellMuted"]),
            Paragraph("Sign starting-caliber dynamic right-back (Aakash Sangwan / Jay Gupta cover).", styles["TableCellBold"]),
        ],
        [
            Paragraph("MEDIUM", styles["BadgeMedium"]),
            Paragraph("Ball-Playing CB", styles["TableCellBold"]),
            Paragraph("5 / 30.6y", styles["TableCell"]),
            Paragraph("Jovanović (35) & Bheke (33) aging; Sana Singh (27) prime domestic anchor.", styles["TableCell"]),
            Paragraph("Backline vulnerability against rapid transitional counter-attacks.", styles["TableCellMuted"]),
            Paragraph("Acquire athletic U26 left-footed CB (domestic or Asian AFC quota).", styles["TableCellBold"]),
        ],
        [
            Paragraph("LOW", styles["BadgeLow"]),
            Paragraph("U23 Goalkeeper", styles["TableCellBold"]),
            Paragraph("3 / 27.7y", styles["TableCell"]),
            Paragraph("Gurpreet (32) elite starter; Ralte (31) backup; Sahil Poonia (18) developing.", styles["TableCell"]),
            Paragraph("Need long-term succession plan for India's No. 1 goalkeeper.", styles["TableCellMuted"]),
            Paragraph("Maintain systematic cup starts for Sahil Poonia; monitor U23 domestic keepers.", styles["TableCellBold"]),
        ],
        [
            Paragraph("LOW", styles["BadgeLow"]),
            Paragraph("Central Midfield", styles["TableCellBold"]),
            Paragraph("4 / 26.5y", styles["TableCell"]),
            Paragraph("Suresh (24) prime anchor; Capó (33) veteran; Fanai (20) rotational depth.", styles["TableCell"]),
            Paragraph("Over-recruiting midfield risks blocking minutes for academy youth.", styles["TableCellMuted"]),
            Paragraph("Enforce rotational minutes protocol; avoid stopgap veteran midfield signings.", styles["TableCellBold"]),
        ],
    ]

    t_gaps = Table(gaps_data, colWidths=[46, 74, 52, 210, 194, 210])
    t_gaps.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_gaps)
    story.append(Spacer(1, 6))

    # Bottom Risk Governance Card
    gov_text = (
        "<b>RISK GOVERNANCE & ACTION TRIGGERS:</b> "
        "<b>1. Availability Threshold:</b> Any starter aged 34+ logging <70% availability triggers immediate pre-contract execution for replacement. "
        "<b>2. Squad Youth Quota:</b> Minimum 4 U23 domestic players must log >800 minutes per campaign to sustain value appreciation. "
        "<b>3. Right-Back Priority:</b> The absence of an established right-back represents the single largest structural vulnerability in the current squad."
    )
    t_gov = Table([[Paragraph(gov_text, styles["Body"])]], colWidths=[786])
    t_gov.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_gov)
    story.append(PageBreak())
    return story


def build_page_13_recruitment_profiles(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 13: Ideal Recruitment Profiles — Suggested Profiles to Complement the Squad"""
    story = [
        create_header_banner("12. Gap-Driven Ideal Recruitment Profiles", "Suggested Profiles to Complement the Squad: Objective Scouting Archetypes", styles),
        Spacer(1, 5),
    ]

    profiles = get_ideal_recruitment_profiles()

    def make_profile_card(p: Dict[str, Any]) -> Table:
        badge_style = styles["BadgeHigh"] if p["priority"] == "High" else (styles["BadgeMedium"] if p["priority"] == "Medium" else styles["BadgeLow"])
        attrs = ", ".join(p["required_attributes"])
        data = [
            [Paragraph(f"<b>{p['profile_name'].upper()}</b>", styles["CardTitleWhite"]), Paragraph(f"PRIORITY: {p['priority'].upper()}", badge_style)],
            [Paragraph(f"<b>Gap Addressed:</b> {p['gap_addressed']}", styles["TableCellMuted"]), ""],
            [Paragraph(f"<b>Target Age:</b> {p['age_range']}  |  <b>Foot:</b> {p['preferred_foot']}  |  <b>Market Value:</b> {p['market_value_range']}", styles["TableCell"]), ""],
            [Paragraph(f"<b>Tactical Role:</b> {p['experience_level']}", styles["TableCellMuted"]), ""],
            [Paragraph(f"<b>Core Required Attributes:</b> {attrs}", styles["TableCellBold"]), ""],
        ]
        t = Table(data, colWidths=[130, 60])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("SPAN", (0, 4), (1, 4)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    p1 = make_profile_card(profiles[0])
    p2 = make_profile_card(profiles[1])
    p3 = make_profile_card(profiles[2])
    p4 = make_profile_card(profiles[3])

    profiles_row = Table([[p1, p2, p3, p4]], colWidths=[196] * 4)
    profiles_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(profiles_row)
    story.append(Spacer(1, 6))

    # Middle: Scouting Shortlist Overview Box (Cerezo Image 5 pattern)
    shortlist_box_data = [
        [Paragraph("<b>SCOUTING SHORTLIST OVERVIEW (CANDIDATES MAPPED TO ROLES)</b>", styles["CardTitle"])],
        [Paragraph("Initial shortlist of players who fit the priority roles. Selected profiles are explored in detail in the following section.", styles["TableCellMuted"])],
        [Spacer(1, 2)],
        [Paragraph("<b>Dynamic Striker / Centre-Forward:</b> David Lalhlansanga (East Bengal) &bull; Irfan Yadwad (Chennaiyin FC) &bull; Parthib Gogoi (NorthEast United)", styles["Body"])],
        [Paragraph("<b>Creative Interior Midfielder (No. 8/10):</b> Vibin Mohanan (Kerala Blasters) &bull; Brison Fernandes (FC Goa) &bull; Ayush Adhikari (Chennaiyin FC)", styles["Body"])],
        [Paragraph("<b>Ball-Playing Centre Back:</b> Bikash Yumnam (Kerala Blasters) &bull; Hormipam Ruivah (Kerala Blasters) &bull; Asian Quota Target (A-League / J2)", styles["Body"])],
        [Paragraph("<b>Attacking Dynamic Full-Back:</b> Aakash Sangwan (FC Goa) &bull; Jay Gupta (FC Goa) &bull; Amey Ranawade (Odisha FC)", styles["Body"])],
    ]
    t_sl_box = Table(shortlist_box_data, colWidths=[786])
    t_sl_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER_SUBTLE),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sl_box)
    story.append(Spacer(1, 5))

    # Bottom Methodological Note
    meth_text = (
        "<b>METHODOLOGICAL INTEGRITY NOTE:</b> Ideal recruitment profiles are generated strictly from empirical squad deficits, "
        "not ad-hoc scouting preference. Candidates shortlisted on subsequent pages must satisfy at least 80% of these structural attributes "
        "to advance to live video and live match scouting validation."
    )
    t_meth = Table([[Paragraph(meth_text, styles["Body"])]], colWidths=[786])
    t_meth.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_ALT),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meth)
    story.append(PageBreak())
    return story


def build_page_14_player_shortlist(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 14: Player Shortlist & 100-Point Fit Scoring — Cerezo Osaka Priority Profiles"""
    story = [
        create_header_banner("13. Player Shortlist & 100-Point Fit Scoring", "Concrete Targets Assessed Against Tactical Fit, Market Valuation & Development Ceiling", styles),
        Spacer(1, 4),
    ]

    radar_chart = os.path.join(CHARTS_DIR, "shortlist_radar.png")
    img_radar = Image(radar_chart, width=3.4 * inch, height=2.45 * inch) if os.path.exists(radar_chart) else Paragraph("Missing Radar Chart", styles["Body"])

    shortlist = get_shortlisted_players()

    def make_target_dossier(p: Dict[str, Any]) -> Table:
        strengths = ", ".join(p["strengths"])
        dossier_data = [
            [
                Paragraph(f"<b>{p['target_profile']}: {p['name']}</b>", styles["CardTitleWhite"]),
                Paragraph(f"FIT SCORE: <b>{p['fit_score']}/100</b>", styles["BadgeLow"]),
            ],
            [
                Paragraph(f"<b>Club:</b> {p['club']}  |  <b>Age:</b> {p['age']}y  |  <b>Nat:</b> {p['nationality']}  |  <b>Val:</b> {p['market_value']}  |  <b>Foot:</b> {p['preferred_foot']}", styles["TableCellMuted"]),
                "",
            ],
            [
                Paragraph(f"<b>Qualitative Profile:</b> {p['playing_style']}", styles["TableCell"]),
                "",
            ],
            [
                Paragraph(f"<b>Why He Fits BFC:</b> {p['why_fits']}", styles["TableCellBold"]),
                "",
            ],
            [
                Paragraph(f"<b>Strengths:</b> {strengths}  |  <b>Watchout:</b> {p['risks']}", styles["TableCellMuted"]),
                "",
            ],
        ]
        t = Table(dossier_data, colWidths=[330, 80])
        t.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (0, 2), (1, 2)),
            ("SPAN", (0, 3), (1, 3)),
            ("SPAN", (0, 4), (1, 4)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    dossier1 = make_target_dossier(shortlist[0])  # David Lalhlansanga
    dossier2 = make_target_dossier(shortlist[1])  # Vibin Mohanan
    dossier3 = make_target_dossier(shortlist[2])  # Muhammed Sanan

    right_stack = Table([[dossier1], [Spacer(1, 3)], [dossier2], [Spacer(1, 3)], [dossier3]], colWidths=[415])
    right_stack.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    radar_summary_box = [
        img_radar,
        Spacer(1, 3),
        Paragraph("<b>100-PT WEIGHTED FIT CRITERIA:</b>", styles["CardTitle"]),
        Paragraph("&bull; Age Fit (20%) &bull; Positional Fit (20%) &bull; Performance Fit (20%)", styles["TableCellMuted"]),
        Paragraph("&bull; Playing Style Fit (15%) &bull; Market Value Fit (15%) &bull; Upside (10%)", styles["TableCellMuted"]),
        Spacer(1, 2),
        Paragraph("<b>Heuristic Disclaimer:</b> Fit scores (92.4, 92.0, 90.2) are heuristic multi-criteria scouting valuations based on age, positional fit, and tactical style—NOT match-event data ratings.", styles["TableCellBold"]),
    ]
    t_radar_box = Table([[item] for item in radar_summary_box], colWidths=[365])
    t_radar_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    layout = Table([[t_radar_box, right_stack]], colWidths=[370, 416])
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(layout)
    story.append(PageBreak())
    return story


def build_page_15_final_strategy(styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Page 15: Final Recruitment Strategy & Action Plan — 4-Pillar Roadmap"""
    story = [
        create_header_banner("14. Final Recruitment Strategy & Action Plan", "The 4-Pillar Strategic Squad Roadmap: Retain, Develop, Replace, Recruit", styles),
        Spacer(1, 5),
    ]

    strategy = get_final_recruitment_strategy()

    def make_pillar_card(pillar_name: str, items: List[str], header_color: colors.HexColor, subtitle: str) -> Table:
        rows = [
            [Paragraph(pillar_name.upper(), styles["CardTitleWhite"])],
            [Paragraph(subtitle, styles["TableCellMuted"])],
            [Spacer(1, 2)],
        ]
        for it in items:
            rows.append([Paragraph(f"&bull; {it}", styles["Body"])])

        t = Table(rows, colWidths=[192])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    p1 = make_pillar_card("RETAIN (Core Assets)", strategy["RETAIN"], COLOR_BFC_BLUE, "Protect prime domestic spine:")
    p2 = make_pillar_card("DEVELOP (Academy)", strategy["DEVELOP"], colors.HexColor("#0284C7"), "Guarantee first-team minutes:")
    p3 = make_pillar_card("REPLACE (Veterans)", strategy["REPLACE"], COLOR_BFC_RED, "Manage contract transitions:")
    p4 = make_pillar_card("RECRUIT (Gaps)", strategy["RECRUIT"], COLOR_SUCCESS, "Execute priority acquisitions:")

    pillars_table = Table([[p1, p2, p3, p4]], colWidths=[196] * 4)
    pillars_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(pillars_table)
    story.append(Spacer(1, 6))

    # Middle: Three-Window Timeline Box
    timeline_data = [
        [Paragraph("<b>STRATEGIC TRANSFER TIMELINE ACROSS THREE WINDOWS:</b>", styles["CardTitle"])],
        [
            Paragraph("<b>Immediate Window:</b> Execute pre-contracts for David Lalhlansanga & Vibin Mohanan; acquire starting-caliber dynamic right-back.", styles["Body"]),
        ],
        [
            Paragraph("<b>Medium-Term Window:</b> Reallocate foreign wage budget into prime-age international playmaker (26–29y); review loan returns.", styles["Body"]),
        ],
        [
            Paragraph("<b>Long-Term Window:</b> Complete transition of central defensive core; institute structured academy promotion quota (min 2 BFC B/yr).", styles["Body"]),
        ],
    ]
    t_tl = Table(timeline_data, colWidths=[786])
    t_tl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER_SUBTLE),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_tl)
    story.append(Spacer(1, 6))

    # Executive Mandate for Sporting Director (6 Sentences)
    mandate_text = [
        Paragraph("<b>SPORTING DIRECTOR & TECHNICAL LEADERSHIP EXECUTIVE MANDATE:</b>", styles["CardTitle"]),
        Spacer(1, 2),
        Paragraph(
            "<b>1. Maintain Financial Discipline:</b> Preserve Bengaluru FC's elite 92.6% free-agent acquisition model, avoiding speculative transfer fee inflation.<br/>"
            "<b>2. Pivot to Active Targeting:</b> Shift from reactive summer contract opportunism to aggressive pre-contract identification 6–12 months in advance.<br/>"
            "<b>3. Execute Attacking Succession:</b> Prioritize immediate domestic U24 acquisitions (David Lalhlansanga, Vibin Mohanan) to replace the 35.8y veteran attacking spine.<br/>"
            "<b>4. Resolve Right-Back Deficit:</b> Secure a starting-caliber right-back immediately to restore tactical balance to Gerard Zaragoza's back four.<br/>"
            "<b>5. Protect Academy Asset Equity:</b> Guarantee first-team match minutes for Vinith Venkatesh and Sivasakthi Narayanan, sustaining the club's +500% to +900% developmental appreciation curve.<br/>"
            "<b>6. Wage-Neutral Foreign Transition:</b> Reinvest departing veteran foreign salaries into athletic prime-age overseas players to secure sustainable championship contention.",
            styles["Body"]
        ),
    ]

    t_mandate = Table([[mandate_text]], colWidths=[786])
    t_mandate.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BFC_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_mandate)
    return story


# ==============================================================================
# MAIN COMPILER
# ==============================================================================

def generate_pdf_report():
    logger.info("Compiling Bengaluru FC 15-Page Professional Scouting Dossier PDF...")
    styles = get_report_styles()

    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=landscape(A4),
        leftMargin=26,
        rightMargin=26,
        topMargin=26,
        bottomMargin=24,
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
