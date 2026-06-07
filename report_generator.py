import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.piecharts import Pie

# ── Brand colours ─────────────────────────────────────────────────────────────
DARK_BG      = colors.HexColor("#080C14")
CARD_BG      = colors.HexColor("#0F1929")
BLUE         = colors.HexColor("#63B3ED")
PURPLE       = colors.HexColor("#B794F4")
GREEN        = colors.HexColor("#68D391")
ORANGE       = colors.HexColor("#FC8A4E")
YELLOW       = colors.HexColor("#F6E05E")
TEXT_PRIMARY = colors.HexColor("#F0F4FF")
TEXT_MUTED   = colors.HexColor("#718096")
WHITE        = colors.white
BORDER       = colors.HexColor("#1E2D45")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


# ── Style helpers ──────────────────────────────────────────────────────────────
def style(name, **kwargs):
    base = dict(
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=TEXT_PRIMARY, spaceAfter=4,
    )
    base.update(kwargs)
    return ParagraphStyle(name, **base)


S_TITLE   = style("title",   fontName="Helvetica-Bold", fontSize=26, leading=32,
                  textColor=BLUE, alignment=TA_CENTER, spaceAfter=2)
S_SUB     = style("sub",     fontSize=10, textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=0)
S_H1      = style("h1",      fontName="Helvetica-Bold", fontSize=13, leading=18,
                  textColor=BLUE, spaceBefore=14, spaceAfter=6)
S_H2      = style("h2",      fontName="Helvetica-Bold", fontSize=10, leading=14,
                  textColor=TEXT_PRIMARY, spaceAfter=4)
S_BODY    = style("body",    fontSize=9,  leading=14, textColor=TEXT_PRIMARY)
S_MUTED   = style("muted",   fontSize=8,  leading=12, textColor=TEXT_MUTED)
S_BADGE_G = style("badge_g", fontName="Helvetica-Bold", fontSize=8,
                  textColor=GREEN,  alignment=TA_CENTER)
S_BADGE_O = style("badge_o", fontName="Helvetica-Bold", fontSize=8,
                  textColor=ORANGE, alignment=TA_CENTER)
S_BADGE_B = style("badge_b", fontName="Helvetica-Bold", fontSize=8,
                  textColor=BLUE,   alignment=TA_CENTER)
S_LABEL   = style("label",   fontName="Helvetica-Bold", fontSize=7,
                  textColor=BLUE, spaceAfter=2)
S_ORIG    = style("orig",    fontSize=8, leading=13, textColor=TEXT_MUTED,
                  leftIndent=6, spaceAfter=3)
S_SUGG    = style("sugg",    fontName="Helvetica-Bold", fontSize=8.5, leading=13,
                  textColor=GREEN, leftIndent=6, spaceAfter=6)
S_ISSUE   = style("issue",   fontSize=8.5, leading=13, textColor=TEXT_PRIMARY,
                  leftIndent=8)
S_CENTER  = style("center",  alignment=TA_CENTER)
S_RIGHT   = style("right",   fontSize=8, textColor=TEXT_MUTED, alignment=TA_RIGHT)


def hr(color=BORDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=8, spaceBefore=4)


def spacer(h=6):
    return Spacer(1, h)


# ── Score ring (drawn with ReportLab graphics) ────────────────────────────────
def score_ring(score: int, label: str, ring_color) -> Drawing:
    size = 110
    cx, cy = size / 2, size / 2
    r_outer, r_inner = 46, 34
    d = Drawing(size, size)

    # Background ring
    from reportlab.graphics.shapes import Wedge, Circle as GCircle
    bg = GCircle(cx, cy, r_outer)
    bg.fillColor = BORDER
    bg.strokeColor = None
    d.add(bg)

    # Filled arc using wedge
    if score > 0:
        end_angle = 90 - (score / 100) * 360
        wedge = Wedge(cx, cy, r_outer, end_angle, 90, radius1=r_inner)
        wedge.fillColor = ring_color
        wedge.strokeColor = None
        d.add(wedge)

    # Inner circle (cutout)
    inner = GCircle(cx, cy, r_inner)
    inner.fillColor = CARD_BG
    inner.strokeColor = None
    d.add(inner)

    # Score text
    pct = String(cx, cy + 4, f"{score}%", textAnchor="middle",
                 fontSize=16, fontName="Helvetica-Bold", fillColor=WHITE)
    lbl = String(cx, cy - 14, label, textAnchor="middle",
                 fontSize=7, fontName="Helvetica", fillColor=TEXT_MUTED)
    d.add(pct)
    d.add(lbl)
    return d


