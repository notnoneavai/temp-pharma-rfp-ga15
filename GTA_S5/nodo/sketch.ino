#include <DallasTemperature.h>
#include <MQTT.h>
#include <OneWire.h>
#include <Preferences.h>
#include <WiFi.h>
#include <time.h>

constexpr int PIN_SONDA = 4;
constexpr int PIN_CORTE_ENLACE = 14;
constexpr int PIN_ALERTA = 27;
constexpr unsigned long PERIODO_MS = 5000;
constexpr unsigned long REINTENTO_MS = 5000;
constexpr int CAPACIDAD = 144;
constexpr char NODO[] = "refrigeradora-01";
constexpr char BROKER[] = "test.mosquitto.org";
constexpr char ESTADO[] = "uide/g3/farmacias/s5-9c41/refrigeradora-01/estado";
constexpr char TELEMETRIA[] = "uide/g3/farmacias/s5-9c41/refrigeradora-01/telemetria";

struct Lectura {
  uint64_t secuencia;
  int64_t horaUtc;
  float temperatura;
};

OneWire bus(PIN_SONDA);
DallasTemperature sonda(&bus);
Preferences memoria;
WiFiClient conexion;
MQTTClient mqtt(512);
uint64_t secuencias[CAPACIDAD] = {};
uint64_t ultimaSecuencia = 0;
unsigned long ultimaMuestra = 0;
unsigned long ultimoIntento = 0;
bool enlaceInterrumpido = false;
bool memoriaDisponible = false;
bool estadoPublicado = false;
char clienteId[32];

void clavePara(int espacio, char *clave) {
  snprintf(clave, 8, "r%03d", espacio);
}

void guardarLectura() {
  const time_t ahora = time(nullptr);
  if (ahora < 1700000000) {
    Serial.println("Reloj sin sincronizar. Lectura pendiente.");
    return;
  }
  sonda.requestTemperatures();
  const float grados = sonda.getTempCByIndex(0);
  if (!isfinite(grados) || grados == DEVICE_DISCONNECTED_C || grados < -55 || grados > 125) {
    digitalWrite(PIN_ALERTA, HIGH);
    Serial.println("Sonda sin lectura valida.");
    return;
  }
  const bool excursion = grados < 2 || grados > 8;
  digitalWrite(PIN_ALERTA, excursion);

  int espacio = 0;
  while (espacio < CAPACIDAD && secuencias[espacio] != 0) {
    ++espacio;
  }
  if (espacio == CAPACIDAD) {
    Serial.println("Cola llena. Se conserva la cola y se pierde la lectura nueva.");
    return;
  }
  const Lectura lectura{ultimaSecuencia + 1, static_cast<int64_t>(ahora), grados};
  if (memoria.putULong64("secuencia", lectura.secuencia) != sizeof(uint64_t)) {
    Serial.println("No se pudo reservar un identificador de lectura.");
    return;
  }
  ultimaSecuencia = lectura.secuencia;
  char clave[8];
  clavePara(espacio, clave);
  if (memoria.putBytes(clave, &lectura, sizeof(lectura)) != sizeof(lectura)) {
    Serial.println("No se pudo guardar la lectura.");
    return;
  }
  secuencias[espacio] = lectura.secuencia;
  Serial.printf("Guardada #%llu %.2f C%s\n", lectura.secuencia, grados,
                excursion ? " FUERA DE RANGO" : "");
}

void publicarPendiente() {
  int espacio = -1;
  for (int i = 0; i < CAPACIDAD; ++i) {
    if (secuencias[i] && (espacio < 0 || secuencias[i] < secuencias[espacio])) {
      espacio = i;
    }
  }
  if (espacio < 0) return;
  char clave[8];
  clavePara(espacio, clave);
  Lectura lectura{};
  if (memoria.getBytes(clave, &lectura, sizeof(lectura)) != sizeof(lectura)) return;
  const time_t hora = static_cast<time_t>(lectura.horaUtc);
  char fecha[25];
  tm utc{};
  gmtime_r(&hora, &utc);
  strftime(fecha, sizeof(fecha), "%Y-%m-%dT%H:%M:%SZ", &utc);
  const bool excursion = lectura.temperatura < 2 || lectura.temperatura > 8;
  char mensaje[240];
  snprintf(mensaje, sizeof(mensaje),
           "{\"nodo\":\"%s\",\"seq\":%llu,\"hora_utc\":\"%s\","
           "\"temperatura_c\":%.2f,\"fuera_de_rango\":%s}",
           NODO, lectura.secuencia, fecha, lectura.temperatura, excursion ? "true" : "false");

  if (mqtt.publish(TELEMETRIA, mensaje, false, 1) && memoria.remove(clave)) {
    secuencias[espacio] = 0;
    Serial.printf("Confirmada por broker #%llu\n", lectura.secuencia);
  }
}

void gestionarRed(unsigned long ahora) {
  const bool corteActivo = digitalRead(PIN_CORTE_ENLACE) == HIGH;
  if (corteActivo != enlaceInterrumpido) {
    enlaceInterrumpido = corteActivo;
    if (corteActivo) {
      conexion.stop();
      estadoPublicado = false;
      Serial.println("Enlace MQTT cortado. El nodo sigue midiendo.");
    } else {
      Serial.println("Enlace MQTT habilitado. Reintentando MQTT.");
    }
  }
  if (corteActivo || WiFi.status() != WL_CONNECTED) return;
  if (!mqtt.connected()) {
    estadoPublicado = false;
    if (ahora - ultimoIntento < REINTENTO_MS) return;
    ultimoIntento = ahora;
    if (!mqtt.connect(clienteId)) return;
  }
  if (!mqtt.loop()) return;
  if (!estadoPublicado) {
    estadoPublicado = mqtt.publish(ESTADO, "online", true, 1);
    if (estadoPublicado) Serial.println("MQTT online");
  }
  if (estadoPublicado && memoriaDisponible) publicarPendiente();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_CORTE_ENLACE, INPUT_PULLUP);
  pinMode(PIN_ALERTA, OUTPUT);
  sonda.begin();
  sonda.setResolution(10);
  memoriaDisponible = memoria.begin("farmacia", false);
  if (memoriaDisponible) {
    ultimaSecuencia = memoria.getULong64("secuencia");
    for (int i = 0; i < CAPACIDAD; ++i) {
      char clave[8];
      clavePara(i, clave);
      if (memoria.getBytesLength(clave) != sizeof(Lectura)) continue;
      Lectura lectura{};
      if (memoria.getBytes(clave, &lectura, sizeof(lectura)) == sizeof(lectura)) {
        secuencias[i] = lectura.secuencia;
      }
    }
  } else {
    Serial.println("Memoria local no disponible.");
  }
  snprintf(clienteId, sizeof(clienteId), "farmacia-9c41-%08lx",
           static_cast<unsigned long>(esp_random()));
  mqtt.begin(BROKER, 1883, conexion);
  mqtt.setKeepAlive(10);
  mqtt.setTimeout(1500);
  mqtt.setWill(ESTADO, "offline", true, 1);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin("Wokwi-GUEST", "", 6);
  configTime(0, 0, "pool.ntp.org", "time.google.com");
}

void loop() {
  const unsigned long ahora = millis();
  if (memoriaDisponible && ahora - ultimaMuestra >= PERIODO_MS) {
    ultimaMuestra = ahora;
    guardarLectura();
  }
  gestionarRed(ahora);
  delay(10);
}
