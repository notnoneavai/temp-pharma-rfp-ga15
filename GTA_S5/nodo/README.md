# Registro automático y auditable de temperatura para farmacias

Prototipo de Tecnologías Emergentes, grupo 3. Mide el equivalente a una refrigeradora de farmacia con una sonda DS18B20 virtual. La fase de diseño del panel, el informe y la verificación de integridad se describe en el plan GTA S5.

## Abrir el simulador

1. Abre [el simulador de farmacias en Wokwi](https://wokwi.com/projects/481864326152183809).
2. Inicia la simulación con el interruptor a la izquierda. Espera la sincronización del reloj y las primeras lecturas. Cambia la temperatura haciendo clic en la sonda.

Para importar el circuito en otro proyecto ESP32, copia `sketch.ino` y `diagram.json` en sus pestañas. Agrega **OneWire**, **DallasTemperature** y **MQTT** de 256dpi en Library Manager.

El DS18B20 conecta DQ a GPIO4 con una resistencia de 4,7 kΩ a 3,3 V. El LED en GPIO27 señala excursiones. En Wokwi, el interruptor en GPIO14 cierra la conexión MQTT para simular la pérdida de comunicación mientras el ESP32 sigue midiendo. El circuito usa Wokwi-GUEST y un broker público para datos sintéticos. El ensayo de corte de Wi-Fi real se realizará con el equipo físico.

## Ensayo en Ubuntu

Con la VM encendida, abre Windows Terminal y conéctate por SSH con tu usuario de Ubuntu. Usa el puerto de reenvío configurado en VirtualBox. Dentro de Ubuntu ejecuta:

```bash
TZ=America/Guayaquil mosquitto_sub -h test.mosquitto.org -p 1883 -q 1 -t 'uide/g3/farmacias/s5-9c41/refrigeradora-01/+' -F '%I %t %q %r %p'
```

| Prueba | Acción | Resultado esperado |
| --- | --- | --- |
| Conexión | Inicia el nodo a 5 °C | Estado `online` y lecturas JSON de 5 °C |
| Excursión | Cambia la sonda a 10 °C y luego a 5 °C | El LED se enciende y apaga. El JSON cambia `fuera_de_rango` |
| Cola local | Mueve el interruptor a la derecha por 20 s con el nodo encendido. Vuelve a la izquierda | La consola local sigue mostrando secuencias guardadas. Las mismas secuencias y horas originales llegan a Ubuntu al reconectar |
| Last Will | Con el nodo en línea, pulsa Stop en Wokwi y mantén abierta la suscripción | Llega un nuevo `offline` en el tema `estado`. Mide desde Stop. La meta del ensayo es ≤30 s |

El estado usa QoS 1 y retención. La telemetría usa QoS 1 sin retención. La cola local de demostración guarda hasta 144 lecturas en flash y libera cada una tras el PUBACK del broker. Un PUBACK confirma recepción en el broker. La persistencia de extremo a extremo requiere acuse posterior al registro en la base y deduplicación por nodo y secuencia. Si el reloj aún no ha sincronizado, el nodo espera antes de emitir lecturas fechadas.

Haz la prueba con una sola instancia. Para ensayos simultáneos, cambia el sufijo de ambos temas y del suscriptor. Los parámetros 5 s y 2–8 °C se usan para la demostración. El regente define el intervalo y los límites para el piloto según los productos almacenados.
