"""Construye el Word editable del dossier GA-1.5."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.shared import Cm, Pt, RGBColor

from build_gan import ACTIVITIES, START, activity_code, add_business_days, cpm_rows, successors
from rfp_data import AR, ARCSA, BASE, DIRECT, EMV_CENTS, FLOW, NPV, PACKAGES, PACKAGE_NAMES, PAYBACK
from rfp_data import PM, PO, PROJECT, REPO, RISKS, ROOT, TEAM, WBS, levels, money

OUTPUT = ROOT / "docs" / "Dossier_Ejecutivo_GA15_FaseI_RfP.docx"


def xml(tag, **attributes):
    element = OxmlElement(f"w:{tag}")
    for key, value in attributes.items():
        element.set(qn(f"w:{key}"), str(value))
    return element


def link(paragraph, text, url):
    relationship = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = xml("hyperlink")
    hyperlink.set(qn("r:id"), relationship)
    run = xml("r")
    properties = xml("rPr")
    properties.append(xml("color", val="373737"))
    properties.append(xml("u", val="single"))
    run.append(properties)
    value = xml("t")
    value.text = text
    run.append(value)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def setup():
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.54)
    section.left_margin = section.right_margin = Cm(2.54)
    section.header_distance = section.footer_distance = Cm(1.27)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(9)
    for name, size in (("Title", 27), ("Heading 1", 19), ("Heading 2", 13), ("Heading 3", 11)):
        style = doc.styles[name]
        style.font.name, style.font.size = "Calibri", Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.keep_with_next = True
        for border in style.element.xpath("./w:pPr/w:pBdr"):
            border.getparent().remove(border)
    for name, size in (("Cuadro", 9.5), ("Nota de figura", 9.5), ("Referencia APA", 11)):
        style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = normal
        style.font.size = Pt(size)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(3)
    ref = doc.styles["Referencia APA"].paragraph_format
    ref.left_indent, ref.first_line_indent = Cm(1.27), Cm(-1.27)
    ref.line_spacing, ref.space_after = 2, Pt(0)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.style = "Cuadro"
    footer.add_run("UIDE   |   GA-1.5   |   ")
    footer._p.append(xml("fldSimple", instr="PAGE"))
    doc.core_properties.title = f"Dossier ejecutivo GA-1.5 · {PROJECT}"
    doc.core_properties.author = "Equipo consultor GA-1.5"
    return doc


def paragraph(doc, value, style=None):
    return doc.add_paragraph(value, style)


def opening(doc, heading, subtitle=None):
    title = doc.add_heading(heading, 1)
    title.paragraph_format.page_break_before = True
    if subtitle:
        doc.add_heading(subtitle, 2)


def sub(doc, value):
    doc.add_heading(value, 2)


def table(doc, headers, rows, widths, *, caption=None):
    if caption:
        number, title = caption
        p = paragraph(doc, f"Tabla {number}", "Heading 3")
        p.paragraph_format.keep_with_next = True
        p = paragraph(doc, title, "Nota de figura")
        p.runs[0].italic = True
        p.paragraph_format.keep_with_next = True
    tbl = doc.add_table(rows=0, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.autofit = False
    for col, width in zip(tbl.columns, widths):
        col.width = Cm(width)
    for i, values in enumerate((headers, *rows)):
        row = tbl.add_row()
        props = row._tr.get_or_add_trPr()
        props.append(xml("cantSplit"))
        if i == 0:
            props.append(xml("tblHeader"))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Cm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if i % 2 == 0:
                cell._tc.get_or_add_tcPr().append(xml("shd", fill="DFDFDF" if i == 0 else "F3F3F3"))
            p = cell.paragraphs[0]
            p.style = "Cuadro"
            p.paragraph_format.space_before = Pt(3)
            run = p.add_run(str(value))
            run.bold = i == 0
    return tbl


def figure(doc, number, caption, image, note, width=15.82):
    p = paragraph(doc, f"Figura {number}", "Heading 3")
    p.paragraph_format.keep_with_next = True
    p = paragraph(doc, caption, "Nota de figura")
    p.runs[0].italic = True
    p.paragraph_format.keep_with_next = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image), width=Cm(width))
    paragraph(doc, note, "Nota de figura")


def cover(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(ROOT / "assets" / "logo_uide.jpeg"), width=Cm(7))
    p = paragraph(doc, "UNIVERSIDAD INTERNACIONAL DEL ECUADOR\nEscuela de Ciencias de la Computación\nGestión de Proyectos de TI")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = paragraph(doc, "Dossier ejecutivo GA-1.5", "Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = paragraph(doc, PROJECT, "Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = paragraph(doc, "Fase I · Ready for Planning (RfP)\nDocente Ing. Daniel Alexander Patiño Vásquez\nSin paralelo asignado · 26 de noviembre de 2026")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table(doc, ("Integrante", "Rol"), TEAM, (8.5, 7.3))
    p = paragraph(doc, "Repositorio oficial del equipo")
    p.paragraph_format.space_before = Pt(15)
    link(doc.add_paragraph(), REPO, REPO)


def summary(doc):
    opening(doc, "Resumen ejecutivo")
    paragraph(doc, "Solicitamos aprobar la compuerta Ready for Planning para una solución de registro de temperatura dirigida a farmacias independientes. La Fase I entrega el caso de negocio, el diseño de alcance, el cronograma, el presupuesto y los criterios de aceptación para preparar un piloto posterior.")
    paragraph(doc, "El sistema propuesto conserva lecturas durante cortes de Wi-Fi, alerta excursiones respecto al rango del producto y permite al regente exportar el registro diario y los incidentes. El historial de solo anexado y su verificación permiten detectar alteraciones.")
    paragraph(doc, f"La duración modelada es de 28 días de lunes a viernes. La línea base propuesta es de USD {money(BASE)}, incluidos USD {money(EMV_CENTS/100)} de contingencia. La decisión requiere revisar el diseño con el regente y validar los supuestos de costos y adopción.")
    sub(doc, "Contenido")
    table(doc, ("Sección", "Pág."), (("Marco de iniciación y gobernanza", 3), ("Ingeniería del alcance", 6),
          ("Ingeniería de tiempo y redes críticas", 9), ("Riesgos y presupuesto base", 12),
          ("Expediente y criterio de entrega", 15), ("Referencias", 16)), (13, 2.8))


def initiation(doc):
    opening(doc, "Capítulo 1. Iniciación y gobernanza", "1.1 Caso de negocio y viabilidad")
    paragraph(doc, "El anexo 2, apartado 5.3, de la guía para farmacias privadas pide un registro diario del control de temperatura de la refrigeradora (Agencia Nacional de Regulación, Control y Vigilancia Sanitaria [ARCSA], 2026). Las anotaciones puntuales pueden dejar excursiones entre lecturas sin detectar. El monitoreo continuo propuesto amplía esa cobertura, con parámetros por producto confirmados por el regente.")
    paragraph(doc, "La viabilidad técnica supone una sonda contrastada con un instrumento de referencia, una cola local con reconciliación por ID, acceso por rol y una bitácora de solo anexado. El piloto comprobará esos controles con una sola refrigeradora y datos sintéticos de usuarios de prueba.")
    table(doc, ("Supuesto financiero", "Cálculo o valor"), (
        ("Inversión inicial con reserva", f"USD {money(BASE)} en t = 0"),
        ("Ingreso anual por suscripción", "18 farmacias × USD 29 × 12 = USD 6.264"),
        ("OPEX anual", "USD 2.400 para hosting, soporte y calibración"),
        ("Flujo anual (años 1, 2 y 3)", f"USD {money(FLOW)} al cierre de cada año"),
        ("Recuperación simple", f"{PAYBACK:.1f} meses".replace(".", ",") + " con flujo mensual constante"),
        ("VAN a 3 años, tasa del 12 %", f"USD {money(NPV)}")), (8, 7.8),
        caption=(1, "Supuestos y resultados del escenario financiero"))
    paragraph(doc, "VAN = –8.102,50 + Σ [3.864 ÷ (1,12)^t], para t de 1 a 3. La proyección supone 18 suscripciones durante todo el año y no incorpora valor residual. Cada alta menos resta USD 348 al flujo anual si el OPEX sigue igual.")
    paragraph(doc, "La decisión para RfP es avanzar con la planificación y contrastar la disposición a pagar, el costo de instalación y el OPEX antes de comprometer el despliegue.")

    opening(doc, "Capítulo 1. Iniciación y gobernanza", "1.2 Acta de constitución del proyecto")
    paragraph(doc, "Propósito. Preparar una propuesta auditable y económicamente defendible para el control de temperatura de una refrigeradora en una farmacia. La aceptación académica de la compuerta corresponde al tribunal. El regente valida los criterios de operación de la farmacia.")
    table(doc, ("Objetivo SMART", "Evidencia y fecha límite"), (
        ("O1. Consolidar cuatro líneas base trazables", "Dossier con EDT, cronograma, costos y riesgos listo para revisión interna el 25/11/2026."),
        ("O2. Modelar y comprobar planificación", "Tres niveles, ≥8 fichas, 12 actividades y 8 riesgos con EMV verificados para el 25/11/2026."),
        ("O3. Limitar el costo del alcance definido", "Costo directo de USD 6.000 y reserva EMV calculada antes del cierre interno del 25/11/2026."),
        ("O4. Definir condiciones de prueba del piloto", "Guion para una refrigeradora con pruebas de desconexión, alerta e integridad documentado el 25/11/2026."),
        ("O5. Entregar al tribunal el expediente digital", "PDF, fuentes y presentación entregables hasta el 26/11/2026 a las 23:59.")),
        (7.6, 8.2), caption=(2, "Objetivos SMART y evidencias"))
    sub(doc, "Premisas, restricciones y autoridad")
    paragraph(doc, "El regente facilitará acceso al equipo en la etapa piloto. El modelo usa días de lunes a viernes sin feriados y los precios quedan sujetos a cotizaciones. El diseño evita los datos de pacientes y limita los datos de operadores al mínimo necesario (Asamblea Nacional del Ecuador, 2021).")
    paragraph(doc, "Alcance incluido: planificación, diseños del nodo y la plataforma, controles, protocolo y ensayo de mesa. Exclusiones: instalación física en Fase I, producción comercial, certificación del producto, ERP y aplicación móvil.")
    paragraph(doc, "La PM coordina cambios y costos. El PO confirma alcance, reporte y evidencias con el regente. El arquitecto verifica factibilidad y riesgos. Los cambios de alcance, fecha base o presupuesto se elevan al Project Owner o tribunal según corresponda.")

    opening(doc, "Capítulo 1. Iniciación y gobernanza", "1.3 Interesados y saliencia")
    paragraph(doc, "La clasificación usa atributos presentes o ausentes en esta compuerta. Poder es la capacidad de influir en la decisión. Legitimidad es la relación reconocida con el proyecto. Urgencia combina importancia y sensibilidad al tiempo (Mitchell et al., 1997).")
    table(doc, ("Interesado", "P", "L", "U", "Tipo y atención prevista"), (
        ("Regente de la farmacia piloto", "Sí", "Sí", "Sí", "Definitivo. Valida criterios de seguridad y registro."),
        ("Representante de la farmacia", "Sí", "Sí", "No", "Dominante. Decide acceso y costo del piloto."),
        ("ARCSA / inspección", "Sí", "Sí", "No", "Dominante. En visita o incidente puede aumentar la urgencia."),
        ("Tribunal / docente", "Sí", "Sí", "Sí", "Definitivo. Decide la compuerta y sus condiciones."),
        ("Equipo consultor", "Sí", "Sí", "Sí", "Definitivo. Controla las entregas y los ajustes internos."),
        ("Operador de turno", "No", "Sí", "Sí", "Dependiente. Validar acuse, relevo y canal de respaldo."),
        ("Proveedor de sondas", "No", "Sí", "No", "Discrecional. Validar garantía y calibración."),
        ("Pacientes", "No", "Sí", "No", "Discrecional. Evitar captura de datos de pacientes.")),
        (5.3, 0.8, 0.8, 0.8, 8.1), caption=(3, "Matriz de saliencia de interesados"))
    sub(doc, "Seguimiento de decisiones")
    paragraph(doc, "La PM registra decisión, fecha, responsable y condición de cierre. El PO coordina con el regente la revisión del rango por producto y del reporte. El arquitecto presenta evidencias de diseño y escenarios de prueba. Una visita o incidente cambia la priorización y se registra en la reunión de avance.")


def scope(doc):
    opening(doc, "Capítulo 2. Ingeniería del alcance", "2.1 EDT a tres niveles")
    paragraph(doc, "El nivel 1 representa el expediente y los diseños de la Fase I. Las seis ramas del nivel 2 delimitan entregables de gestión, requisitos, nodo, plataforma, seguridad y preparación del piloto. El tercer nivel contiene 17 paquetes terminales.")
    figure(doc, 1, "Estructura de desglose del trabajo", ROOT/"diagrams"/"EDT_WBS_FaseI.png",
           "Nota. Elaboración propia. Fuente editable: diagrams/EDT_WBS_FaseI.drawio.")
    table(doc, ("Rama", "Verificación del 100 %"), (
        ("1.1 y 1.2", "Acta, plan y cierre cubren gobernanza. Matriz, especificación y reporte cubren requisitos."),
        ("1.3 y 1.4", "Muestreo, cola y alertas cubren el nodo. API, tablero y exportación cubren la interfaz."),
        ("1.5 y 1.6", "Integridad y acceso cubren seguridad. Protocolo, simulación e informe cubren preparación.")),
        (3, 12.8), caption=(4, "Cobertura de los entregables de segundo nivel"))
    paragraph(doc, "Los requisitos describen qué se debe cumplir. Los diseños describen cómo cumplirlo. El protocolo define cómo se verificará después de la compuerta. Esta distinción evita contar dos veces el mismo trabajo.")

    for group in range(2):
        opening(doc, "Capítulo 2. Ingeniería del alcance",
                f"2.2 Diccionario de la EDT ({group+1} de 2)")
        paragraph(doc, "Cada ficha identifica un producto verificable del paquete. El esfuerzo se estima en horas de trabajo y se mantiene dentro de la regla 8/80.")
        for code, owner, hours, delivery, criterion in PACKAGES[group*4:(group+1)*4]:
            doc.add_heading(f"{code}  {PACKAGE_NAMES[code]}", 3)
            paragraph(doc, f"Responsable { {'PM': PM, 'PO': PO, 'AR': AR}[owner] } · {hours} horas",
                      "Nota de figura")
            paragraph(doc, f"Producto. {delivery}.")
            paragraph(doc, f"Aceptación. {criterion}")
        if group == 0:
            paragraph(doc, "Los paquetes de nodo definen la recuperación local y el acuse de alertas. La instalación y el ensayo físico se programan después de la autorización del piloto.")
        else:
            paragraph(doc, "El cierre de Fase I registra criterios pendientes y responsables. Una especificación o un ensayo de mesa se conserva como evidencia documental, junto con su alcance y supuestos.")


def schedule(doc, preview):
    outgoing, rows = successors(), cpm_rows()
    opening(doc, "Capítulo 3. Ingeniería de tiempo y redes críticas", "3.1 Precedencias y calendario")
    paragraph(doc, "Las relaciones son fin a inicio sin desfase. El calendario del caso usa lunes a viernes sin feriados, con inicio el 19/10/2026. El cierre modelado es el 25/11/2026 y el plazo del buzón es el 26/11/2026 a las 23:59.")
    fmt = lambda ids: ", ".join(activity_code(key) for key in ids) or "—"
    table(doc, ("ID", "Actividad", "Días", "Predecesoras", "Sucesoras"),
          [(activity_code(aid), name.split(" — ", 1)[1], duration, fmt(preds), fmt(outgoing[aid]))
           for aid, name, duration, preds, _ in ACTIVITIES], (1.2, 7.3, 1.6, 3, 2.7),
          caption=(5, "Matriz de precedencias lógicas"))
    paragraph(doc, "El ensayo de reconciliación K corresponde a un ejercicio de mesa con datos sintéticos. El CPM se calcula sin nivelación de recursos. La PM confirmará la disponibilidad en tareas simultáneas antes de comprometer las fechas de ejecución. El piloto físico depende de la sede, el hardware y el protocolo aprobados.")

    opening(doc, "Capítulo 3. Ingeniería de tiempo y redes críticas", "3.2 Red CPM y ruta crítica")
    paragraph(doc, "El cálculo hacia adelante toma el mayor fin temprano de las predecesoras. El cálculo hacia atrás toma el menor inicio tardío de las sucesoras. La holgura total es LS menos ES. Las actividades con holgura cero forman la ruta crítica.")
    figure(doc, 2, "Diagrama de red con dependencias fin a inicio", ROOT/"diagrams"/"Red_CPM_FaseI.png",
           "Nota. Las 12 actividades y las 14 relaciones corresponden al archivo .gan.")
    table(doc, ("Actividad no crítica", "Holgura total", "Convergencia"),
          (("B. Caso de negocio", rows[2][4], "En E con D"), ("E. Cronograma", rows[5][4], "En I"),
           ("F. Diseño del nodo", rows[6][4], "En H con G"), ("I. Riesgos y EMV", rows[9][4], "En K con J")),
          (7.2, 3.1, 5.5), caption=(6, "Holguras de las actividades no críticas"))
    paragraph(doc, "La PM prioriza la recuperación de retrasos en la ruta crítica. Una holgura compartida en una rama se vuelve a calcular después de cada cambio aprobado.")

    opening(doc, "Capítulo 3. Ingeniería de tiempo y redes críticas", "3.3 Cronograma y fechas CPM")
    figure(doc, 3, "Cronograma de Gantt de la Fase I", preview,
           "Nota. Vista del Gantt exportado desde GanttProject. El anexo PDF conserva la exportación a tamaño completo.", width=13.8)
    p = paragraph(doc, "Cronograma editable y PDF de respaldo. ")
    link(p, "Cronograma CPM Fase I", REPO + "/blob/master/schedule/Cronograma_CPM_FaseI.pdf")
    date_rows = []
    for aid, *_ in ACTIVITIES:
        es, ef, ls, lf, slack = rows[aid]
        dates = [add_business_days(START, day).strftime("%d/%m/%y") for day in (es, ef-1, ls, lf-1)]
        date_rows.append((activity_code(aid), *dates, slack))
    table(doc, ("ID", "Inicio T.", "Fin T.", "Inicio tardío", "Fin tardío", "Holg. d"),
          date_rows, (1.4, 2.8, 2.8, 3.2, 3.1, 2.5), caption=(7, "Fechas tempranas, tardías y holguras totales"))
    paragraph(doc, "T. = temprano. Los fines se expresan como el último día de ejecución. La tabla del PDF de respaldo incluye fechas completas y holguras totales.", "Nota de figura")


def risk(doc):
    opening(doc, "Capítulo 4. Riesgos y presupuesto base", "4.1 Taxonomía y evaluación cualitativa")
    paragraph(doc, "Se adaptan las categorías de Wallace y Keil (2004) a los riesgos del cliente, los requerimientos, el entorno regulatorio y la ejecución. La probabilidad se estima para el piloto. El impacto representa el costo incremental en caso de materialización.")
    figure(doc, 4, "Matriz de severidad 5 × 5", ROOT/"diagrams"/"Matriz_Riesgos_5x5.png",
           "Nota. Cada celda muestra P × I. El tono más oscuro identifica la severidad alta.")
    table(doc, ("Dimensión", "Riesgos"), tuple((category, ", ".join(code for code, c, *_ in RISKS if c == category))
          for category in dict.fromkeys(r[1] for r in RISKS)), (10.3, 5.5),
          caption=(8, "Clasificación de los riesgos por dimensión"))
    paragraph(doc, "Se atienden primero R7 (20) y R1 (16). A igual severidad, el EMV ordena la respuesta. Los intervalos monetarios reflejan ajustes menores, retrabajo y repetición de pruebas para una farmacia.")

    opening(doc, "Capítulo 4. Riesgos y presupuesto base", "4.2 Valor Monetario Esperado y responsables")
    paragraph(doc, "EMV = (P % ÷ 100) × impacto en USD. Las probabilidades y costos son estimaciones iniciales. Se revisarán con cotizaciones, un ensayo de desconexión y la verificación de recuperación de lecturas.")
    table(doc, ("Cód.", "Riesgo y responsable nominal", "P %", "I USD", "EMV USD", "Respuesta"),
          [(code, event + "\n" + owner, p, money(impact), money(p*impact/100), response)
           for code, _, event, owner, p, impact, response, *_ in RISKS]
          + [("Σ", "Reserva de contingencia", "—", "—", money(EMV_CENTS/100), "—")],
          (1.1, 7.2, 1.1, 2.0, 2.2, 2.2), caption=(9, "Registro cuantitativo de riesgos"))
    paragraph(doc, "R7 aporta USD 600 y R1 aporta USD 385. Ambos representan aproximadamente el 47 % de la reserva. Los costos compartidos entre incidentes se imputan una sola vez.")
    paragraph(doc, "Los responsables notifican disparadores en la revisión semanal. La PM escala pérdidas de evidencia, incidentes de privacidad o gastos superiores al saldo de reserva. Ante una falla de control térmico, el regente activa el registro manual.")

    opening(doc, "Capítulo 4. Riesgos y presupuesto base", "4.3 Línea base y acciones de contingencia")
    table(doc, ("Rama de la EDT", "USD"), [(code + " " + name, money(cost)) for code, name, cost, _ in WBS]
          + [("Costo directo EDT", money(DIRECT)), ("Reserva de contingencia", money(EMV_CENTS/100)),
             ("Línea base de costo", money(BASE))], (11.5, 4.3), caption=(10, "Presupuesto por rama de la EDT"))
    paragraph(doc, "La PM registra los gastos por código de riesgo y solicita aprobación al Project Owner para ampliar la línea base. Los desembolsos requieren evidencia del disparador y del costo.")
    table(doc, ("Cód.", "Disparador", "Acción inicial"), [(r[0], r[7], r[8]) for r in RISKS],
          (1.2, 6, 8.6), caption=(11, "Disparadores y respuesta inicial"))


def evidence(doc):
    opening(doc, "Expediente y entrega")
    paragraph(doc, "La compuerta solicita autorización para continuar con la planificación del piloto. La aprobación académica corresponde al tribunal. La validación física comienza después de acordar con el regente la sede y los criterios de seguridad.")
    table(doc, ("Evidencia", "Ruta en el repositorio"), (
        ("Dossier institucional en PDF", "docs/Dossier_Ejecutivo_GA15_FaseI_RfP.pdf"),
        ("Dossier editable", "docs/Dossier_Ejecutivo_GA15_FaseI_RfP.docx"),
        ("EDT editable y figura", "diagrams/EDT_WBS_FaseI.drawio · diagrams/EDT_WBS_FaseI.png"),
        ("Red CPM y matriz de riesgos", "diagrams/Red_CPM_FaseI.png · diagrams/Matriz_Riesgos_5x5.png"),
        ("Cronograma fuente y respaldo", "schedule/Cronograma_CPM_FaseI.gan · schedule/Cronograma_CPM_FaseI.pdf"),
        ("Defensa ejecutiva, siete láminas", "slides/Defensa_Ejecutiva_GA15_RfP.pdf")),
        (5.3, 10.5), caption=(12, "Inventario de evidencias del expediente"))
    sub(doc, "Trazabilidad y control de acceso")
    paragraph(doc, "Al revisar el historial, la PM registra cuatro commits, el PO tres y el arquitecto dos. La revisión de equidad considera los cambios y evidencias de cada rol junto con el conteo.")
    p = paragraph(doc, "Repositorio oficial. ")
    link(p, REPO, REPO)
    paragraph(doc, "La consulta autenticada confirmó que el repositorio es privado. Para entregar el expediente se requiere verificar que el enlace definitivo abre sin sesión de GitHub. La visibilidad pública queda pendiente de autorización.")


def references(doc):
    opening(doc, "Referencias")
    references = (
        ("Agencia Nacional de Regulación, Control y Vigilancia Sanitaria. (2026). ",
         "Regulación, control y vigilancia sanitaria de farmacias y botiquines privados",
         " (Instructivo IE-B.3.4.2-EST-01, versión 5.0, anexo 2). ", ARCSA),
        ("Asamblea Nacional del Ecuador. (2021). ", "Ley Orgánica de Protección de Datos Personales",
         ". Registro Oficial Suplemento 459. ", "https://www.spdp.gob.ec/docs/proteccion-de-datos-personales/general/normativa/"),
        ("Mitchell, R. K., Agle, B. R., & Wood, D. J. (1997). Toward a theory of stakeholder identification and salience: Defining the principle of who and what really counts. ",
         "Academy of Management Review, 22", "(4), 853–886. ", "https://doi.org/10.5465/amr.1997.9711022105"),
        ("Wallace, L., & Keil, M. (2004). Software project risks and their effect on outcomes. ",
         "Communications of the ACM, 47", "(4), 68–73. ", "https://doi.org/10.1145/975817.975819"),
    )
    for start, italic, end, url in references:
        p = paragraph(doc, start, "Referencia APA")
        p.add_run(italic).italic = True
        p.add_run(end)
        link(p, url, url)


def build():
    doc = setup()
    cover(doc)
    summary(doc)
    initiation(doc)
    scope(doc)
    source = ROOT / "schedule" / "Cronograma_CPM_FaseI.pdf"
    with TemporaryDirectory() as scratch:
        full = Path(scratch) / "chart"
        subprocess.run(["pdftoppm", "-r", "180", "-f", "1", "-l", "1", "-png",
                        "-singlefile", str(source), str(full)], check=True)
        preview = Path(scratch) / "preview.png"
        with Image.open(full.with_suffix(".png")) as chart:
            width, height = chart.size
            region = (round(width*.022), round(height*.113),
                      round(width*.978), round(height*.739))
            chart.crop(region).save(preview)
        schedule(doc, preview)
    risk(doc)
    evidence(doc)
    references(doc)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
