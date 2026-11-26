"""Genera las figuras y las siete láminas de defensa."""
from math import atan2, cos, sin
from pathlib import Path
import argparse
import subprocess
from tempfile import TemporaryDirectory
from textwrap import wrap
from xml.etree import ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen.canvas import Canvas
from reportlab import rl_config
from pypdf import PdfReader, PdfWriter

from build_gan import ACTIVITIES, START, activity_code, add_business_days, cpm_rows, successors
from rfp_data import BASE, DIRECT, EMV_CENTS, NPV, PAYBACK, PROJECT, RISKS, ROOT, TEAM, WBS, levels, money

GRAY = "#666666"
BLACK = "#222222"
RED = "#B52222"
LINE = "#909090"
FIGURES = ROOT / "diagrams"
LOGO = ROOT / "assets" / "logo_uide.jpeg"
SIZE = (800, 365)


def label(c, value, x, y, size=11, bold=False, center=False, color=BLACK):
    c.setFillColor(colors.HexColor(color))
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    if center:
        c.drawCentredString(x, y, value)
    else:
        c.drawString(x, y, value)


def rectangle(c, x, y, w, h, fill="#FFFFFF", stroke=LINE):
    c.setStrokeColor(colors.HexColor(stroke))
    c.setFillColor(colors.HexColor(fill))
    c.rect(x, y, w, h, fill=1, stroke=1)


def line(c, x, y, ex, ey, color=LINE, width=0.8, arrow=False):
    c.setLineWidth(width)
    c.setStrokeColor(colors.HexColor(color))
    c.line(x, y, ex, ey)
    if arrow:
        angle = atan2(ey-y, ex-x)
        for offset in (-0.52, 0.52):
            c.line(ex, ey, ex-7*cos(angle+offset), ey-7*sin(angle+offset))


def box(c, value, x, y, w, h, width, size=10, bold=False, stroke=LINE):
    rectangle(c, x, y, w, h, stroke=stroke)
    strings = wrap(value, width)
    first = y + h/2 + (len(strings)-1)*size*0.55 - size*0.33
    for index, string in enumerate(strings):
        label(c, string, x+w/2, first-index*size*1.1, size, bold, center=True)


def wbs_layout():
    nodes = [("1", "1  " + PROJECT, 240, 281, 320, 46, 49, True)]
    edges = []
    for index, (code, name, _, children) in enumerate(WBS):
        x = 12 + index * 131
        nodes.append((code, code + " " + name, x, 204, 121, 47, 20, True))
        edges.append(("1", code))
        for j, child in enumerate(children, 1):
            child_code = f"{code}.{j}"
            nodes.append((child_code, child_code + " " + child, x+13, 205-j*61, 108, 43, 19, False))
            edges.append((code, child_code))
    return nodes, edges


def wbs_figure(c):
    nodes, edges = wbs_layout()
    by_id = {node[0]: node for node in nodes}
    for parent, child in edges:
        _, _, x, y, w, _, _, _ = by_id[parent]
        _, _, ex, ey, ew, eh, _, _ = by_id[child]
        if parent == "1":
            branch = 266
            line(c, x+w/2, y, x+w/2, branch)
            line(c, x+w/2, branch, ex+ew/2, branch)
            line(c, ex+ew/2, branch, ex+ew/2, ey+eh)
        else:
            line(c, x+6, y, x+6, ey+eh/2)
            line(c, x+6, ey+eh/2, ex, ey+eh/2)
    for code, title, x, y, w, h, width, bold in nodes:
        box(c, title, x, y, w, h, width, size=10.7 if code == "1" else 9.1, bold=bold)


