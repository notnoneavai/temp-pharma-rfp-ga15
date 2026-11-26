# -*- coding: utf-8 -*-
"""Genera el Dossier Ejecutivo GA-1.5 (Fase I / RfP) desde la plantilla UIDE."""
from __future__ import annotations

import copy
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

MAROON = RGBColor(0x80, 0x00, 0x40)


def clear_body(doc: Document) -> None:
    body = doc.element.body
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)


def set_run(run, *, bold=False, size=11, color=None, italic=False):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), "Calibri")
    rFonts.set(qn("w:hAnsi"), "Calibri")
    if color is not None:
        run.font.color.rgb = color


def add_p(
    doc,
    text="",
    *,
    style=None,
    bold=False,
    size=11,
    align=None,
    color=None,
    italic=False,
    space_after=6,
    space_before=0,
):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    if text:
        run = p.add_run(text)
        set_run(run, bold=bold, size=size, color=color, italic=italic)
    return p


def add_h(doc, text, level=1):
    style = f"Heading {level}"
    p = add_p(doc, text, style=style, bold=True, size=14 if level == 1 else 12, space_before=12, space_after=8)
    for run in p.runs:
        set_run(run, bold=True, size=14 if level == 1 else 12, color=MAROON)
    return p


def shade_cell(cell, hex_color: str):
    tc = cell._teProp if False else cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_text(cell, text, *, bold=False, size=9, center=False):
    cell.text = ""
    p = cell.paragraphs[0]
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run(run, bold=bold, size=size)


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True, size=9, center=True)
        shade_cell(table.rows[0].cells[i], "800040")
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            set_cell_text(table.rows[r_i + 1].cells[c_i], str(val), size=9)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)
    add_p(doc, "", space_after=4)
    return table


