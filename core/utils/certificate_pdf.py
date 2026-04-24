import io
import math
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = colors.HexColor("#0B0D1A")
PURPLE    = colors.HexColor("#6C8EFF")
VIOLET    = colors.HexColor("#B06EFF")
WHITE     = colors.white
OFF_WHITE = colors.HexColor("#E8EAFF")
DIM       = colors.HexColor("#8892B0")
DIM2      = colors.HexColor("#444B6A")
GOLD      = colors.HexColor("#FFD700")

PAGE_W, PAGE_H = landscape(A4)
CX = PAGE_W / 2


# ── Helpers ──────────────────────────────────────────────────────────────────
def _lerp(c1, c2, t):
    return colors.Color(
        c1.red   + (c2.red   - c1.red)   * t,
        c1.green + (c2.green - c1.green) * t,
        c1.blue  + (c2.blue  - c1.blue)  * t,
    )


def _hgrad(c, x, y, w, h, cl, cr, steps=80):
    sw = w / steps
    for i in range(steps):
        t = i / max(steps - 1, 1)
        c.setFillColor(_lerp(cl, cr, t))
        c.rect(x + i * sw, y, sw + 0.6, h, fill=1, stroke=0)


def _radial_glow(c, cx, cy, r_max, base_col, peak_alpha=0.10, steps=28):
    for i in range(steps, 0, -1):
        t = i / steps
        a = t * t * peak_alpha
        c.setFillColor(colors.Color(base_col.red, base_col.green, base_col.blue, alpha=a))
        c.circle(cx, cy, r_max * t, fill=1, stroke=0)


def _topo_lines(c, n=14, alpha=0.038):
    """Subtle topographic ellipse watermark, centred on page."""
    for i in range(1, n + 1):
        rx = PAGE_W * 0.08 + i * PAGE_W * 0.042
        ry = PAGE_H * 0.06 + i * PAGE_H * 0.034
        ox = math.sin(i * 0.65) * PAGE_W * 0.025
        oy = math.cos(i * 0.50) * PAGE_H * 0.020
        fade = alpha * (1.0 - i / (n + 1)) + 0.005
        c.setStrokeColor(colors.Color(0.42, 0.56, 1.0, alpha=fade))
        c.setLineWidth(0.55)
        c.ellipse(CX + ox - rx, PAGE_H * 0.5 + oy - ry,
                  CX + ox + rx, PAGE_H * 0.5 + oy + ry,
                  fill=0, stroke=1)


def _gradient_text_centred(c, text, cx, y, font, size, cl, cr):
    """Centre-aligned text with per-character horizontal gradient."""
    c.setFont(font, size)
    total_w = c.stringWidth(text, font, size)
    x_cur = cx - total_w / 2
    for ch in text:
        ch_w = c.stringWidth(ch, font, size)
        t = (x_cur - (cx - total_w / 2) + ch_w / 2) / max(total_w, 1)
        c.setFillColor(_lerp(cl, cr, max(0.0, min(1.0, t))))
        c.drawString(x_cur, y, ch)
        x_cur += ch_w


def _divider(c, cx, y, w, cl, cr):
    """Thin gradient line with a diamond at centre."""
    _hgrad(c, cx - w / 2, y, w, 1.0, cl, cr, steps=50)
    mid_col = _lerp(cl, cr, 0.5)
    d = 4
    c.setFillColor(mid_col)
    p = c.beginPath()
    p.moveTo(cx,     y + d)
    p.lineTo(cx + d, y)
    p.lineTo(cx,     y - d)
    p.lineTo(cx - d, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)




