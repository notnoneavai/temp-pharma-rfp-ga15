# -*- coding: utf-8 -*-
"""Genera Cronograma_CPM_FaseI.gan (GanttProject) con ruta crítica en rojo."""
from pathlib import Path
from datetime import date, timedelta

OUT = Path(__file__).resolve().parents[1] / "schedule" / "Cronograma_CPM_FaseI.gan"

# Activities: id, name, duration days, predecessors (ids), critical
# Start Monday 2026-10-19 for a 28 working-day plan ending before 26/11
START = date(2026, 10, 19)

ACTIVITIES = [
    # id, name, dur, preds, critical, color
    (1, "A — Kickoff y Charter", 3, [], True),
    (2, "B — Business Case y presupuesto", 4, [1], False),
    (3, "C — Matriz ARCSA / requisitos", 5, [1], True),
    (4, "D — EDT + diccionario de paquetes", 4, [3], True),
    (5, "E — Cronograma CPM y ruta crítica", 3, [2, 4], False),
    (6, "F — Diseño nodo IoT + offline", 6, [3], False),
    (7, "G — Diseño plataforma y reporte", 5, [4], True),
    (8, "H — Modelo de integridad y accesos", 4, [6, 7], True),
    (9, "I — Matriz de riesgos 5x5 + EMV", 3, [5], False),
    (10, "J — Protocolo piloto refrigeradora", 3, [8], True),
    (11, "K — Ensayo Wi-Fi y reconciliación", 2, [9, 10], True),
    (12, "L — Cierre RfP y empaquetado dossier", 2, [11], True),
]


def add_business_days(d: date, days: int) -> date:
    cur = d
    added = 0
    while added < days:
        cur += timedelta(days=1)
        if cur.weekday() < 5:
            added += 1
    return cur


def business_days_between(start: date, end: date) -> int:
    """Inclusive count of business days from start to end-1 for duration semantics.
    GanttProject duration is in days; we use start date + duration.
    """
    if end <= start:
        return 0
    n = 0
    cur = start
    while cur < end:
        if cur.weekday() < 5:
            n += 1
        cur += timedelta(days=1)
    return n


def compute_schedule():
    """Forward pass ES/EF in business days from project start index 0."""
    dur = {a[0]: a[2] for a in ACTIVITIES}
    preds = {a[0]: a[3] for a in ACTIVITIES}
    es = {}
    ef = {}
    for aid, *_ in ACTIVITIES:
        if not preds[aid]:
            es[aid] = 0
        else:
            es[aid] = max(ef[p] for p in preds[aid])
        ef[aid] = es[aid] + dur[aid]
    return es, ef


def task_xml():
    es, ef = compute_schedule()
    lines = []
    dep_id = 1
    for aid, name, dur, preds, critical in ACTIVITIES:
        start = START if es[aid] == 0 else add_business_days(START, es[aid])
        # GanttProject uses start date and duration; color for critical = red
        color = "#ff0000" if critical else "#800040"
        lines.append(
            f'      <task id="{aid}" name="{name}" color="{color}" '
            f'meeting="false" start="{start.isoformat()}" duration="{dur}" '
            f'complete="0" expand="true">'
        )
        for p in preds:
            lines.append(
                f'        <depend id="{dep_id}" type="2" difference="0" hardness="Strong" dependee-id="{p}"/>'
            )
            dep_id += 1
        # custom property tip
        tip = "RUTA CRITICA (holgura=0)" if critical else "Holgura > 0"
        lines.append(f'        <customproperty taskproperty-id="tpc0" value="{tip}"/>')
        lines.append("      </task>")
    return "\n".join(lines), max(ef.values())


def build():
    tasks, project_days = task_xml()
    finish = add_business_days(START, project_days)
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<project name="CPM Fase I — Registro temperatura farmacias (RfP)"
         company="UIDE · Equipo Consultor GA-1.5"
         webLink="https://github.com/notnoneavai/temp-pharma-rfp-ga15"
         view-date="{START.isoformat()}"
         view-index="0"
         gantt-divider-location="450"
         resource-divider-location="300"
         version="3.0"
         locale="es">
  <description>
    Cronograma CPM Fase I. Ruta critica en ROJO: A-C-D-G-H-J-K-L (28 dias habiles).
    ES/EF/LS/LF y holguras documentadas en el Dossier Ejecutivo.
    Inicio: {START.isoformat()} · Fin estimado camino critico: {finish.isoformat()}.
  </description>
  <tasks empty-milestones="true">
    <taskproperties>
      <taskproperty id="tpd0" name="type" type="default" valuetype="icon"/>
      <taskproperty id="tpd1" name="priority" type="default" valuetype="icon"/>
      <taskproperty id="tpd2" name="info" type="default" valuetype="text"/>
      <taskproperty id="tpd3" name="name" type="default" valuetype="text"/>
      <taskproperty id="tpd4" name="begindate" type="default" valuetype="date"/>
      <taskproperty id="tpd5" name="enddate" type="default" valuetype="date"/>
      <taskproperty id="tpd6" name="duration" type="default" valuetype="int"/>
      <taskproperty id="tpd7" name="completion" type="default" valuetype="int"/>
      <taskproperty id="tpd8" name="coordinator" type="default" valuetype="text"/>
      <taskproperty id="tpd9" name="predecessors" type="default" valuetype="text"/>
      <taskproperty id="tpc0" name="Nota CPM" type="custom" valuetype="text"/>
    </taskproperties>
{tasks}
  </tasks>
  <resources>
    <resource id="0" name="Madeleine Jiménez (PM)" function="Default:0" contacts="" phone=""/>
    <resource id="1" name="Freddy Guaman (PO)" function="Default:1" contacts="" phone=""/>
    <resource id="2" name="Franco Quezada (Arch/Risk)" function="Default:1" contacts="" phone=""/>
  </resources>
  <allocations>
    <allocation task-id="1" resource-id="0" function="Default:0" responsible="true" load="100.0"/>
    <allocation task-id="2" resource-id="1" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="3" resource-id="1" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="4" resource-id="0" function="Default:0" responsible="true" load="100.0"/>
    <allocation task-id="5" resource-id="0" function="Default:0" responsible="true" load="100.0"/>
    <allocation task-id="6" resource-id="2" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="7" resource-id="1" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="8" resource-id="2" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="9" resource-id="2" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="10" resource-id="1" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="11" resource-id="2" function="Default:1" responsible="true" load="100.0"/>
    <allocation task-id="12" resource-id="0" function="Default:0" responsible="true" load="100.0"/>
  </allocations>
  <vacations/>
  <taskdisplaycolumns>
    <displaycolumn property-id="tpd3" order="0" width="200" visible="true"/>
    <displaycolumn property-id="tpd4" order="1" width="80" visible="true"/>
    <displaycolumn property-id="tpd5" order="2" width="80" visible="true"/>
    <displaycolumn property-id="tpd6" order="3" width="50" visible="true"/>
    <displaycolumn property-id="tpd7" order="4" width="50" visible="true"/>
    <displaycolumn property-id="tpc0" order="5" width="160" visible="true"/>
  </taskdisplaycolumns>
  <previous/>
  <roles roleset-name="Default"/>
</project>
'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(xml, encoding="utf-8")
    print(f"OK -> {OUT} (critical path {project_days} business days, finish ~{finish})")


if __name__ == "__main__":
    build()