# ── Card table wrapper ────────────────────────────────────────────────────────
def card(content_rows, col_widths=None, bg=CARD_BG, padding=10):
    usable = PAGE_W - 2 * MARGIN
    w = col_widths or [usable]
    t = Table(content_rows, colWidths=w)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), bg),
        ("ROUNDEDCORNERS", [8]),
        ("BOX",         (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING",  (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
    ]))
    return t


# ── Skill badge pill ──────────────────────────────────────────────────────────
def skill_pill(text: str, kind: str = "match") -> Table:
    color  = GREEN  if kind == "match" else ORANGE
    bg_hex = "#0D2A1A" if kind == "match" else "#2A1A0D"
    s = ParagraphStyle("pill", fontName="Helvetica-Bold", fontSize=7.5,
                       textColor=color, alignment=TA_CENTER)
    t = Table([[Paragraph(f"{'✓' if kind=='match' else '✗'}  {text}", s)]],
              colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ("BOX",           (0, 0), (-1, -1), 0.5, color),
        ("ROUNDEDCORNERS", [10]),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]))
    return t


# ── Main generator ────────────────────────────────────────────────────────────
def generate_pdf_report(result: dict, keyword_score: int) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="HireSense.AI Resume Analysis Report",
    )

    usable_w = PAGE_W - 2 * MARGIN
    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    now = datetime.now().strftime("%B %d, %Y  •  %I:%M %p")
    header_data = [[
        Paragraph("HireSense<font color='#B794F4'>.AI</font>", S_TITLE),
    ]]
    header_t = Table(header_data, colWidths=[usable_w])
    header_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(header_t)
    story.append(Paragraph("Resume Analysis Report", S_SUB))
    story.append(Paragraph(f"Generated on {now}", S_MUTED))
    story.append(spacer(10))
    story.append(hr(BLUE, 1.5))
    story.append(spacer(8))

    # ── SCORES ROW ────────────────────────────────────────────────────────────
    ai_score  = result.get("match_score", 0)

    def ring_color(s):
        return GREEN if s >= 70 else YELLOW if s >= 50 else ORANGE

    ring_ai = score_ring(ai_score,      "AI Match",    ring_color(ai_score))
    ring_kw = score_ring(keyword_score, "Keyword Match", ring_color(keyword_score))

    feedback = result.get("overall_feedback", "No feedback available.")
    assessment_para = [
        Paragraph("OVERALL ASSESSMENT", S_LABEL),
        spacer(4),
        Paragraph(feedback, S_BODY),
    ]

    score_tbl = Table(
        [[ring_ai, ring_kw, assessment_para]],
        colWidths=[usable_w * 0.22, usable_w * 0.22, usable_w * 0.56],
    )
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEAFTER",     (0, 0), (1, 0),   0.5, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (1, 0),   "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(KeepTogether([score_tbl]))
    story.append(spacer(14))

    # ── SKILLS ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Skill Analysis", S_H1))
    story.append(hr())

    matched  = result.get("matched_skills", [])
    missing  = result.get("missing_skills", [])
    half_w   = (usable_w - 6) / 2

    def pills_block(items, kind):
        if not items:
            return [Paragraph("None found.", S_MUTED)]
        rows = []
        row = []
        for i, sk in enumerate(items):
            row.append(skill_pill(sk, kind))
            if len(row) == 3 or i == len(items) - 1:
                while len(row) < 3:
                    row.append("")
                rows.append(row[:])
                row = []
        t = Table(rows, colWidths=[half_w * 0.33] * 3)
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ]))
        return [t]

    matched_block = [
        [Paragraph("✅  MATCHED SKILLS", style("mg", fontName="Helvetica-Bold",
                    fontSize=9, textColor=GREEN))],
        *[[p] for p in pills_block(matched, "match")],
    ]
    missing_block = [
        [Paragraph("❌  MISSING SKILLS", style("mr", fontName="Helvetica-Bold",
                    fontSize=9, textColor=ORANGE))],
        *[[p] for p in pills_block(missing, "miss")],
    ]

    def skill_card(rows, col_w):
        t = Table(rows, colWidths=[col_w])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("ROUNDEDCORNERS", [8]),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG]),
        ]))
        return t

    skills_row = Table(
        [[skill_card(matched_block, half_w), skill_card(missing_block, half_w)]],
        colWidths=[half_w, half_w], hAlign="LEFT",
    )
    skills_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("COLPADDING",    (0, 0), (-1, -1), 6),
    ]))
    story.append(skills_row)
    story.append(spacer(14))

    # ── BULLET REWRITES ───────────────────────────────────────────────────────
    weak = result.get("weak_bullets", [])
    if weak:
        story.append(Paragraph("Bullet Point Rewrites", S_H1))
        story.append(hr())

        for i, item in enumerate(weak, 1):
            orig = item.get("original", "")
            sugg = item.get("suggestion", "")
            block = [
                [Paragraph(f"#{i}", style("num", fontName="Helvetica-Bold",
                            fontSize=9, textColor=BLUE))],
                [Paragraph("ORIGINAL", S_LABEL)],
                [Paragraph(orig, S_ORIG)],
                [Paragraph("IMPROVED", style("il", fontName="Helvetica-Bold",
                            fontSize=7, textColor=GREEN, spaceAfter=2))],
                [Paragraph(sugg, S_SUGG)],
            ]
            t = Table(block, colWidths=[usable_w])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
                ("BACKGROUND",    (0, 0), (0, 0),   colors.HexColor("#0D1929")),
                ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
                ("LINEBEFORE",    (0, 2), (0, 4),   2, BLUE),
                ("ROUNDEDCORNERS", [6]),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ]))
            story.append(KeepTogether([t, spacer(6)]))

        story.append(spacer(8))

    # ── STRUCTURE & GRAMMAR ───────────────────────────────────────────────────
    story.append(Paragraph("Resume Quality Check", S_H1))
    story.append(hr())

    missing_sec  = result.get("missing_sections", [])
    grammar_iss  = result.get("grammar_issues", [])

    def issue_rows(items, accent, icon):
        if not items:
            return [[Paragraph(f"{icon}  All clear — no issues found.",
                               style("ok", fontSize=9, textColor=GREEN))]]
        rows = []
        for it in items:
            rows.append([Paragraph(f"{icon}  {it}", S_ISSUE)])
        return rows

    struct_rows  = [[Paragraph("📋  RESUME STRUCTURE", style("sh", fontName="Helvetica-Bold",
                                fontSize=9, textColor=BLUE))]] + \
                   issue_rows(missing_sec, ORANGE, "⚠")
    grammar_rows = [[Paragraph("✏️  LANGUAGE & GRAMMAR", style("gh", fontName="Helvetica-Bold",
                                fontSize=9, textColor=PURPLE))]] + \
                   issue_rows(grammar_iss, YELLOW, "💡")

    qc_row = Table(
        [[skill_card(struct_rows, half_w), skill_card(grammar_rows, half_w)]],
        colWidths=[half_w, half_w],
    )
    qc_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(qc_row)
    story.append(spacer(20))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(hr(BLUE, 0.8))
    story.append(Paragraph(
        "Generated by <font color='#63B3ED'><b>HireSense.AI</b></font> — "
        "AI-powered resume intelligence. Results are for guidance only.",
        style("footer", fontSize=7.5, textColor=TEXT_MUTED, alignment=TA_CENTER)
    ))

    # ── BUILD ─────────────────────────────────────────────────────────────────
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()