def wbs_drawio():
    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", id="edt-rfp", name="EDT Fase I")
    model = ET.SubElement(diagram, "mxGraphModel", grid="1", gridSize="10",
                          page="1", pageWidth="800", pageHeight="365")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    nodes, edges = wbs_layout()
    by_id = {node[0]: node for node in nodes}
    for code, title, x, y, w, h, width, bold in nodes:
        style = ("whiteSpace=wrap;html=0;fillColor=#FFFFFF;fontColor=#222222;"
                 "strokeColor=#909090;fontSize=10;align=center;verticalAlign=middle;")
        cell = ET.SubElement(root, "mxCell", id="n"+code, value="\n".join(wrap(title, width)),
                             style=style + ("fontStyle=1;" if bold else ""), vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(SIZE[1]-y-h),
                      width=str(w), height=str(h), attrib={"as": "geometry"})
    for index, (source, target) in enumerate(edges, 1):
        if source == "1":
            style = "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
            sx = by_id[source][2] + by_id[source][4] / 2
            tx = by_id[target][2] + by_id[target][4] / 2
            bend = ((sx, 99), (tx, 99))
        else:
            style = "exitX=0.05;exitY=1;entryX=0;entryY=0.5;"
            sx = by_id[source][2] + 6
            ty = SIZE[1] - by_id[target][3] - by_id[target][5] / 2
            bend = ((sx, ty),)
        edge = ET.SubElement(root, "mxCell", id=f"e{index}", edge="1", parent="1",
                             source="n"+source, target="n"+target,
                             style=style+"edgeStyle=segmentEdgeStyle;endArrow=none;strokeColor=#909090;")
        geometry = ET.SubElement(edge, "mxGeometry", relative="1", attrib={"as":"geometry"})
        points = ET.SubElement(geometry, "Array", attrib={"as":"points"})
        for px, py in bend:
            ET.SubElement(points, "mxPoint", x=str(px), y=str(py))
    ET.indent(mxfile)
    ET.ElementTree(mxfile).write(FIGURES / "EDT_WBS_FaseI.drawio", encoding="UTF-8", xml_declaration=True)


def network_figure(c):
    layout = {"A": (48, 190), "B": (146, 292), "C": (146, 190), "D": (244, 190),
              "E": (342, 292), "F": (244, 86), "G": (342, 190), "H": (440, 190),
              "I": (440, 292), "J": (538, 190), "K": (636, 190), "L": (734, 190)}
    timings = cpm_rows()
    for aid, targets in successors().items():
        x, y = layout[activity_code(aid)]
        for target in targets:
            ex, ey = layout[activity_code(target)]
            red = timings[aid][4] == timings[target][4] == 0
            line(c, x+29, y, ex-29, ey, RED if red else GRAY, 2 if red else 1, arrow=True)
    for aid, _, duration, _, _ in ACTIVITIES:
        key = activity_code(aid)
        x, y = layout[key]
        critical = timings[aid][4] == 0
        rectangle(c, x-29, y-22, 58, 44, stroke=RED if critical else LINE)
        label(c, key, x, y+2, 14, True, True, RED if critical else BLACK)
        label(c, f"{duration} días", x, y-13, 9, center=True)
    line(c, 22, 39, 50, 39, RED, 2)
    label(c, "Ruta crítica A-C-D-G-H-J-K-L (28 días)", 60, 35, 11)
    line(c, 333, 39, 361, 39)
    label(c, "Enlace con holgura", 371, 35, 11)


def risk_figure(c):
    placements = {}
    for code, _, _, _, p, impact, *_ in RISKS:
        placements.setdefault(levels(p, impact), []).append(code)
    probability = ("<10 %", "10-30 %", "31-50 %", "51-70 %", ">70 %")
    costs = ("<150", "150 a <300", "300 a <600", "600 a <900", "900 o más")
    x0, y0, w, h = 155, 85, 113, 42
    for p in range(1, 6):
        y = y0 + (p-1)*h
        label(c, f"{p}  {probability[p-1]}", 25, y+15, 11)
        for impact in range(1, 6):
            x = x0 + (impact-1)*w
            score = p*impact
            fill = "#FCFCFC" if score <= 4 else "#E9E9E9" if score <= 9 else "#D2D2D2" if score <= 14 else "#A9A9A9"
            rectangle(c, x, y, w, h, fill=fill)
            keys = placements.get((p, impact), [])
            label(c, str(score), x+9, y+26, 9)
            if keys:
                label(c, " / ".join(keys), x+w/2, y+12, 12, True, True)
    for i, cost in enumerate(costs, 1):
        label(c, f"{i}  {cost}", x0+(i-0.5)*w, 63, 10, center=True)
    label(c, "Probabilidad", 25, 312, 12, True)
    label(c, "Impacto (USD)", 25, 63, 11, True)
    label(c, "1-4 bajo   |   5-9 medio   |   10-14 medio alto   |   15-25 alto",
          155, 29, 11)


