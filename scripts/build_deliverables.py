# -*- coding: utf-8 -*-
"""Genera: diapositivas PDF (7), EDT PNG HR, cronograma CPM PDF (ruta crítica roja)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from reportlab.lib.colors import Color, HexColor, white, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides" / "Defensa_Ejecutiva_GA15_RfP.pdf"
EDT_PNG = ROOT / "diagrams" / "EDT_WBS_FaseI.png"
CPM_PDF = ROOT / "schedule" / "Cronograma_CPM_FaseI.pdf"
LOGO = ROOT / "assets" / "logo_uide.jpeg"
REPO = "https://github.com/notnoneavai/temp-pharma-rfp-ga15"

MAROON = HexColor("#800040")
GOLD = HexColor("#C5A043")
LIGHT = HexColor("#F5E6EC")
DARK = HexColor("#2B2B2B")
CRIT = HexColor("#CC0000")
GRAY = HexColor("#666666")


def draw_header(c: canvas.Canvas, w, h, title: str):
    c.setFillColor(MAROON)
    c.rect(0, h - 1.6 * cm, w, 1.6 * cm, fill=1, stroke=0)
    if LOGO.exists():
        try:
            c.drawImage(str(LOGO), 0.8 * cm, h - 1.45 * cm, width=3.2 * cm, height=1.15 * cm, mask="auto", preserveAspectRatio=True, anchor="sw")
        except Exception:
            pass
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 0.8 * cm, h - 1.0 * cm, title)


def draw_footer(c: canvas.Canvas, w, page: int, total: int = 7):
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(0.8 * cm, 1.0 * cm, w - 0.8 * cm, 1.0 * cm)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(0.8 * cm, 0.45 * cm, "UIDE · Gestión de Proyectos de TI · GA-1.5 RfP")
    c.drawRightString(w - 0.8 * cm, 0.45 * cm, f"{page}/{total}")


def bullet(c, x, y, text, size=11, color=DARK, max_width=24 * cm):
    c.setFillColor(MAROON)
    c.circle(x + 0.12 * cm, y + 0.12 * cm, 0.12 * cm, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    # simple wrap
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if c.stringWidth(trial, "Helvetica", size) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for i, line in enumerate(lines):
        c.drawString(x + 0.5 * cm, y - i * (size + 3), line)
    return y - len(lines) * (size + 3) - 0.35 * cm


def card(c, x, y, w, h, fill=LIGHT):
    c.setFillColor(fill)
    c.setStrokeColor(MAROON)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)


def build_slides():
    w, h = landscape(A4)
    c = canvas.Canvas(str(SLIDES), pagesize=landscape(A4))

    # ---- 1 Portada ----
    c.setFillColor(HexColor("#FAF7F8"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(MAROON)
    c.rect(0, 0, 1.2 * cm, h, fill=1, stroke=0)
    if LOGO.exists():
        c.drawImage(str(LOGO), 2 * cm, h - 3.2 * cm, width=5.5 * cm, height=2.0 * cm, mask="auto", preserveAspectRatio=True)
    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(2 * cm, h - 4.5 * cm, "Defensa Ejecutiva GA-1.5")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(DARK)
    c.drawString(2 * cm, h - 5.5 * cm, "Registro automático y auditable de temperatura para farmacias")
    c.setFont("Helvetica", 11)
    c.setFillColor(GRAY)
    c.drawString(2 * cm, h - 6.3 * cm, "Buzón Habilitante · Compuerta Ready for Planning (RfP) · Fase I")
    c.drawString(2 * cm, h - 6.9 * cm, "26 de noviembre de 2026")

    roles = [
        ("Madeleine Y. Jiménez Gaona", "Project Manager"),
        ("Freddy E. Guaman Gonzalez", "Product Owner"),
        ("Franco R. Quezada Ordoñez", "Arquitecto de Software / Risk Manager"),
    ]
    y = h - 8.2 * cm
    for name, role in roles:
        card(c, 2 * cm, y - 0.15 * cm, 16 * cm, 1.1 * cm)
        c.setFillColor(MAROON)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2.4 * cm, y + 0.45 * cm, name)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 10)
        c.drawString(2.4 * cm, y + 0.1 * cm, role)
        y -= 1.35 * cm
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawString(2 * cm, 1.2 * cm, REPO)
    c.showPage()

    # ---- 2 Problema + valor ----
    draw_header(c, w, h, "1. Problema y propuesta de valor")
    draw_footer(c, w, 2)
    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5 * cm, h - 2.6 * cm, "Brecha operativa")
    y = h - 3.3 * cm
    for t in [
        "Registro manual 2 veces/día: sin evidencia nocturna ni de fines de semana.",
        "Guía ARCSA IE-B.3.4.2-EST-01 exige control de almacenamiento y trazabilidad.",
        "Riesgo: sanción, merma de cadena de frío y bitácora no auditable.",
    ]:
        y = bullet(c, 1.5 * cm, y, t, size=11, max_width=25 * cm)

    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5 * cm, y - 0.3 * cm, "Aporte del piloto")
    y -= 1.0 * cm
    for t in [
        "Registro continuo + alerta fuera de rango + reporte de incidente.",
        "Historial no alterable → evidencia ante inspector.",
        "Buffer local si cae el Wi-Fi; plataforma web para el regente.",
    ]:
        y = bullet(c, 1.5 * cm, y, t, size=11, max_width=25 * cm)
    c.showPage()

    # ---- 3 Business Case ----
    draw_header(c, w, h, "2. Business Case (viabilidad)")
    draw_footer(c, w, 3)
    metrics = [
        ("Inversión", "USD 6.000"),
        ("Suscripción", "USD 29/mes"),
        ("Payback", "≈ 18,6 meses"),
        ("ROI Año 1", "64,4 %"),
        ("NPV 3 años", "≈ USD 2.910"),
        ("Decisión", "GO → RfP"),
    ]
    x0 = 1.5 * cm
    for i, (k, v) in enumerate(metrics):
        col, row = i % 3, i // 3
        x = x0 + col * 8.5 * cm
        y = h - 4.2 * cm - row * 3.2 * cm
        card(c, x, y, 7.8 * cm, 2.6 * cm)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 10)
        c.drawString(x + 0.4 * cm, y + 1.7 * cm, k)
        c.setFillColor(MAROON)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x + 0.4 * cm, y + 0.7 * cm, v)
    c.setFont("Helvetica", 9)
    c.setFillColor(GRAY)
    c.drawString(1.5 * cm, 1.5 * cm, "Supuestos piloto: 18 farmacias Año 1 · r=12 % · OPEX USD 2.400")
    c.showPage()

    # ---- 4 EDT ----
    draw_header(c, w, h, "3. Ingeniería del alcance (EDT / WBS)")
    draw_footer(c, w, 4)
    if EDT_PNG.exists():
        c.drawImage(str(EDT_PNG), 0.8 * cm, 1.4 * cm, width=w - 1.6 * cm, height=h - 3.4 * cm, preserveAspectRatio=True, anchor="c", mask="auto")
    else:
        c.setFont("Helvetica", 12)
        c.drawString(2 * cm, h / 2, "Ver diagrams/EDT_WBS_FaseI.png")
    c.showPage()

    # ---- 5 CPM ----
    draw_header(c, w, h, "4. CPM — ruta crítica")
    draw_footer(c, w, 5)
    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, h - 2.6 * cm, "Ruta crítica (holgura = 0) · 28 días hábiles")
    c.setFillColor(CRIT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(1.5 * cm, h - 3.3 * cm, "A → C → D → G → H → J → K → L")

    # mini network boxes
    nodes = ["A", "C", "D", "G", "H", "J", "K", "L"]
    x = 1.5 * cm
    y = h - 5.2 * cm
    for i, n in enumerate(nodes):
        c.setFillColor(CRIT)
        c.roundRect(x, y, 2.4 * cm, 1.2 * cm, 4, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(x + 1.2 * cm, y + 0.4 * cm, n)
        if i < len(nodes) - 1:
            c.setStrokeColor(CRIT)
            c.setLineWidth(2)
            c.line(x + 2.45 * cm, y + 0.6 * cm, x + 3.0 * cm, y + 0.6 * cm)
        x += 3.15 * cm

    c.setFillColor(DARK)
    c.setFont("Helvetica", 11)
    y = h - 7.0 * cm
    for t in [
        "Actividades no críticas con holgura: B (5), E (5), F (1), I (5).",
        "Fuente editable: schedule/Cronograma_CPM_FaseI.gan (GanttProject).",
        "PDF del Gantt: schedule/Cronograma_CPM_FaseI.pdf — barras críticas en rojo.",
    ]:
        y = bullet(c, 1.5 * cm, y, t, size=11, max_width=25 * cm)
    c.showPage()

    # ---- 6 Riesgos + presupuesto ----
    draw_header(c, w, h, "5. Riesgos EMV y línea base de costo")
    draw_footer(c, w, 6)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(MAROON)
    c.drawString(1.5 * cm, h - 2.5 * cm, "Top EMV")
    rows = [
        ("R7 Pérdida de lecturas al reconectar", "USD 600", "Franco Quezada"),
        ("R1 Alertas desatendidas", "USD 385", "Freddy Guaman"),
        ("R4 Evidencia sin integridad", "USD 280", "Franco Quezada"),
        ("Σ Reserva de contingencia (8 riesgos)", "USD 2.102,50", "PM controla"),
    ]
    y = h - 3.0 * cm
    for name, emv, owner in rows:
        card(c, 1.5 * cm, y - 1.15 * cm, 16 * cm, 1.2 * cm)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 10)
        c.drawString(1.8 * cm, y - 0.45 * cm, name)
        c.setFillColor(MAROON)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(12.5 * cm, y - 0.45 * cm, emv)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 9)
        c.drawString(13.2 * cm, y - 0.45 * cm, owner)
        y -= 1.4 * cm

    card(c, 18.2 * cm, h - 8.5 * cm, 9.5 * cm, 5.5 * cm)
    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(18.6 * cm, h - 3.5 * cm, "Línea base de costo")
    c.setFont("Helvetica", 10)
    c.setFillColor(DARK)
    c.drawString(18.6 * cm, h - 4.4 * cm, "Costo directo EDT")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(27.2 * cm, h - 4.4 * cm, "6.000")
    c.setFont("Helvetica", 10)
    c.drawString(18.6 * cm, h - 5.2 * cm, "+ Contingencia EMV")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(27.2 * cm, h - 5.2 * cm, "2.102,50")
    c.setStrokeColor(GOLD)
    c.line(18.6 * cm, h - 5.7 * cm, 27.2 * cm, h - 5.7 * cm)
    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(18.6 * cm, h - 6.5 * cm, "Línea base")
    c.drawRightString(27.2 * cm, h - 6.5 * cm, "8.102,50")
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawString(18.6 * cm, h - 7.4 * cm, "USD · fórmula oficial del dossier")
    c.showPage()

    # ---- 7 Decisión RfP ----
    draw_header(c, w, h, "6. Decisión Ready for Planning")
    draw_footer(c, w, 7)
    c.setFillColor(MAROON)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 3.2 * cm, "Recomendación del equipo consultor: APROBAR RfP")
    y = h - 4.3 * cm
    for t in [
        "Alcance: EDT 3 niveles + diccionario con criterios inequívocos (regla 8/80).",
        "Tiempo: CPM con ruta crítica explícita (28 días hábiles).",
        "Costo: línea base USD 8.102,50 (directo + EMV).",
        "Riesgo: 8 riesgos software con Risk Owner y estrategias.",
        "Evidencia: repo privado con Word, .drawio, .gan, PNG y PDF de defensa.",
    ]:
        y = bullet(c, 3 * cm, y, t, size=12, max_width=22 * cm)

    card(c, 3 * cm, 1.6 * cm, w - 6 * cm, 1.8 * cm)
    c.setFillColor(DARK)
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, 2.7 * cm, "Siguiente paso: Sesión 2 de defensa · Empaquetado de evidencia en GitHub")
    c.setFillColor(MAROON)
    c.setFont("Helvetica", 9)
    c.drawCentredString(w / 2, 2.1 * cm, REPO)
    c.showPage()
    c.save()
    print(f"OK slides -> {SLIDES}")


def build_edt_png():
    fig, ax = plt.subplots(figsize=(18, 11), dpi=200)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def box(x, y, w, h, text, fc="#800040", ec="#5B002E", tc="white", fs=9, fw="bold"):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                               linewidth=1.5, facecolor=fc, edgecolor=ec)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, fontweight=fw, wrap=True)

    def link(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color="#800040", linewidth=1.2)

    # Level 1
    box(6.2, 9.4, 5.6, 1.1, "1. Proyecto\nRegistro automático y auditable\nde temperatura para farmacias", fs=10)

    # Level 2
    l2 = [
        (0.3, "1.1 Gestión y\ngobernanza"),
        (3.3, "1.2 Cumplimiento\nARCSA / requisitos"),
        (6.3, "1.3 Nodo IoT\nde temperatura"),
        (9.3, "1.4 Plataforma\ndel regente"),
        (12.3, "1.5 Seguridad e\nintegridad"),
        (15.0, "1.6 Piloto\nrefrigeradora"),
    ]
    for x, t in l2:
        box(x, 7.2, 2.6, 1.1, t, fc="#A64B6B", fs=8)
        link(9.0, 9.4, x + 1.3, 8.3)

    # Level 3
    l3 = {
        0.3: ["1.1.1 Kickoff &\nCharter", "1.1.2 Plan RfP", "1.1.3 Cierre\ndocumental"],
        3.3: ["1.2.1 Matriz\nARCSA", "1.2.2 Spec\nregistro/alertas", "1.2.3 Criterios\nreporte"],
        6.3: ["1.3.1 Sonda &\nmuestreo", "1.3.2 Buffer\noffline", "1.3.3 Alertas\nde umbral"],
        9.3: ["1.4.1 API &\nidentidad", "1.4.2 Tablero\nequipos", "1.4.3 Reporte\ninalterable"],
        12.3: ["1.5.1 Hash /\nno alteración", "1.5.2 Accesos\nLOPDP"],
        15.0: ["1.6.1 Protocolo\ncon regente", "1.6.2 Ensayo\nWi-Fi", "1.6.3 Informe\nvalidación RfP"],
    }
    for x, items in l3.items():
        for i, t in enumerate(items):
            y = 5.4 - i * 1.35
            box(x, y, 2.6, 1.05, t, fc="#F5E6EC", ec="#800040", tc="#2B2B2B", fs=7.5, fw="normal")
            link(x + 1.3, 7.2, x + 1.3, y + 1.05)

    ax.text(0.3, 0.35, "EDT por entregables · Regla del 100% · 3 niveles · GA-1.5 Fase I / RfP · UIDE",
            fontsize=10, color="#800040", fontstyle="italic")
    fig.tight_layout()
    EDT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(EDT_PNG, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK EDT PNG -> {EDT_PNG}")


def build_cpm_pdf():
    # Gantt-like chart with critical path in red
    tasks = [
        ("A Kickoff y Charter", 0, 3, True),
        ("B Business Case", 3, 4, False),
        ("C Matriz ARCSA", 3, 5, True),
        ("D EDT + diccionario", 8, 4, True),
        ("E Cronograma CPM", 12, 3, False),
        ("F Diseño nodo IoT", 8, 6, False),
        ("G Diseño plataforma", 12, 5, True),
        ("H Integridad/accesos", 17, 4, True),
        ("I Riesgos 5x5 + EMV", 15, 3, False),
        ("J Protocolo piloto", 21, 3, True),
        ("K Ensayo Wi-Fi", 24, 2, True),
        ("L Cierre RfP", 26, 2, True),
    ]
    # holguras for table
    slack = {"A": 0, "B": 5, "C": 0, "D": 0, "E": 5, "F": 1, "G": 0, "H": 0, "I": 5, "J": 0, "K": 0, "L": 0}

    fig = plt.figure(figsize=(16, 10), dpi=160)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.2, 1.3], hspace=0.35)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    n = len(tasks)
    for i, (name, start, dur, crit) in enumerate(tasks):
        y = n - i - 1
        color = "#CC0000" if crit else "#800040"
        ax.barh(y, dur, left=start, height=0.55, color=color, edgecolor="black", linewidth=0.4, alpha=0.92)
        ax.text(-0.4, y, name, ha="right", va="center", fontsize=9)
        ax.text(start + dur / 2, y, f"{dur}d", ha="center", va="center", fontsize=8, color="white", fontweight="bold")

    ax.set_xlim(-8, 30)
    ax.set_ylim(-0.8, n)
    ax.set_xlabel("Días hábiles desde el inicio (ES)", fontsize=10)
    ax.set_yticks([])
    ax.set_title("Cronograma CPM — Fase I RfP\nBarras ROJAS = Ruta crítica (holgura total = 0)", fontsize=13, color="#800040", pad=10)
    ax.axvline(0, color="#999", lw=0.8)
    ax.axvline(28, color="#CC0000", lw=1.2, linestyle="--")
    ax.text(28.1, n - 0.3, "Fin CP = 28", color="#CC0000", fontsize=8)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    crit_patch = mpatches.Patch(color="#CC0000", label="Ruta crítica")
    other_patch = mpatches.Patch(color="#800040", label="Con holgura")
    ax.legend(handles=[crit_patch, other_patch], loc="lower right")

    # Slack table
    ax2.axis("off")
    ax2.set_title("Tabla de holguras totales (ES/EF/LS/LF)", fontsize=11, color="#800040", loc="left")
    headers = ["ID", "ES", "EF", "LS", "LF", "Holgura", "¿Crítica?"]
    data_map = {
        "A": (0, 3, 0, 3), "B": (3, 7, 8, 12), "C": (3, 8, 3, 8), "D": (8, 12, 8, 12),
        "E": (12, 15, 17, 20), "F": (8, 14, 9, 15), "G": (12, 17, 12, 17), "H": (17, 21, 17, 21),
        "I": (15, 18, 20, 23), "J": (21, 24, 21, 24), "K": (24, 26, 24, 26), "L": (26, 28, 26, 28),
    }
    cell = [headers]
    for tid, (es, ef, ls, lf) in data_map.items():
        ht = slack[tid]
        cell.append([tid, str(es), str(ef), str(ls), str(lf), str(ht), "Sí" if ht == 0 else "No"])
    table = ax2.table(cellText=cell, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.25)
    for (r, col), cell_obj in table.get_celld().items():
        if r == 0:
            cell_obj.set_facecolor("#800040")
            cell_obj.set_text_props(color="white", fontweight="bold")
        else:
            tid = cell[r][0]
            if slack[tid] == 0:
                cell_obj.set_facecolor("#FFD6D6")
            else:
                cell_obj.set_facecolor("#F8F8F8")

    fig.suptitle("UIDE · GA-1.5 · schedule/Cronograma_CPM_FaseI.pdf · Fuente: .gan GanttProject",
                 fontsize=9, color="#666666", y=0.02)
    CPM_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(CPM_PDF, format="pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"OK CPM PDF -> {CPM_PDF}")


def build_network_png():
    """Diagrama de red de actividades con ruta crítica en rojo."""
    out = ROOT / "diagrams" / "Red_CPM_FaseI.png"
    fig, ax = plt.subplots(figsize=(16, 7), dpi=200)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # positions: id -> (x,y), critical?
    pos = {
        "A": (1.0, 3.5, True),
        "B": (3.5, 5.5, False),
        "C": (3.5, 3.5, True),
        "D": (6.0, 3.5, True),
        "E": (8.5, 5.5, False),
        "F": (6.0, 1.5, False),
        "G": (8.5, 3.5, True),
        "H": (11.0, 2.5, True),
        "I": (11.0, 5.5, False),
        "J": (13.0, 2.5, True),
        "K": (14.5, 3.5, True),
        "L": (15.5, 3.5, True),
    }
    # fix L position - too close. Rescale layout
    pos = {
        "A": (0.8, 3.5, True),
        "B": (3.0, 5.6, False),
        "C": (3.0, 3.5, True),
        "D": (5.2, 3.5, True),
        "E": (7.4, 5.6, False),
        "F": (5.2, 1.4, False),
        "G": (7.4, 3.5, True),
        "H": (9.6, 2.5, True),
        "I": (9.6, 5.6, False),
        "J": (11.8, 2.5, True),
        "K": (13.8, 3.5, True),
        "L": (15.5, 3.5, True),
    }
    edges = [
        ("A", "B", False), ("A", "C", True),
        ("B", "E", False), ("C", "D", True), ("C", "F", False),
        ("D", "E", False), ("D", "G", True),
        ("E", "I", False), ("F", "H", False), ("G", "H", True),
        ("H", "J", True), ("I", "K", False), ("J", "K", True), ("K", "L", True),
    ]
    for a, b, crit in edges:
        x1, y1, _ = pos[a]
        x2, y2, _ = pos[b]
        ax.annotate(
            "",
            xy=(x2 - 0.55, y2),
            xytext=(x1 + 0.55, y1),
            arrowprops=dict(arrowstyle="->", color="#CC0000" if crit else "#800040", lw=2 if crit else 1.2),
        )

    labels = {
        "A": "A\n3d", "B": "B\n4d", "C": "C\n5d", "D": "D\n4d",
        "E": "E\n3d", "F": "F\n6d", "G": "G\n5d", "H": "H\n4d",
        "I": "I\n3d", "J": "J\n3d", "K": "K\n2d", "L": "L\n2d",
    }
    for tid, (x, y, crit) in pos.items():
        fc = "#CC0000" if crit else "#800040"
        circ = plt.Circle((x, y), 0.55, facecolor=fc, edgecolor="black", linewidth=1.0, zorder=3)
        ax.add_patch(circ)
        ax.text(x, y, labels[tid], ha="center", va="center", color="white", fontsize=8, fontweight="bold", zorder=4)

    ax.text(0.3, 6.5, "Diagrama de red CPM — Fase I RfP", fontsize=14, color="#800040", fontweight="bold")
    ax.text(0.3, 6.1, "Rojo = ruta crítica A-C-D-G-H-J-K-L (28 días hábiles) · Granate = con holgura", fontsize=9, color="#666666")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK network PNG -> {out}")


def main():
    build_edt_png()
    build_network_png()
    build_cpm_pdf()
    build_slides()


if __name__ == "__main__":
    main()
