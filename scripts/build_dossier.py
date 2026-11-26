# -*- coding: utf-8 -*-
"""Dossier Ejecutivo GA-1.5 — B/N, gráficos nativos de Word, texto directo."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "Plan de Gestión de Riesgos - Farmacias corregido.docx"
OUT = ROOT / "docs" / "Dossier_Ejecutivo_GA15_FaseI_RfP.docx"
REPO_URL = "https://github.com/notnoneavai/temp-pharma-rfp-ga15"

BLACK = RGBColor(0, 0, 0)


def clear_body(doc: Document) -> None:
    body = doc.element.body
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)


def set_run(run, *, bold=False, size=11, italic=False):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    run.font.color.rgb = BLACK
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), "Calibri")
    rFonts.set(qn("w:hAnsi"), "Calibri")


def add_p(
    doc,
    text="",
    *,
    style=None,
    bold=False,
    size=11,
    align=None,
    italic=False,
    space_after=4,
    space_before=0,
):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    if text:
        set_run(p.add_run(text), bold=bold, size=size, italic=italic)
    return p


def add_h(doc, text, level=1):
    p = add_p(
        doc,
        text,
        style=f"Heading {level}",
        bold=True,
        size=13 if level == 1 else 11,
        space_before=10,
        space_after=6,
    )
    for run in p.runs:
        set_run(run, bold=True, size=13 if level == 1 else 11)
    return p


def shade_cell(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_text(cell, text, *, bold=False, size=9, center=False):
    cell.text = ""
    p = cell.paragraphs[0]
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run(text), bold=bold, size=size)


def add_table(doc, headers, rows, col_widths=None, header_black=True):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True, size=9, center=True)
        if header_black:
            shade_cell(table.rows[0].cells[i], "000000")
            for run in table.rows[0].cells[i].paragraphs[0].runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
        else:
            shade_cell(table.rows[0].cells[i], "D9D9D9")
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            set_cell_text(table.rows[r_i + 1].cells[c_i], str(val), size=9)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)
    add_p(doc, "", space_after=2)
    return table


def add_edt_word_diagram(doc):
    """EDT en tabla nativa de Word (B/N)."""
    add_p(doc, "Figura 1. EDT / WBS a 3 niveles (tabla de Word).", bold=True, size=10)

    # Nivel 1
    t1 = doc.add_table(rows=1, cols=1)
    t1.style = "Table Grid"
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_cell_text(
        t1.rows[0].cells[0],
        "1. Proyecto: Registro automático y auditable de temperatura para farmacias",
        bold=True,
        size=10,
        center=True,
    )
    shade_cell(t1.rows[0].cells[0], "000000")
    for run in t1.rows[0].cells[0].paragraphs[0].runs:
        run.font.color.rgb = RGBColor(255, 255, 255)
    add_p(doc, "", space_after=2)

    # Nivel 2
    l2 = [
        "1.1 Gestión y gobernanza",
        "1.2 Cumplimiento ARCSA",
        "1.3 Nodo IoT temperatura",
        "1.4 Plataforma del regente",
        "1.5 Seguridad e integridad",
        "1.6 Piloto refrigeradora",
    ]
    t2 = doc.add_table(rows=1, cols=6)
    t2.style = "Table Grid"
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, txt in enumerate(l2):
        set_cell_text(t2.rows[0].cells[i], txt, bold=True, size=8, center=True)
        shade_cell(t2.rows[0].cells[i], "D9D9D9")
    add_p(doc, "", space_after=2)

    # Nivel 3
    l3 = [
        ["1.1.1 Kickoff y Charter", "1.1.2 Plan RfP", "1.1.3 Cierre documental"],
        ["1.2.1 Matriz ARCSA", "1.2.2 Spec registro/alertas", "1.2.3 Criterios del reporte"],
        ["1.3.1 Sonda y muestreo", "1.3.2 Buffer offline", "1.3.3 Alertas de umbral"],
        ["1.4.1 API e identidad", "1.4.2 Tablero de equipos", "1.4.3 Reporte inalterable"],
        ["1.5.1 Hash / no alteración", "1.5.2 Accesos LOPDP", "—"],
        ["1.6.1 Protocolo con regente", "1.6.2 Ensayo Wi-Fi", "1.6.3 Informe validación RfP"],
    ]
    t3 = doc.add_table(rows=3, cols=6)
    t3.style = "Table Grid"
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, items in enumerate(l3):
        for r, txt in enumerate(items):
            set_cell_text(t3.rows[r].cells[c], txt, size=7, center=True)
    add_p(
        doc,
        "Regla del 100%: cada nivel hijo suma el alcance completo del padre. Fuente editable: diagrams/EDT_WBS_FaseI.drawio",
        size=8,
        italic=True,
        space_after=8,
    )


def add_network_word_diagram(doc):
    """Diagrama de red CPM en tablas de Word (B/N). Crítica = negrita + borde marcado."""
    add_p(doc, "Figura 2. Diagrama de red CPM (tablas de Word).", bold=True, size=10)
    add_p(
        doc,
        "Ruta crítica (holgura = 0): A → C → D → G → H → J → K → L = 28 días hábiles. "
        "Las celdas en negrita son críticas.",
        size=9,
        space_after=4,
    )

    # Camino crítico en una fila
    crit = ["A 3d", "→", "C 5d", "→", "D 4d", "→", "G 5d", "→", "H 4d", "→", "J 3d", "→", "K 2d", "→", "L 2d"]
    tc = doc.add_table(rows=1, cols=len(crit))
    tc.style = "Table Grid"
    tc.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, txt in enumerate(crit):
        bold = txt != "→"
        set_cell_text(tc.rows[0].cells[i], txt, bold=bold, size=8, center=True)
        if bold:
            shade_cell(tc.rows[0].cells[i], "D9D9D9")
    add_p(doc, "Camino crítico", size=8, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    # Caminos con holgura
    add_p(doc, "Caminos con holgura (no críticos)", bold=True, size=9)
    add_table(
        doc,
        ["Camino", "Secuencia", "Holgura"],
        [
            ["Superior", "A → B → E → I → K", "5 días (salvo K, que es crítica)"],
            ["Inferior", "A → C → F → H", "1 día en F"],
        ],
        header_black=True,
    )


def build():
    doc = Document(str(TEMPLATE))
    clear_body(doc)

    # ---- Portada ----
    add_p(doc, "UNIVERSIDAD INTERNACIONAL DEL ECUADOR (UIDE)", bold=True, size=13, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(
        doc,
        "Escuela de Ciencias de la Computación · Gestión de Proyectos de TI · Ing. Daniel Alexander Patiño Vásquez",
        size=9,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    add_p(doc, "DOSSIER EJECUTIVO — BUZÓN HABILITANTE GA-1.5", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8)
    add_p(doc, "Compuerta Ready for Planning (RfP) — Fase I", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(
        doc,
        "Registro automático y auditable de temperatura para farmacias",
        bold=True,
        size=12,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=6,
        space_after=8,
    )

    add_table(
        doc,
        ["Integrante", "Rol", "Responsabilidad"],
        [
            ["Madeleine Yanhely Jiménez Gaona", "Project Manager", "Cronograma, presupuesto, gobernanza"],
            ["Freddy Emanuel Guaman Gonzalez", "Product Owner", "Business Case, alcance, valor"],
            ["Franco Rene Quezada Ordoñez", "Arquitecto / Risk Manager", "EDT técnica, riesgos EMV, integridad"],
        ],
    )
    add_p(doc, "Modalidad: grupal · Fecha: 26/11/2026 · Repo: " + REPO_URL, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(
        doc,
        "Buzón formativo (0 pts). La nota se asienta en GA-1.5 (4 pts).",
        size=8,
        italic=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=10,
    )

    # ============================================================
    add_h(doc, "Capítulo 1. Iniciación y gobernanza", 1)

    add_h(doc, "1.1 Business Case", 2)
    add_p(
        doc,
        "Problema: en farmacias pequeñas el registro de temperatura se anota a mano dos veces al día. "
        "Lo que ocurre en la noche o el fin de semana no queda registrado. Eso incumple la evidencia que "
        "exige la guía ARCSA IE-B.3.4.2-EST-01 y expone a sanción o pérdida de medicamentos.",
    )
    add_p(
        doc,
        "Solución: un registro continuo que alerta si la refrigeradora sale de rango, genera el reporte de "
        "incidente y no se puede alterar. Sirve como evidencia ante el inspector. Paga la farmacia.",
    )
    add_p(doc, "Viabilidad financiera del piloto (presupuesto base USD 6.000):", bold=True, size=10)
    add_table(
        doc,
        ["Indicador", "Valor", "Qué significa"],
        [
            ["Inversión", "USD 6.000", "Costo directo del piloto"],
            ["Precio suscripción", "USD 29 / mes", "Oferta a farmacia independiente"],
            ["Clientes Año 1", "18 farmacias", "Escenario conservador"],
            ["Ingreso Año 1", "USD 6.264", "18 × 29 × 12"],
            ["OPEX Año 1", "USD 2.400", "Hosting, soporte, calibración"],
            ["Beneficio neto Año 1", "USD 3.864", "Ingreso − OPEX"],
            ["Payback", "18,6 meses", "Tiempo para recuperar la inversión"],
            ["ROI Año 1", "64,4 %", "3.864 / 6.000"],
            ["NPV (3 años, 12 %)", "USD 2.910", "Valor actual neto positivo → conviene invertir"],
        ],
    )
    add_p(doc, "Decisión: el NPV es positivo y el payback es menor a 24 meses. Se recomienda aprobar la compuerta RfP.", bold=True, size=10)

    add_h(doc, "1.2 Project Charter", 2)
    add_p(doc, "Proyecto: Registro automático y auditable de temperatura para farmacias.", bold=True)
    add_p(doc, "PM: Madeleine Jiménez · PO: Freddy Guaman · Arquitecto/Risk: Franco Quezada.")

    add_p(doc, "Objetivos SMART", bold=True, size=10, space_before=6)
    add_table(
        doc,
        ["ID", "Objetivo"],
        [
            ["O1", "Entregar el dossier RfP con líneas base de alcance, tiempo, costo y riesgo."],
            ["O2", "Completar EDT a 3 niveles, ≥6 paquetes con criterios de aceptación, CPM y 8 riesgos con EMV."],
            ["O3", "Respetar techo de USD 6.000 de costo directo + reserva EMV."],
            ["O4", "Cubrir el vacío de evidencia frente a inspección ARCSA en farmacias pequeñas."],
            ["O5", "Cerrar evidencia documental el 26/11/2026 a las 23:59."],
        ],
    )

    add_p(doc, "Premisas", bold=True, size=10)
    for t in [
        "La farmacia piloto da acceso a una refrigeradora real.",
        "Los umbrales y el reporte se alinean a la guía ARCSA vigente.",
        "El equipo mantiene commits trazables en GitHub.",
        "La Fase I es planificación RfP, no despliegue comercial.",
    ]:
        add_p(doc, f"• {t}", size=10, space_after=1)

    add_p(doc, "Restricciones", bold=True, size=10, space_before=4)
    for t in [
        "Costo directo máximo: USD 6.000.",
        "Plazo documental: 26/11/2026 23:59.",
        "Sin datos de pacientes (LOPDP).",
        "Sin app móvil nativa ni integración ERP en esta fase.",
    ]:
        add_p(doc, f"• {t}", size=10, space_after=1)

    add_p(doc, "Alcance (IN / OUT)", bold=True, size=10, space_before=4)
    add_table(
        doc,
        ["Incluye", "No incluye"],
        [
            ["Plan RfP, EDT, CPM, riesgos EMV, presupuesto", "Certificación formal ARCSA del producto"],
            ["Diseño de nodo, alertas y buffer offline", "Integración con ERP de terceros"],
            ["Plataforma web del regente y reporte inalterable", "App móvil nativa"],
            ["Piloto en una refrigeradora real", "Venta nacional y facturación electrónica"],
        ],
    )

    add_p(
        doc,
        "Presupuesto Charter: costo directo 6.000 + contingencia EMV 2.102,50 = línea base USD 8.102,50.",
        bold=True,
        size=10,
        space_after=8,
    )

    add_h(doc, "1.3 Interesados (Mitchell et al., 1997)", 2)
    add_p(doc, "Se clasifican por poder, legitimidad y urgencia.", size=10)
    add_table(
        doc,
        ["Interesado", "Poder", "Legitimidad", "Urgencia", "Tipo", "Qué hacer"],
        [
            ["Regente farmacia piloto", "Alto", "Sí", "Alta", "Definitivo", "Gestionar de cerca"],
            ["Dueño de la farmacia", "Alto", "Sí", "Media", "Expectante", "Mantener satisfecho (ROI/sanción)"],
            ["Inspector ARCSA", "Alto", "Sí", "Baja*", "Expectante", "Diseñar evidencia auditable"],
            ["Docente / Project Owner", "Alto", "Sí", "Alta", "Definitivo", "Cumplir rúbrica GA-1.5"],
            ["Equipo consultor", "Medio", "Sí", "Alta", "Expectante", "Coordinar y entregar"],
            ["Operador de turno", "Bajo", "Sí", "Alta", "Expectante", "Alertas simples"],
            ["Proveedor de sondas", "Medio", "Sí", "Media", "Expectante", "Garantía/calibración"],
            ["Pacientes (indirectos)", "Bajo", "Sí", "Baja", "Latente", "No capturar sus datos"],
        ],
    )
    add_p(doc, "*La urgencia del inspector sube solo en visita; el diseño asume esa latencia.", size=8, italic=True)

    # ============================================================
    add_h(doc, "Capítulo 2. Alcance (EDT/WBS)", 1)
    add_h(doc, "2.1 Diagrama EDT a 3 niveles", 2)
    add_p(
        doc,
        "La EDT se arma por entregables. Cumple la regla del 100%: el trabajo de los hijos cubre todo el padre.",
        size=10,
    )
    add_edt_word_diagram(doc)

    add_h(doc, "2.2 Diccionario de la EDT", 2)
    add_p(doc, "Ocho paquetes terminales. Esfuerzo entre 8 y 80 horas (regla 8/80).", size=10)
    add_table(
        doc,
        ["ID", "Paquete", "Qué entrega", "Horas", "Criterio de aceptación", "Owner"],
        [
            ["1.1.2", "Plan RfP", "Líneas base alcance/tiempo/costo/riesgo", "40", "Dossier aprobado por PM/PO/Arch en el repo", "M. Jiménez"],
            ["1.2.1", "Matriz ARCSA", "Requisitos vs. guía ARCSA", "24", "≥95 % controles mapeados; gaps con dueño", "F. Guaman"],
            ["1.3.2", "Buffer offline", "Lecturas locales sin Wi-Fi", "56", "2 h sin Wi-Fi: 0 pérdidas; sync por ID OK", "F. Quezada"],
            ["1.3.3", "Alertas", "Aviso fuera de rango", "32", "Alerta ≤60 s; acuse por turno", "F. Quezada"],
            ["1.4.3", "Reporte", "Exportación para inspección", "40", "Incluye hash; no se editan lecturas", "F. Guaman"],
            ["1.5.1", "Integridad", "Historial no alterable", "48", "Alteración falla verificación", "F. Quezada"],
            ["1.6.1", "Protocolo piloto", "Prueba con regente", "24", "Acta firmada pass/fail", "F. Guaman"],
            ["1.6.2", "Ensayo Wi-Fi", "Corte de red y reconciliación", "16", "Sin huecos ni duplicados", "F. Quezada"],
        ],
    )

    # ============================================================
    add_h(doc, "Capítulo 3. Tiempo y CPM", 1)
    add_h(doc, "3.1 Precedencias", 2)
    add_p(doc, "Relaciones Finish-to-Start. Duraciones en días hábiles. Fuente: schedule/Cronograma_CPM_FaseI.gan", size=10)
    add_table(
        doc,
        ["ID", "Actividad", "Días", "Predecesoras", "Sucesoras"],
        [
            ["A", "Kickoff y Charter", "3", "—", "B, C"],
            ["B", "Business Case y presupuesto", "4", "A", "E"],
            ["C", "Matriz ARCSA / requisitos", "5", "A", "D, F"],
            ["D", "EDT + diccionario", "4", "C", "E, G"],
            ["E", "Cronograma CPM", "3", "B, D", "I"],
            ["F", "Diseño nodo IoT + offline", "6", "C", "H"],
            ["G", "Diseño plataforma y reporte", "5", "D", "H"],
            ["H", "Integridad y accesos", "4", "F, G", "J"],
            ["I", "Riesgos 5×5 + EMV", "3", "E", "K"],
            ["J", "Protocolo piloto", "3", "H", "K"],
            ["K", "Ensayo Wi-Fi", "2", "I, J", "L"],
            ["L", "Cierre RfP", "2", "K", "—"],
        ],
    )

    add_h(doc, "3.2 Red, ruta crítica y holguras", 2)
    add_network_word_diagram(doc)
    add_table(
        doc,
        ["ID", "ES", "EF", "LS", "LF", "Holgura", "Crítica"],
        [
            ["A", "0", "3", "0", "3", "0", "Sí"],
            ["B", "3", "7", "8", "12", "5", "No"],
            ["C", "3", "8", "3", "8", "0", "Sí"],
            ["D", "8", "12", "8", "12", "0", "Sí"],
            ["E", "12", "15", "17", "20", "5", "No"],
            ["F", "8", "14", "9", "15", "1", "No"],
            ["G", "12", "17", "12", "17", "0", "Sí"],
            ["H", "17", "21", "17", "21", "0", "Sí"],
            ["I", "15", "18", "20", "23", "5", "No"],
            ["J", "21", "24", "21", "24", "0", "Sí"],
            ["K", "24", "26", "24", "26", "0", "Sí"],
            ["L", "26", "28", "26", "28", "0", "Sí"],
        ],
    )
    add_p(
        doc,
        "PDF del Gantt con ruta crítica: schedule/Cronograma_CPM_FaseI.pdf · Fuente editable: .gan",
        size=8,
        italic=True,
        space_after=8,
    )

    # ============================================================
    add_h(doc, "Capítulo 4. Riesgos y presupuesto", 1)
    add_h(doc, "4.1 Matriz 5×5", 2)
    add_p(doc, "Severidad = Probabilidad × Impacto (1–5). Ocho riesgos de software.", size=10)
    add_table(
        doc,
        ["Cód.", "Riesgo", "P×I", "Zona"],
        [
            ["R1", "Alertas desatendidas", "16", "Alta (15–25)"],
            ["R2", "Retiro de la farmacia piloto", "10", "Media-alta (10–14)"],
            ["R3", "Umbrales o reporte mal definidos", "9", "Media (5–9)"],
            ["R4", "Evidencia sin integridad verificable", "12", "Media-alta (10–14)"],
            ["R5", "Acceso indebido a datos de usuarios", "10", "Media-alta (10–14)"],
            ["R6", "Captura o retención excesiva", "6", "Media (5–9)"],
            ["R7", "Pérdida de lecturas al reconectar", "20", "Alta (15–25)"],
            ["R8", "Deriva de la sonda", "9", "Media (5–9)"],
        ],
    )

    add_h(doc, "4.2 EMV y Risk Owners", 2)
    add_p(doc, "EMV = (P% / 100) × Impacto en USD. La reserva de contingencia es la suma de EMV.", size=10)
    add_table(
        doc,
        ["Cód.", "Risk Owner", "P %", "Impacto USD", "EMV USD", "Estrategia"],
        [
            ["R1", "Freddy Guaman", "55", "700", "385,00", "Mitigar"],
            ["R2", "M. Jiménez", "20", "950", "190,00", "Escalar"],
            ["R3", "Freddy Guaman", "45", "450", "202,50", "Mitigar"],
            ["R4", "Franco Quezada", "35", "800", "280,00", "Evitar"],
            ["R5", "M. Jiménez", "15", "1.200", "180,00", "Mitigar"],
            ["R6", "Freddy Guaman", "25", "500", "125,00", "Evitar"],
            ["R7", "Franco Quezada", "60", "1.000", "600,00", "Mitigar"],
            ["R8", "Franco Quezada", "40", "350", "140,00", "Transferir"],
            ["Σ", "—", "—", "—", "2.102,50", "Reserva"],
        ],
    )
    add_p(doc, "Prioridad por dinero en riesgo: R7 (600) y R1 (385).", bold=True, size=10)

    add_h(doc, "4.3 Línea base de costo", 2)
    add_p(doc, "Fórmula: Costo directo EDT + Reserva de contingencia (EMV) = Línea base de costo.", size=10)
    add_table(
        doc,
        ["Componente", "USD"],
        [
            ["1.1 Gestión y gobernanza", "900"],
            ["1.2 Cumplimiento y requisitos", "800"],
            ["1.3 Nodo IoT", "1.600"],
            ["1.4 Plataforma del regente", "1.500"],
            ["1.5 Seguridad e integridad", "700"],
            ["1.6 Piloto", "500"],
            ["Costo directo EDT", "6.000"],
            ["Reserva contingencia (Σ EMV)", "2.102,50"],
            ["LÍNEA BASE DE COSTO", "8.102,50"],
        ],
    )

    # ============================================================
    add_h(doc, "Anexo. Repositorio", 1)
    add_table(
        doc,
        ["Archivo", "Contenido"],
        [
            ["docs/Dossier_Ejecutivo_GA15_FaseI_RfP.docx", "Este dossier"],
            ["docs/Plan_Gestion_Riesgos_referencia.docx", "Plan de riesgos ampliado"],
            ["diagrams/EDT_WBS_FaseI.drawio", "EDT editable"],
            ["schedule/Cronograma_CPM_FaseI.gan", "Gantt editable"],
            ["schedule/Cronograma_CPM_FaseI.pdf", "Gantt PDF + holguras"],
            ["slides/Defensa_Ejecutiva_GA15_RfP.pdf", "7 láminas de defensa"],
        ],
    )
    add_p(doc, REPO_URL, size=9)

    add_h(doc, "Referencias", 1)
    for r in [
        "ARCSA. (2026). IE-B.3.4.2-EST-01, v5.0, anexo 2.",
        "Asamblea Nacional del Ecuador. (2021). LOPDP.",
        "Mitchell, R. K., Agle, B. R., & Wood, D. J. (1997). Stakeholder identification and salience. AMR, 22(4).",
        "PMI. (2021). PMBOK Guide (7.ª ed.).",
        "Wallace, L., & Keil, M. (2004). Software project risks. CACM, 47(4).",
    ]:
        add_p(doc, r, size=8, space_after=2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    build()
