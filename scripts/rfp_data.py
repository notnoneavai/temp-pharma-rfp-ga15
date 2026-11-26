"""Datos del dossier y de las láminas GA-1.5."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/notnoneavai/temp-pharma-rfp-ga15"
PROJECT = "Registro automático y auditable de temperatura para farmacias"
PM = "Madeleine Yanhely Jiménez Gaona"
PO = "Freddy Emanuel Guaman Gonzalez"
AR = "Franco Rene Quezada Ordoñez"
TEAM = ((PM, "Project Manager"), (PO, "Product Owner"), (AR, "Arquitecto de Software / Risk Manager"))
ARCSA = "https://www.controlsanitario.gob.ec/wp-content/plugins/download-monitor/download.php?force=0&id=16026"

# Código, entregable, costo directo, paquetes terminales.
WBS = (
    ("1.1", "Gestión y gobernanza", 900, ("Acta y caso de negocio", "Plan integral RfP", "Expediente y cierre")),
    ("1.2", "Cumplimiento y requisitos", 800, ("Matriz ARCSA", "Especificación de registro y alertas", "Criterios del reporte")),
    ("1.3", "Nodo de temperatura", 1600, ("Diseño de sonda y muestreo", "Almacenamiento local", "Diseño de alertas")),
    ("1.4", "Plataforma del regente", 1500, ("Diseño de API e identidad", "Diseño del tablero", "Exportación para inspección")),
    ("1.5", "Seguridad e integridad", 700, ("Integridad de lecturas", "Controles de acceso y datos")),
    ("1.6", "Preparación del piloto", 500, ("Protocolo con regente", "Ensayo de mesa sin Wi-Fi", "Informe de preparación")),
)

# Código, responsable, esfuerzo, producto documental y aceptación previa al piloto.
PACKAGES = (
    ("1.1.2", "PM", 40, "Líneas base de alcance, tiempo, costo y riesgo", "Cada línea base tiene versión y responsable. Los cuatro valores coinciden con el dossier."),
    ("1.2.1", "PO", 24, "Matriz de trazabilidad del anexo 2, apartado 5.3", "Cada criterio aplicable tiene fuente, evidencia prevista, dueño y tratamiento de brechas."),
    ("1.3.2", "AR", 56, "Diseño de cola persistente y recuperación por ID", "El diseño incluye prueba de desconexión de 2 h y exige cero huecos y duplicados al reconciliar."),
    ("1.3.3", "AR", 32, "Especificación de alerta, acuse y respaldo", "Define prueba con aviso en ≤60 s en línea y escalamiento al turno a los 15 min sin acuse."),
    ("1.4.3", "PO", 40, "Especificación y muestra de informe con datos sintéticos", "Incluye equipo, fechas, lecturas, eventos y verificación de integridad, sin datos de pacientes."),
    ("1.5.1", "AR", 48, "Diseño de historial de solo anexado y verificación", "Incluye prueba negativa que detecta un registro modificado y conserva el original."),
    ("1.6.1", "PO", 24, "Guion de validación con regente y criterios de suspensión", "Define responsable, protocolo de registro manual y acta con criterios de aprobación por prueba."),
    ("1.6.2", "AR", 16, "Guion y evidencia esperada del ensayo de mesa", "Contrasta IDs de entrada y salida y exige cero pérdidas o duplicados tras la reconexión."),
)
PACKAGE_NAMES = {f"{code}.{i}": name for code, _, _, children in WBS for i, name in enumerate(children, 1)}

# Código, categoría, evento, responsable, P %, I USD, respuesta, disparador y acción.
RISKS = (
    ("R1", "Mandato del cliente", "Alertas desatendidas", PO, 55, 700, "Mitigar", "Alerta sin acuse en 15 min", "Activar respaldo telefónico y ensayar el relevo."),
    ("R2", "Mandato del cliente", "Retiro de la farmacia piloto", PM, 20, 950, "Escalar", "Cancelación o sede sin confirmar a cinco días", "Proponer sede alterna y elevar impacto al Project Owner."),
    ("R3", "Requerimientos", "Umbrales o reporte mal definidos", PO, 45, 450, "Mitigar", "Umbral distinto de la etiqueta o día sin reporte", "Conservar bitácora manual y validar parámetros con el regente."),
    ("R4", "Requerimientos", "Evidencia sin integridad verificable", AR, 35, 800, "Evitar", "Falla la verificación de una lectura", "Bloquear edición directa y recuperar la copia verificable."),
    ("R5", "Entorno regulatorio LOPDP", "Acceso indebido a datos de usuarios", PM, 15, 1200, "Mitigar", "Acceso confirmado fuera del rol", "Revocar accesos, preservar evidencia y evaluar notificación."),
    ("R6", "Entorno regulatorio LOPDP", "Captura o retención excesiva", PO, 25, 500, "Evitar", "Dato de paciente o fuera del plazo aprobado", "Bloquear campos libres y depurar con aprobación."),
    ("R7", "Ejecución y equipo", "Pérdida de lecturas al reconectar", AR, 60, 1000, "Mitigar", "Falta o sobra una lectura tras desconectar el Wi-Fi", "Activar registro manual y reconciliar el respaldo por ID."),
    ("R8", "Ejecución y equipo", "Deriva de la sonda", AR, 40, 350, "Transferir", "Diferencia >0,5 °C en dos mediciones", "Activar garantía pactada y usar un repuesto verificado."),
)

DIRECT = sum(cost for _, _, cost, _ in WBS)
EMV_CENTS = sum(r[4] * r[5] for r in RISKS)
BASE = DIRECT + EMV_CENTS / 100
FLOW = 18 * 29 * 12 - 2400
PAYBACK = BASE / (FLOW / 12)
NPV = -BASE + sum(FLOW / (1.12 ** i) for i in range(1, 4))


def money(value):
    return f"{value:,.2f}".translate(str.maketrans(",.", ".,"))


def levels(probability, impact):
    p = 1 + sum(probability >= threshold for threshold in (10, 31, 51, 71))
    i = 1 + sum(impact >= threshold for threshold in (150, 300, 600, 900))
    return p, i