def cpm_annex(path):
    rows = cpm_rows()
    c = Canvas(str(path), pagesize=landscape(A4))
    c.setTitle("Cronograma CPM y holguras totales")
    label(c, "Fechas tempranas, tardías y holgura total", 48, 542, 23, True)
    label(c, "Calendario del caso: lunes a viernes, sin feriados. Fechas de fin inclusivas.", 48, 515, 11)
    headers = ("ID", "Actividad", "ES", "EF", "LS", "LF", "Holg. (d)")
    xs = (48, 89, 382, 469, 556, 643, 729)
    for index, header in enumerate(headers):
        label(c, header, xs[index], 475, 10, True)
    line(c, 48, 466, 790, 466)
    for aid, name, _, _, _ in ACTIVITIES:
        es, ef, ls, lf, slack = rows[aid]
        dates = tuple(add_business_days(START, offset).strftime("%d/%m/%Y")
                      for offset in (es, ef-1, ls, lf-1))
        values = (activity_code(aid), name.split(" — ", 1)[1], *dates, str(slack))
        y = 447-(aid-1)*27
        for index, value in enumerate(values):
            label(c, value, xs[index], y, 10, slack==0 and index==0,
                  color=RED if slack==0 and index==0 else BLACK)
        line(c, 48, y-8, 790, y-8, "#D0D0D0", 0.5)
    label(c, "Ruta crítica: A-C-D-G-H-J-K-L (28 días). Inicio 19/10/2026; cierre 25/11/2026.", 48, 115, 11, True)
    label(c, "ES/EF: inicio/fin temprano. LS/LF: inicio/fin tardío. Holgura = LS - ES.", 48, 91, 10)
    c.save()