def build():
    doc = Document(str(TEMPLATE))
    clear_body(doc)

    # ---- Portada ----
    add_p(
        doc,
        "UNIVERSIDAD INTERNACIONAL DEL ECUADOR (UIDE)",
        bold=True,
        size=14,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        color=MAROON,
        space_after=2,
    )
    add_p(
        doc,
        "Escuela de Ciencias de la Computación · Asignatura: Gestión de Proyectos de TI",
        size=10,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    add_p(
        doc,
        "Docente: Ing. Daniel Alexander Patiño Vásquez",
        size=10,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=10,
    )
    add_p(
        doc,
        "DOSSIER EJECUTIVO — BUZÓN HABILITANTE GA-1.5",
        bold=True,
        size=13,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        color=MAROON,
        space_after=4,
    )
    add_p(
        doc,
        "Evidencia Técnica de Respaldo para la Evaluación Práctica\nCompuerta Ready for Planning (RfP) — Fase I del Proyecto Integrador",
        size=11,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=10,
    )
    add_p(
        doc,
        "Proyecto corporativo",
        bold=True,
        size=11,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    add_p(
        doc,
        "Registro automático y auditable de temperatura para farmacias",
        bold=True,
        size=14,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        color=MAROON,
        space_after=12,
    )

    add_table(
        doc,
        ["Integrante", "Rol formal", "Responsabilidad RfP"],
        [
            [
                "Madeleine Yanhely Jiménez Gaona",
                "Project Manager (PM)",
                "Gobernanza, cronograma CPM, presupuesto base y reserva",
            ],
            [
                "Freddy Emanuel Guaman Gonzalez",
                "Product Owner (PO)",
                "Business Case, alcance, criterios de aceptación y valor",
            ],
            [
                "Franco Rene Quezada Ordoñez",
                "Arquitecto de Software / Risk Manager",
                "EDT técnica, riesgos cuantitativos EMV e integridad",
            ],
        ],
        col_widths=[6.5, 5.0, 6.0],
    )

    add_p(doc, "Modalidad: Equipos Consultores (Grupal) · Paralelo: Gestión de Proyectos de TI", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc, "Fecha de entrega documental: 26 de noviembre de 2026", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p(doc, f"Repositorio oficial (privado): {REPO_URL}", size=10, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    add_p(
        doc,
        "Ponderación del buzón: 0,00 pts (formativo). La sustentación y nota se asientan en GA-1.5 (4,00 pts).",
        size=9,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        italic=True,
        space_after=14,
    )

    # ============================================================
    add_h(doc, "Capítulo 1. Marco de Iniciación y Gobernanza", 1)

    add_h(doc, "1.1 Justificación del Business Case", 2)
    add_p(
        doc,
        "Problema. La guía técnica ARCSA IE-B.3.4.2-EST-01 (versión 5.0, anexo 2) exige controles de almacenamiento "
        "en establecimientos farmacéuticos, incluido el registro de temperatura. En farmacias independientes el "
        "registro manual dos veces al día deja sin evidencia las excursiones nocturnas y de fin de semana, elevando "
        "el riesgo de sanción, merma de cadena de frío y pérdida de confianza del regente ante inspección.",
    )
    add_p(
        doc,
        "Propuesta de valor. Un registro continuo, con alerta fuera de rango, reporte de incidente automático e "
        "historial no alterable, convierte la bitácora en evidencia auditable. El pagador es la farmacia; el "
        "usuario operativo es el regente/operador de turno.",
    )
    add_p(
        doc,
        "Viabilidad técnica. Factibilidad alta: sondas de temperatura de bajo costo, almacenamiento local ante "
        "caída de Wi-Fi, plataforma web para visualización/exportación y controles de integridad contrastables "
        "con ARCSA y LOPDP. Existen registradores comerciales; la defensa competitiva es el costo de suscripción "
        "para farmacias pequeñas y la matriz explícita contra requisitos regulatorios.",
    )
    add_p(doc, "Viabilidad financiera (piloto Fase I — supuestos del equipo consultor)", bold=True, size=11)

    add_table(
        doc,
        ["Concepto", "Valor", "Base de cálculo"],
        [
            ["Inversión inicial (CAPEX + desarrollo piloto)", "USD 6.000", "Presupuesto base aprobado del equipo"],
            ["Suscripción objetivo (farmacia independiente)", "USD 29 / mes", "Comparación vs. registrador comercial"],
            ["Clientes piloto Año 1 (conservador)", "18 farmacias", "Adopción gradual post-piloto"],
            ["Ingreso anual estimado Año 1", "USD 6.264", "18 × 29 × 12"],
            ["Costo operativo anual estimado Año 1", "USD 2.400", "Hosting, soporte, calibración puntual"],
            ["Beneficio neto Año 1", "USD 3.864", "Ingresos − OPEX"],
            ["Payback simple estimado", "≈ 18,6 meses", "6.000 / (3.864/12)"],
            ["ROI Año 1 (sobre inversión)", "64,4 %", "3.864 / 6.000"],
            ["NPV (3 años, r=12 %)", "≈ USD 2.910", "Flujos 3,9k / 5,2k / 6,5k descontados − 6.000"],
        ],
    )
    add_p(
        doc,
        "Lectura de decisión. El payback inferior a 24 meses y el NPV positivo a tasa del 12 % justifican "
        "avanzar a la compuerta RfP. El valor evitado de una sanción o de un lote comprometido refuerza el caso "
        "frente a la alternativa de no hacer nada. Las cifras son estimaciones de planificación y se validarán "
        "con cotizaciones y tracción comercial en Fase II.",
        space_after=10,
    )

    add_h(doc, "1.2 Project Charter (completo)", 2)
    add_p(doc, "Nombre del proyecto: Registro automático y auditable de temperatura para farmacias.", bold=True)
    add_p(doc, "Patrocinador académico / Project Owner de aula: Ing. Daniel Alexander Patiño Vásquez.")
    add_p(doc, "Project Manager: Madeleine Yanhely Jiménez Gaona.  Product Owner: Freddy Emanuel Guaman Gonzalez.")
    add_p(doc, "Arquitecto de Software / Risk Manager: Franco Rene Quezada Ordoñez.")

    add_p(doc, "Objetivos SMART", bold=True)
    add_table(
        doc,
        ["ID", "Objetivo SMART"],
        [
            [
                "O1",
                "Específico: Entregar el dossier RfP y la línea base de alcance/tiempo/costo/riesgo del piloto de registro continuo de temperatura.",
            ],
            [
                "O2",
                "Medible: Completar EDT a 3 niveles, ≥6 paquetes terminales con criterios de aceptación, CPM con ruta crítica y matriz 5×5 con 8 riesgos + EMV.",
            ],
            [
                "O3",
                "Alcanzable: Usar stack conocido del equipo (sonda + almacenamiento local + plataforma web) y presupuesto techo USD 6.000 + reserva EMV.",
            ],
            [
                "O4",
                "Relevante: Responder al gap de evidencia ante inspección ARCSA en farmacias pequeñas frente al registro manual.",
            ],
            [
                "O5",
                "Temporal: Cerrar evidencia documental del buzón habilitante el 26/11/2026 23:59, previo a la Sesión 2 de defensa.",
            ],
        ],
    )

    add_p(doc, "Premisas", bold=True)
    for t in [
        "La farmacia piloto facilita acceso a una refrigeradora real durante las pruebas acordadas.",
        "El rango de almacenamiento y la frecuencia de reporte se alinean a la guía ARCSA vigente citada en referencias.",
        "El equipo mantiene repositorio GitHub con trazabilidad de commits de los tres integrantes.",
        "La Fase I se limita a planificación RfP y definición del piloto; no incluye despliegue masivo comercial.",
    ]:
        add_p(doc, f"• {t}", size=10, space_after=2)

    add_p(doc, "Restricciones", bold=True, space_before=6)
    for t in [
        "Presupuesto base de costo directo: USD 6.000 (techo de la línea base antes de contingencia).",
        "Plazo duro de evidencia documental: 26/11/2026 23:59.",
        "Alcance estricto Fase I: gobernanza, EDT, CPM, riesgos cuantitativos y presupuesto; sin PDF de defensa en este buzón aún.",
        "Cumplimiento LOPDP: no capturar datos de pacientes; solo telemetría de equipos y trazas de operadores autorizados.",
    ]:
        add_p(doc, f"• {t}", size=10, space_after=2)

    add_p(doc, "Límites estrictos de alcance (In / Out)", bold=True, space_before=6)
    add_table(
        doc,
        ["Incluye (IN)", "Excluye (OUT)"],
        [
            [
                "Planificación RfP, EDT/WBS, CPM, riesgos EMV, presupuesto base del piloto",
                "Certificación formal ARCSA del producto final",
            ],
            [
                "Diseño del nodo con sonda, alertas y buffer offline",
                "Integración con ERP farmacéutico de terceros",
            ],
            [
                "Plataforma para que el regente vea equipos y descargue reporte de incidente",
                "App móvil nativa multiplataforma en Fase I",
            ],
            [
                "Controles de integridad/no alteración del historial",
                "Comercialización nacional y facturación electrónica",
            ],
        ],
    )

    add_p(doc, "Presupuesto base (Charter)", bold=True)
    add_p(
        doc,
        "Costo directo EDT: USD 6.000. Reserva de contingencia (suma EMV): USD 2.102,50. "
        "Línea base de costo = 6.000 + 2.102,50 = USD 8.102,50. Reserva de gestión (fuera de línea base): a discreción del Project Owner académico ante riesgos desconocidos.",
        space_after=10,
    )

    add_h(doc, "1.3 Matriz de interesados — Mitchell, Agle y Wood (1997)", 2)
    add_p(
        doc,
        "Clasificación por posesión de poder, legitimidad y urgencia. Tipología: latente (1 atributo), expectante (2) o definitiva (3).",
    )
    add_table(
        doc,
        ["Interesado", "Poder", "Legitimidad", "Urgencia", "Tipología", "Estrategia"],
        [
            ["Regente de farmacia piloto", "Alto", "Sí", "Alta", "Definitivo", "Gestionar de cerca; co-diseñar umbrales y reporte"],
            ["Propietario / admin. farmacia", "Alto", "Sí", "Media", "Expectante dominante", "Mantener satisfecho; justificar ROI y riesgo de sanción"],
            ["Inspector ARCSA (contexto)", "Alto", "Sí", "Baja*", "Expectante dominante", "Diseñar evidencia auditable; no lobby operativo"],
            ["Docente / Project Owner aula", "Alto", "Sí", "Alta", "Definitivo", "Cumplir rúbrica GA-1.5 y hitos de defensa"],
            ["Equipo consultor (PM/PO/Arch)", "Medio", "Sí", "Alta", "Expectante dependiente", "Coordinación diaria; commits equitativos"],
            ["Operador de turno", "Bajo", "Sí", "Alta", "Expectante dependiente", "Informar; UX de alertas simple"],
            ["Proveedor de sondas", "Medio", "Sí", "Media", "Expectante dominante", "Contrato de calibración/garantía (R8)"],
            ["Pacientes (indirectos)", "Bajo", "Sí", "Baja", "Latente discrecional", "Monitorear; cero datos clínicos en el sistema"],
        ],
    )
    add_p(
        doc,
        "*La urgencia del inspector es baja en el día a día del piloto, pero se torna alta ante una visita; el diseño asume esa latencia.",
        size=9,
        italic=True,
        space_after=10,
    )

    # ============================================================
    add_h(doc, "Capítulo 2. Ingeniería del Alcance (EDT/WBS)", 1)
    add_h(doc, "2.1 Diagrama EDT a 3 niveles (regla del 100 %)", 2)
    add_p(
        doc,
        "La EDT se organiza por entregables. El archivo vectorial editable está en diagrams/EDT_WBS_FaseI.drawio "
        "(compatible con diagrams.net). Cumple la regla del 100 %: la suma de los componentes hijos equivale al padre.",
    )
    add_p(doc, "Estructura jerárquica", bold=True)
    wbs_lines = [
        "1. Proyecto — Registro automático y auditable de temperatura para farmacias",
        "   1.1 Gestión y gobernanza del proyecto",
        "      1.1.1 Kickoff, Charter y Business Case",
        "      1.1.2 Plan RfP (alcance, tiempo, costo, riesgo)",
        "      1.1.3 Control integrado y cierre documental Fase I",
        "   1.2 Cumplimiento ARCSA y requisitos",
        "      1.2.1 Matriz de requisitos vs. guía ARCSA",
        "      1.2.2 Especificación funcional del registro y alertas",
        "      1.2.3 Criterios de aceptación del reporte de inspección",
        "   1.3 Nodo IoT de temperatura",
        "      1.3.1 Integración de sonda y muestreo continuo",
        "      1.3.2 Buffer local offline ante pérdida de Wi-Fi",
        "      1.3.3 Motor de alertas fuera de rango",
        "   1.4 Plataforma del regente",
        "      1.4.1 API e identidad de operadores",
        "      1.4.2 Tablero de equipos y series temporales",
        "      1.4.3 Exportación de reporte de incidente inalterable",
        "   1.5 Seguridad, auditoría e integridad",
        "      1.5.1 Modelo de no alteración / hash de lecturas",
        "      1.5.2 Controles de acceso y minimización LOPDP",
        "   1.6 Piloto en refrigeradora real",
        "      1.6.1 Protocolo de prueba con regente",
        "      1.6.2 Ensayo de corte Wi-Fi y reconciliación",
        "      1.6.3 Informe de validación y decisión RfP → ejecución",
    ]
    for line in wbs_lines:
        add_p(doc, line, size=9, space_after=1)

    add_h(doc, "2.2 Diccionario de la EDT (paquetes terminales)", 2)
    add_p(
        doc,
        "Se documentan ocho paquetes terminales representativos. Duraciones estimadas respetan la regla 8/80 "
        "(entre 8 y 80 horas de esfuerzo). Criterios de aceptación inequívocos y verificables.",
    )
    add_table(
        doc,
        ["ID", "Paquete", "Descripción", "Esfuerzo", "Criterios de aceptación", "Owner"],
        [
            [
                "1.1.2",
                "Plan RfP",
                "Consolidar líneas base de alcance, tiempo, costo y riesgo para la compuerta.",
                "40 h",
                "Dossier aprobado por PM/PO/Arch; EDT, CPM y EMV publicados en el repo.",
                "M. Jiménez",
            ],
            [
                "1.2.1",
                "Matriz ARCSA",
                "Trazar requisitos de registro/alerta/evidencia frente a la guía vigente.",
                "24 h",
                "≥95 % de controles aplicables mapeados; gaps listados con dueño y fecha.",
                "F. Guaman",
            ],
            [
                "1.3.2",
                "Buffer offline",
                "Persistir lecturas localmente y resincronizar sin pérdida ni duplicados.",
                "56 h",
                "Ensayo 2 h sin Wi-Fi: 0 lecturas perdidas; reconciliación por ID OK.",
                "F. Quezada",
            ],
            [
                "1.3.3",
                "Alertas umbral",
                "Notificar cuando la refrigeradora sale de rango configurado.",
                "32 h",
                "Alerta en ≤60 s tras excursión simulada; acuse registrable por turno.",
                "F. Quezada",
            ],
            [
                "1.4.3",
                "Reporte incidente",
                "Generar PDF/exportación para inspección sin edición de lecturas crudas.",
                "40 h",
                "Exportación incluye sello temporal, equipo, umbral y hash; edición bloqueada.",
                "F. Guaman",
            ],
            [
                "1.5.1",
                "Integridad",
                "Impedir sobrescritura silenciosa del historial de temperatura.",
                "48 h",
                "Prueba de alteración falla verificación; auditoría conserva original.",
                "F. Quezada",
            ],
            [
                "1.6.1",
                "Protocolo piloto",
                "Definir y ejecutar prueba en refrigeradora real con el regente.",
                "24 h",
                "Acta firmada con umbrales, turnos y resultado pass/fail del día de prueba.",
                "F. Guaman",
            ],
            [
                "1.6.2",
                "Ensayo Wi-Fi",
                "Validar continuidad del registro ante corte de red.",
                "16 h",
                "Bitácora completa post-corte; sin huecos ni duplicados tras sync.",
                "F. Quezada",
            ],
        ],
    )

    # ============================================================
    add_h(doc, "Capítulo 3. Ingeniería de Tiempo y Redes Críticas (CPM)", 1)
    add_h(doc, "3.1 Matriz de precedencias lógicas", 2)
    add_p(
        doc,
        "Relaciones Finish-to-Start (FS). Duraciones en días hábiles. Archivo fuente editable: schedule/Cronograma_CPM_FaseI.gan (GanttProject).",
    )
    add_table(
        doc,
        ["ID", "Actividad", "Dur. (días)", "Predecesoras", "Sucesoras"],
        [
            ["A", "Kickoff y Charter", "3", "—", "B, C"],
            ["B", "Business Case y presupuesto", "4", "A", "E"],
            ["C", "Matriz ARCSA / requisitos", "5", "A", "D, F"],
            ["D", "EDT + diccionario de paquetes", "4", "C", "E, G"],
            ["E", "Cronograma CPM y ruta crítica", "3", "B, D", "I"],
            ["F", "Diseño nodo IoT + offline", "6", "C", "H"],
            ["G", "Diseño plataforma y reporte", "5", "D", "H"],
            ["H", "Modelo de integridad y accesos", "4", "F, G", "J"],
            ["I", "Matriz de riesgos 5×5 + EMV", "3", "E", "K"],
            ["J", "Protocolo piloto refrigeradora", "3", "H", "K"],
            ["K", "Ensayo Wi-Fi y reconciliación", "2", "I, J", "L"],
            ["L", "Cierre RfP y empaquetado dossier", "2", "K", "—"],
        ],
    )

    add_h(doc, "3.2 Diagrama de red, ruta crítica y holguras", 2)
    add_p(
        doc,
        "Ruta crítica (holgura total = 0), marcada en rojo en el archivo GanttProject: "
        "A → C → D → G → H → J → K → L. Duración del camino crítico: 3+5+4+5+4+3+2+2 = 28 días hábiles.",
        space_after=4,
    )
    add_table(
        doc,
        ["ID", "ES", "EF", "LS", "LF", "Holgura total", "¿Crítica?"],
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
        "Nota de entrega. En este buzón se entrega el fuente .gan editable. La exportación PDF del Gantt con "
        "ruta crítica en rojo se generará desde GanttProject para la defensa oral (GA-1.5), según acuerdo del equipo.",
        size=9,
        italic=True,
        space_after=10,
    )

    # ============================================================
    add_h(doc, "Capítulo 4. Gestión Cuantitativa de Riesgos y Presupuesto Base", 1)
    add_h(doc, "4.1 Matriz de riesgos 5×5 (software)", 2)
    add_p(
        doc,
        "Severidad = P × I (escala 1–5). Zonas: Verde 1–4, Amarillo 5–9, Naranja 10–14, Rojo 15–25. "
        "Taxonomía adaptada de Wallace y Keil (2004). Detalle ampliado en docs/Plan_Gestion_Riesgos_referencia.docx.",
    )
    add_table(
        doc,
        ["Cód.", "Dimensión", "Riesgo de software", "P×I", "Zona"],
        [
            ["R1", "Mandato del cliente", "Alertas desatendidas", "16", "Rojo"],
            ["R2", "Mandato del cliente", "Retiro de la farmacia piloto", "10", "Naranja"],
            ["R3", "Requerimientos", "Umbrales o reporte mal definidos", "9", "Amarillo"],
            ["R4", "Requerimientos", "Evidencia sin integridad verificable", "12", "Naranja"],
            ["R5", "Entorno regulatorio (LOPDP)", "Acceso indebido a datos de usuarios", "10", "Naranja"],
            ["R6", "Entorno regulatorio (LOPDP)", "Captura o retención excesiva", "6", "Amarillo"],
            ["R7", "Ejecución / equipo", "Pérdida de lecturas al reconectar", "20", "Rojo"],
            ["R8", "Ejecución / equipo", "Deriva de la sonda", "9", "Amarillo"],
        ],
    )

    add_h(doc, "4.2 Risk Owners, impacto financiero y EMV", 2)
    add_p(doc, "EMV = (P% / 100) × Impacto (USD). Reserva de contingencia = Σ EMV.")
    add_table(
        doc,
        ["Cód.", "Risk Owner", "P %", "Impacto (USD)", "EMV (USD)", "Estrategia"],
        [
            ["R1", "Freddy Guaman", "55 %", "700", "385,00", "Mitigar"],
            ["R2", "M. Jiménez", "20 %", "950", "190,00", "Escalar"],
            ["R3", "Freddy Guaman", "45 %", "450", "202,50", "Mitigar"],
            ["R4", "Franco Quezada", "35 %", "800", "280,00", "Evitar"],
            ["R5", "M. Jiménez", "15 %", "1.200", "180,00", "Mitigar"],
            ["R6", "Freddy Guaman", "25 %", "500", "125,00", "Evitar"],
            ["R7", "Franco Quezada", "60 %", "1.000", "600,00", "Mitigar"],
            ["R8", "Franco Quezada", "40 %", "350", "140,00", "Transferir"],
            ["Σ", "—", "—", "—", "2.102,50", "Reserva contingencia"],
        ],
    )

    add_h(doc, "4.3 Presupuesto estructurado y línea base de costo", 2)
    add_table(
        doc,
        ["Componente", "Monto (USD)", "Notas"],
        [
            ["1.1 Gestión y gobernanza", "900", "Planificación, control, cierre RfP"],
            ["1.2 Cumplimiento y requisitos", "800", "Matriz ARCSA y especificación"],
            ["1.3 Nodo IoT / sensórica", "1.600", "Sonda, MCU, offline, alertas"],
            ["1.4 Plataforma del regente", "1.500", "API, tablero, exportación"],
            ["1.5 Seguridad e integridad", "700", "Hash, accesos, minimización datos"],
            ["1.6 Piloto refrigeradora real", "500", "Pruebas, actas, ajustes"],
            ["Costo directo EDT (línea base de alcance)", "6.000", "Techo Charter"],
            ["Reserva de contingencia (Σ EMV)", "2.102,50", "Riesgos identificados"],
            ["LÍNEA BASE DE COSTO", "8.102,50", "Costo directo + contingencia"],
        ],
    )
    add_p(
        doc,
        "Fórmula oficial del dossier: Costo directo de la EDT + Reserva de Contingencia (EMV) = Línea Base de Costo. "
        "Prioridad de acción por EMV: R7 (600) y R1 (385).",
        space_after=10,
    )

    # ============================================================
    add_h(doc, "Anexo A. Estructura del repositorio GitHub", 1)
    add_p(doc, f"URL: {REPO_URL} (repositorio privado del equipo consultor).")
    add_table(
        doc,
        ["Ruta", "Contenido"],
        [
            ["docs/Dossier_Ejecutivo_GA15_FaseI_RfP.docx", "Dossier ejecutivo formal (este documento)"],
            ["docs/Plan_Gestion_Riesgos_referencia.docx", "Plan de riesgos detallado de respaldo"],
            ["diagrams/EDT_WBS_FaseI.drawio", "EDT vectorial editable (3 niveles)"],
            ["schedule/Cronograma_CPM_FaseI.gan", "Cronograma CPM editable (GanttProject)"],
            ["slides/", "Carpeta reservada para diapositivas de defensa (máx. 7 láminas)"],
            ["assets/logo_uide.jpeg", "Logotipo institucional UIDE"],
            ["README.md", "Instrucciones de navegación y roles"],
        ],
    )
    add_p(
        doc,
        "Trazabilidad. El historial de commits del repositorio refleja aportes de Madeleine Jiménez (PM), "
        "Freddy Guaman (PO) y Franco Quezada (Arquitecto / Risk Manager).",
        space_after=10,
    )

    add_h(doc, "Referencias (APA 7.ª ed.)", 1)
    refs = [
        "Agencia Nacional de Regulación, Control y Vigilancia Sanitaria. (2026). Regulación, control y vigilancia sanitaria de farmacias y botiquines privados (IE-B.3.4.2-EST-01, versión 5.0, anexo 2). https://www.controlsanitario.gob.ec/",
        "Asamblea Nacional del Ecuador. (2021). Ley Orgánica de Protección de Datos Personales. Registro Oficial, Suplemento 459.",
        "Flyvbjerg, B., & Budzier, A. (2011). Why your IT project may be riskier than you think. Harvard Business Review, 89(9), 23–25.",
        "Mitchell, R. K., Agle, B. R., & Wood, D. J. (1997). Toward a theory of stakeholder identification and salience. Academy of Management Review, 22(4), 853–886.",
        "Project Management Institute. (2021). A guide to the project management body of knowledge (PMBOK® guide) (7.ª ed.). PMI.",
        "Wallace, L., & Keil, M. (2004). Software project risks and their effect on outcomes. Communications of the ACM, 47(4), 68–73.",
    ]
    for r in refs:
        add_p(doc, r, size=9, space_after=4)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    build()