# ── Certificate generator ─────────────────────────────────────────────────────
def generate_certificate_pdf(user, course, certificate_id, issued_at, score_pct):
    """Clean centred Coursera-inspired certificate — Erudite dark theme."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # ── Background ────────────────────────────────────────────────────────
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Radial glow (top-centre, behind logo)
    _radial_glow(c, CX, PAGE_H - 50, 260, PURPLE, peak_alpha=0.08)
    # Softer glow bottom-centre
    _radial_glow(c, CX, 60, 200, VIOLET, peak_alpha=0.05)

    # Topographic watermark
    _topo_lines(c, n=15, alpha=0.04)


    # ── Border ────────────────────────────────────────────────────────────
    c.setStrokeColor(colors.Color(0.42, 0.56, 1.0, alpha=0.22))
    c.setLineWidth(1.0)
    c.rect(10, 10, PAGE_W - 20, PAGE_H - 20, fill=0, stroke=1)
    c.setStrokeColor(colors.Color(0.69, 0.43, 1.0, alpha=0.10))
    c.setLineWidth(0.5)
    c.rect(17, 17, PAGE_W - 34, PAGE_H - 34, fill=0, stroke=1)

    # ── ERUDITE wordmark logo ─────────────────────────────────────────────
    logo_y = PAGE_H - 88
    _gradient_text_centred(c, "ERUDITE", CX, logo_y, "Helvetica-Bold", 50, PURPLE, VIOLET)

    # Divider below logo
    _divider(c, CX, logo_y - 22,
             280,
             colors.Color(0.42, 0.56, 1.0, alpha=0.35),
             colors.Color(0.69, 0.43, 1.0, alpha=0.35))

    # ── "This is to certify that" ─────────────────────────────────────────
    date_str = issued_at.strftime("%B %d, %Y") if issued_at else ""
    c.setFillColor(DIM)
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(CX, logo_y - 58, "This is to certify that")

    # ── Student name ──────────────────────────────────────────────────────
    username = getattr(user, "get_full_name", lambda: "")() or user.username
    name_y = logo_y - 110
    _gradient_text_centred(c, username, CX, name_y, "Helvetica-Bold", 42, WHITE, OFF_WHITE)

    # Thin gradient line under name
    name_w = c.stringWidth(username, "Helvetica-Bold", 42)
    line_w = max(name_w + 60, 200)
    _hgrad(c, CX - line_w / 2, name_y - 12, line_w, 1.5,
           colors.Color(0.42, 0.56, 1.0, alpha=0.45),
           colors.Color(0.69, 0.43, 1.0, alpha=0.45))

    # ── "has successfully completed" ──────────────────────────────────────
    c.setFillColor(DIM)
    c.setFont("Helvetica", 13)
    c.drawCentredString(CX, name_y - 34, "has successfully completed")

    # ── Course title ──────────────────────────────────────────────────────
    title_y = name_y - 72
    title = course.title
    max_title_w = PAGE_W - 160
    for fs in [20, 18, 16, 14, 13]:
        if c.stringWidth(title, "Helvetica-Bold", fs) <= max_title_w:
            c.setFont("Helvetica-Bold", fs)
            break
    c.setFillColor(OFF_WHITE)
    c.drawCentredString(CX, title_y, title)

    # ── Date · Level · Score ──────────────────────────────────────────────
    level = getattr(course, "level", "").capitalize() or "N/A"
    c.setFillColor(DIM)
    c.setFont("Helvetica", 11)
    c.drawCentredString(CX, title_y - 28,
                        f"{date_str}   ·   Level: {level}   ·   Score: {score_pct:.1f}%")

    # ── Footer ────────────────────────────────────────────────────────────
    cert_short = str(certificate_id)[:8].upper()
    _hgrad(c, 40, 36, PAGE_W - 80, 0.8,
           colors.Color(0.42, 0.56, 1.0, alpha=0.15),
           colors.Color(0.69, 0.43, 1.0, alpha=0.15))
    c.setFillColor(DIM2)
    c.setFont("Helvetica", 8)
    c.drawCentredString(CX, 22, f"Certificate ID: {cert_short}   ·   Issued by Erudite Platform")

    c.save()
    return buf.getvalue()