def build_slides():
    path = ROOT / "slides" / "Defensa_Ejecutiva_GA15_RfP.pdf"
    w, h = landscape(A4)
    c = Canvas(str(path), pagesize=(w, h))
    c.setTitle("Defensa ejecutiva GA-1.5")
    c.setAuthor("Equipo consultor GA-1.5")
    titles = ("Defensa ejecutiva GA-1.5", "El problema y el alcance del piloto", "Viabilidad económica",
              "Alcance y entregables", "Ruta crítica y holguras", "Riesgos y línea base", "Decisión solicitada")
    figures = {4: wbs_figure, 5: network_figure, 6: risk_figure}
    slide_text = {
        1: ("Presentamos el plan para probar el sistema en una refrigeradora de farmacia.",
            "La Fase I define el alcance, el cronograma, el presupuesto y los riesgos."),
        2: ("ARCSA pide un registro diario de la temperatura de la refrigeradora. Entre dos anotaciones manuales, una salida de rango puede pasar desapercibida.",
            "Proponemos tomar lecturas continuas y avisar al personal de turno cuando la temperatura salga del rango definido para el producto.",
            "Si se corta el Wi-Fi, el equipo guarda las lecturas localmente. Al reconectar, la plataforma las recupera para que el regente pueda revisar el historial.",
            "En el piloto físico se probarán las alertas, la recuperación de lecturas y el reporte de incidentes."),
        3: (f"Estimamos una inversión de USD {money(BASE)}, incluida la reserva de contingencia.",
            "El escenario supone 18 farmacias pagando USD 29 al mes durante un año. Con USD 2.400 de costos operativos, el flujo anual es de USD 3.864.",
            f"Con ese flujo constante, recuperaríamos la inversión en {PAYBACK:.1f} meses. El valor actual neto a tres años, con una tasa del 12 %, es de USD {money(NPV)}.".replace("25.2", "25,2"),
            "Por cada farmacia menos, el flujo bajaría USD 348 al año si los costos operativos se mantienen."),
        4: ("La EDT divide el alcance de la Fase I en seis entregables y 17 paquetes de trabajo.",
            "Los paquetes de cada rama cubren todo su entregable. El nodo, por ejemplo, reúne muestreo, memoria local y alertas.",
            "Ocho paquetes tienen una ficha que indica quién responde, cuánto esfuerzo se estima y cómo se acepta el trabajo."),
        5: ("Cada flecha indica qué actividad debe terminar antes de que empiece la siguiente.",
            "La secuencia en rojo dura 28 días hábiles. Si una de esas tareas se retrasa, se mueve el cierre previsto.",
            "Fuera de esa ruta, B tiene 11 días de margen, E e I tienen 6 cada una y F tiene 3."),
        6: ("La matriz cruza la probabilidad con el impacto. Los tonos más oscuros indican mayor severidad.",
            "Primero atendemos R7, pérdida de lecturas al reconectar, y R1, alertas sin atender.",
            "La reserva suma el costo esperado de los ocho riesgos. Para cada uno multiplicamos probabilidad por impacto.",
            f"USD {money(DIRECT)} de costo directo más USD {money(EMV_CENTS/100)} de reserva dan una línea base de USD {money(BASE)}."),
        7: ("Solicitamos al tribunal aprobar la Fase I para avanzar con la preparación del piloto.",
            "Antes de probar con una refrigeradora real, confirmaremos el sitio, la disponibilidad de las piezas y quién atenderá las alertas.",
            "Con el regente acordaremos los límites de temperatura por producto y validaremos el formato del registro diario y del reporte de incidentes.",
            "Los archivos editables permiten revisar los entregables, las dependencias del cronograma y el cálculo de la reserva."),
    }

    def read_aloud(page, y, size, leading, gap):
        for sentence in slide_text[page]:
            for row in simpleSplit(sentence, "Helvetica", size, w-90):
                label(c, row, 42, y, size)
                y -= leading
            y -= gap
        assert y + leading + gap > 55, f"El texto de la lámina {page} invade el pie"

    for num, title in enumerate(titles, 1):
        c.drawImage(str(LOGO), w-155, h-84, width=116, height=57, preserveAspectRatio=True, mask="auto")
        label(c, title, 42, h-72, 28, True)
        line(c, 42, h-94, w-42, h-94, "#BDBDBD")
        if num == 1:
            for row, sentence in enumerate(wrap(PROJECT, 47)):
                label(c, sentence, 42, 428-row*35, 27, True)
            label(c, "Fase I · Ready for Planning · 26 de noviembre de 2026", 42, 324, 16)
            read_aloud(num, 294, 15, 20, 0)
            for index, (name, role) in enumerate(TEAM):
                label(c, f"{name}  |  {role}", 42, 252-index*36, 15)
            label(c, "Sin paralelo asignado", 42, 119, 12)
        elif num in figures:
            c.saveState()
            c.translate(54, 187)
            c.scale(0.91, 0.91)
            figures[num](c)
            c.restoreState()
            read_aloud(num, 173, 15, 18, 6)
        else:
            read_aloud(num, 437, 19, 26, 25)
        line(c, 42, 55, w-42, 55, "#BDBDBD")
        label(c, "UIDE · Gestión de Proyectos de TI", 42, 34, 10)
        label(c, f"{num} / 7", w-70, 34, 10)
        c.showPage()
    c.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gantt-export", type=Path, help="PDF exportado desde GanttProject")
    args = parser.parse_args()
    rl_config.useA85 = 0
    wbs_drawio()
    outputs = ((wbs_figure, "EDT_WBS_FaseI"), (network_figure, "Red_CPM_FaseI"),
               (risk_figure, "Matriz_Riesgos_5x5"))
    with TemporaryDirectory() as scratch:
        for function, name in outputs:
            pdf = Path(scratch) / f"{name}.pdf"
            c = Canvas(str(pdf), pagesize=SIZE)
            function(c)
            c.save()
            raster = Path(scratch) / name
            subprocess.run(["pdftoppm", "-r", "250", "-png", "-singlefile", str(pdf),
                            str(raster)], check=True)
            (FIGURES / f"{name}.png").write_bytes(raster.with_suffix(".png").read_bytes())
        if args.gantt_export:
            annex = Path(scratch) / "holguras.pdf"
            cpm_annex(annex)
            native = PdfReader(args.gantt_export)
            chart = next(page for page in native.pages if "Gantt Chart" in page.extract_text())
            writer = PdfWriter()
            writer.add_page(chart)
            writer.append(annex)
            writer.add_metadata({"/Title": "Cronograma CPM · Exportación GanttProject y holguras"})
            writer.write(ROOT / "schedule" / "Cronograma_CPM_FaseI.pdf")
    build_slides()


if __name__ == "__main__":
    main()
