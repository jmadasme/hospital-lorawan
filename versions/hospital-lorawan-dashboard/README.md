# 🏥 Hospital LoRaWAN Monitor

**Sistema de Monitoreo en Tiempo Real de Temperatura y Humedad para Entornos Hospitalarios**

![Versión](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57)
![Licencia](https://img.shields.io/badge/license-MIT-yellow)

---

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#-descripción-del-proyecto)
2. [El Problema: Monitoreo Hospitalario](#-el-problema-monitoreo-hospitalario)
3. [Principio Físico: Sensores LoRaWAN](#-principio-físico-sensores-lorawan)
4. [Arquitectura del Sistema](#-arquitectura-del-sistema)
5. [Stack Tecnológico](#-stack-tecnológico)
6. [Requisitos del Sistema](#-requisitos-del-sistema)
7. [Guía de Instalación](#-guía-de-instalación)
8. [Cómo Funciona](#-cómo-funciona)
9. [Secciones del Dashboard](#-secciones-del-dashboard)
10. [Tipos de Dispositivos](#-tipos-de-dispositivos)
11. [Conexión con LoRaWAN](#-conexión-con-lorawan)
12. [Ejemplos de Uso](#-ejemplos-de-uso)
13. [Calibración y Configuración](#-calibración-y-configuración)
14. [Advertencias y Precauciones](#-advertencias-y-precauciones)
15. [Licencia y Autor](#-licencia-y-autor)

---

## 🏆 Descripción del Proyecto

**Hospital LoRaWAN Monitor** es una aplicación web de dashboard para monitorear en **tiempo real** la temperatura y humedad de hasta **200 sensores** distribuidos en un entorno hospitalario. Los sensores se conectan mediante una red **LoRaWAN** (Long Range Wide Area Network) y el sistema visualiza los datos en un panel interactivo con gráficos, alertas y filtros.

El proyecto incluye un **generador de datos mock** que simula el comportamiento realista de los sensores, permitiendo probar y demostrar el sistema sin necesidad de hardware físico. En un entorno de producción, los datos llegarían desde una red LoRaWAN real a través de gateways y servidores de red como **The Things Network (TTN)** o **ChirpStack**.

---

## 🎯 El Problema: Monitoreo Hospitalario

En un hospital, mantener condiciones ambientales controladas no es un lujo, es una **necesidad crítica**:

| Área | Por qué es importante |
|------|----------------------|
| 🧪 **Laboratorios y Bancos de Sangre** | Reactivos, muestras biológicas y hemoderivados requieren refrigeración estricta (2-8 °C). Una desviación puede inutilizar insumos costosos. |
| 💊 **Farmacia** | Medicamentos como insulinas, vacunas y biológicos pierden efectividad si se rompe la cadena de frío. |
| 🧬 **Biobancos y Freezers -80°C** | Muestras de tejidos, ADN y células madre se degradan irreversiblemente si la temperatura sube. |
| 🍽️ **Cocina y Almacenes** | Alimentos perecederos para pacientes requieren temperaturas controladas. |
| 🌡️ **Áreas de Pacientes** | Temperatura y humedad ambiental afectan la recuperación de pacientes y el control de infecciones. |
| ⚰️ **Morgue** | La conservación de cuerpos requiere frío constante. |

**El desafío**: un hospital típico puede tener 100+ equipos de refrigeración distribuidos en diferentes pisos y edificios. Verificar manualmente cada uno es imposible en tiempo real. Se necesita un sistema **automatizado, centralizado y con alertas inmediatas**.

---

## 📡 Principio Físico: Sensores LoRaWAN

### ¿Qué es LoRaWAN?

**LoRaWAN** (Long Range Wide Area Network) es un protocolo de comunicación inalámbrica de **bajo consumo** y **largo alcance** diseñado para Internet de las Cosas (IoT). Opera en bandas ISM sub-GHz (915 MHz en América, 868 MHz en Europa).

### ¿Cómo funciona un sensor de temperatura LoRaWAN?

```
┌─────────────────────────────────────────────────────────────────┐
│                    SENSOR LORAWAN TÍPICO                        │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ Sensor   │───▶│ Microcont.   │───▶│ Módulo LoRa         │   │
│  │ Temp/HR  │    │ + ADC        │    │ (RFM95, SX1276)     │   │
│  │(DS18B20, │    │              │    │                      │   │
│  │ DHT22,   │    │              │    │  Antena              │   │
│  │ SHT30)   │    │              │    │   ◢◣                 │   │
│  └──────────┘    └──────────────┘    └───┬──────────────────┘   │
│                                         │                      │
│  ┌──────────┐                            │                      │
│  │ Batería  │                            │                      │
│  │ (LiSOCl2)│                            │                      │
│  └──────────┘                            │                      │
└──────────────────────────────────────────┼──────────────────────┘
                                           │
                                    (radiofrecuencia)
                                           │
                              ┌────────────▼────────────┐
                              │     Gateway LoRaWAN      │
                              │   (Concentrador SX130x) │
                              └────────────┬────────────┘
                                           │
                                    (Internet / Ethernet)
                                           │
                              ┌────────────▼────────────┐
                              │   Servidor de Red        │
                              │   (TTN / ChirpStack)     │
                              └────────────┬────────────┘
                                           │
                                    (MQTT / HTTP)
                                           │
                              ┌────────────▼────────────┐
                              │   ┌──────────────┐      │
                              │   │  Dashboard   │      │
                              │   │  (Flask App) │      │
                              │   └──────────────┘      │
                              └─────────────────────────┘
```

1. **Sensor digital** (DS18B20, DHT22, SHT30) mide temperatura y/o humedad.
2. El **microcontrolador** lee el sensor, convierte la señal analógica a digital y empaqueta los datos.
3. El **módulo LoRa** (semiconductor RF) transmite el paquete por radiofrecuencia a baja potencia.
4. Un **Gateway LoRaWAN** (concentrador multi-canal) recibe el paquete y lo reenvía por IP.
5. El **servidor de red** (The Things Network, ChirpStack) descodifica el payload y lo entrega vía MQTT/HTTP.
6. El **dashboard** consume los datos y los visualiza.

### Ventajas de LoRaWAN para hospitales

| Característica | Beneficio |
|---------------|-----------|
| **Alcance:** 2-15 km en exteriores, cientos de metros en interiores | Un solo gateway puede cubrir un hospital completo |
| **Bajo consumo:** Batería de 5-10 años | Sensores inalámbricos sin mantenimiento constante |
| **Penetración:** Buena en interiores con muros | Funciona en sótanos, cuartos fríos, laboratorios |
| **Costo:** Módulos desde $10 USD | Despliegue masivo viable |
| **Capacidad:** Miles de nodos por gateway | Escalable a todo el hospital |

---

## 🏗️ Arquitectura del Sistema

```
                         ┌─────────────────────────────┐
                         │       NAVEGADOR WEB          │
                         │  (Chrome, Firefox, Edge)     │
                         │                              │
                         │  ┌────────────────────────┐  │
                         │  │  Chart.js (gráficos)    │  │
                         │  │  dashboard.js (lógica)  │  │
                         │  │  dashboard.css (estilos)│  │
                         │  └────────────────────────┘  │
                         └─────────────┬───────────────┘
                                       │  HTTP Polling cada 10s
                                       │
                         ┌─────────────▼───────────────┐
                         │        SERVIDOR FLASK        │
                         │                              │
                         │  ┌────────────────────────┐  │
                         │  │  app.py (punto entrada) │  │
                         │  │  routes.py (API REST)   │  │
                         │  │  config.py (config)     │  │
                         │  └────────────────────────┘  │
                         │              │                │
                         │  ┌───────────▼────────────┐  │
                         │  │    data_generator.py    │  │
                         │  │  (Thread daemon, 30s)  │  │
                         │  └───────────┬────────────┘  │
                         │              │                │
                         │  ┌───────────▼────────────┐  │
                         │  │    database.py          │  │
                         │  │  (SQLite3, modelos)    │  │
                         │  └───────────┬────────────┘  │
                         └─────────────┼────────────────┘
                                       │
                         ┌─────────────▼────────────────┐
                         │  ┌─────────────────────────┐ │
                         │  │   hospital_lorawan.db    │ │
                         │  │   (SQLite)              │ │
                         │  │   ├─ devices (200)      │ │
                         │  │   ├─ readings (∞)       │ │
                         │  │   └─ alerts (∞)         │ │
                         │  └─────────────────────────┘ │
                         └──────────────────────────────┘

   FLUJO DE DATOS (Mock):
   ┌──────────┐    cada 30s    ┌───────────┐    cada 10s    ┌──────────┐
   │Generator │ ──────────────▶│  SQLite   │ ◀───────────── │ Frontend │
   │(Thread)  │  inserta       │    BD     │   poll JSON    │ (Chart)  │
   └──────────┘  lecturas      └───────────┘                └──────────┘
```

### Flujo de Datos Detallado

1. **Generación Mock**: `data_generator.py` ejecuta un thread daemon que cada **30 segundos** genera lecturas realistas para los 200 dispositivos.
2. **Validación**: Cada lectura se compara con los rangos configurados. Si está fuera de rango, se genera una alerta en la BD.
3. **Almacenamiento**: Las lecturas y alertas se guardan en `hospital_lorawan.db` (SQLite).
4. **Polling**: El frontend (JavaScript) consulta los endpoints REST cada **10 segundos** para obtener datos actualizados.
5. **Visualización**: Chart.js renderiza gráficos de tendencia. Las alertas se muestran en rojo con animación.
6. **Interacción**: El usuario puede filtrar por tipo de dispositivo, buscar por nombre/ubicación, y seleccionar un dispositivo para ver su historial gráfico.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|-----------|
| **Backend** | Python + Flask | 3.10+ / 3.0+ | Servidor web y API REST |
| **Frontend** | HTML5 + CSS3 + JavaScript | — | Interfaz de usuario |
| **Gráficos** | Chart.js | 4.4+ | Gráficos de tendencia en tiempo real |
| **Base de Datos** | SQLite3 | 3.x | Almacenamiento local (sin servidor) |
| **Estilos** | Font Awesome | 6.5+ | Iconografía profesional |
| **Comunicación** | Flask-CORS | 4.0+ | Permitir peticiones cross-origin |
| **Red IoT** | LoRaWAN (simulado) | — | En producción: MQTT/HTTP desde TTN |

---

## 💻 Requisitos del Sistema

### Mínimos (para desarrollo/demo)

| Recurso | Especificación |
|---------|---------------|
| **CPU** | 2 cores (x86_64 o ARM) |
| **RAM** | 1 GB |
| **Disco** | 500 MB libres |
| **SO** | Linux, macOS o Windows (WSL2) |
| **Python** | 3.10 o superior |
| **Navegador** | Chrome 90+, Firefox 88+, Edge 90+, Safari 14+ |

### Recomendados (para producción)

| Recurso | Especificación |
|---------|---------------|
| **CPU** | 4 cores |
| **RAM** | 4 GB |
| **Disco** | 10 GB (crecimiento de BD) |
| **SO** | Ubuntu 22.04 LTS o Raspberry Pi OS |
| **Proxy** | Nginx (para servir estáticos y SSL) |

### Dependencias de Python

```
flask>=3.0.0
flask-cors>=4.0.0
```

---

## 🚀 Guía de Instalación

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/wanderc137/hospital-lorawan-dashboard.git
cd hospital-lorawan-dashboard
```

### Paso 2: Crear y activar entorno virtual

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### Paso 3: Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Ejecutar la aplicación

```bash
python app.py
```

### Paso 5: Abrir el dashboard

Navega a **[http://localhost:5000](http://localhost:5000)** en tu navegador.

### Verificación

Deberías ver:
- 5 tarjetas de resumen con estadísticas
- Una tabla con 200 dispositivos monitoreados
- Alertas en vivo (algunas aparecerán por el 10% de datos fuera de rango)
- Un gráfico de tendencia (selecciona un dispositivo)
- El indicador **EN VIVO** parpadeando

---

## 🔧 Cómo Funciona

### Generación de Datos Mock

El sistema incluye un generador de datos interno que simula el comportamiento de sensores LoRaWAN reales:

- **Intervalo**: Genera una ronda completa de lecturas para los 200 dispositivos cada **30 segundos**.
- **Realismo**: Usa distribución **gaussiana** alrededor del punto medio del rango de cada dispositivo.
- **Variación**: Los freezers tienen variación mínima (±0.5 °C). Los equipos de refrigeración tienen variación moderada (±15% del rango).
- **Fallos simulados**: El **10%** de las lecturas se generan **fuera de rango** para probar el sistema de alertas.
- **Inercia térmica**: Los sensores ambientales varían lentamente simulando la inercia térmica de una habitación.

### Sistema de Polling

```
Frontend (JS)                    Backend (Flask)
     │                               │
     │  GET /api/readings/current     │
     ├──────────────────────────────▶│
     │  GET /api/alerts              │
     ├──────────────────────────────▶│
     │  GET /api/stats               │
     ├──────────────────────────────▶│
     │                               │
     │  ◀──── JSON con datos ───────┤
     │                               │
     │  (Actualiza tabla, cards,     │
     │   alertas y contadores)       │
     │                               │
     │  ─── Espera 10 segundos ───   │
     │                               │
```

### Sistema de Alertas

- **Evaluación**: Cada lectura se evalúa contra los límites `temp_min`/`temp_max` y `humidity_min`/`humidity_max`.
- **Creación**: Si un valor excede los límites, se inserta un registro en la tabla `alerts`.
- **Severidad**:
  - `warning`: Desviación menor a 2 °C del límite.
  - `critical`: Desviación mayor a 2 °C del límite.
- **Visualización**: Las alertas se muestran en el panel derecho con animación. Las filas de dispositivos en alerta tienen fondo rojizo.
- **Persistencia**: Las alertas permanecen en la BD hasta que se resuelven (campo `resolved = 0`).

---

## 🖥️ Secciones del Dashboard

### 1. Barra Superior

```
┌──────────────────────────────────────────────────────────────────┐
│  🏥 Hospital LoRaWAN Monitor    ● EN VIVO  14:32:15   🔄       │
│  Sistema de Monitoreo de Temperatura y Humedad                   │
└──────────────────────────────────────────────────────────────────┘
```

- Logotipo y nombre del sistema.
- Indicador **EN VIVO** con punto pulsante.
- Reloj de última actualización.
- Botón de refrescar manual.

### 2. Cards de Resumen

| Card | Descripción |
|------|-------------|
| 🧠 **Total Dispositivos** | Número total de sensores monitoreados (200) |
| ✅ **Dispositivos OK** | Cuántos están operando dentro de rango |
| ⚠️ **Alertas Activas** | Cantidad de dispositivos en estado de alerta |
| 💾 **Total Lecturas** | Lecturas acumuladas en la BD |
| 🕐 **Lecturas 24h** | Lecturas generadas en las últimas 24 horas |

### 3. Filtros

- **Filtro por Tipo**: Selecciona un tipo específico de dispositivo (Vitrina, Frigobar, Freezer, etc.).
- **Búsqueda**: Busca por nombre de dispositivo o ubicación.
- **Filtro por Estado**: Botones para ver **Todos**, solo **OK** o solo **Alerta**.

### 4. Gráfico de Tendencia (Chart.js)

- Selecciona un dispositivo del menú desplegable.
- Muestra un gráfico de líneas con las últimas **60 lecturas**.
- **Eje Y izquierdo**: Temperatura (°C) — línea azul.
- **Eje Y derecho**: Humedad (%HR) — línea verde (solo para sensores ambientales).
- Actualización automática al seleccionar un dispositivo.

### 5. Tabla de Dispositivos

| Columna | Contenido |
|---------|-----------|
| # | ID numérico del dispositivo |
| Nombre | Nombre descriptivo (enlace para ver gráfico) |
| Tipo | Tipo abreviado de dispositivo |
| Ubicación | Dónde está instalado |
| Temp. (°C) | Última lectura de temperatura (coloreada) |
| Humedad (%HR) | Última lectura de humedad si aplica |
| Estado | Badge **OK** (verde) o **Alerta** (rojo pulsante) |
| Últ. Lectura | Timestamp de la última lectura |

**Código de colores de temperatura:**
- <span style="color:green">**Verde**</span>: dentro de rango
- <span style="color:orange">**Naranja**</span>: fuera de rango por menos de 3 °C
- <span style="color:red">**Rojo**</span>: fuera de rango por más de 3 °C

### 6. Panel de Alertas

Lista las últimas **20 alertas activas**, cada una mostrando:
- Nombre del dispositivo en alerta
- Timestamp de la alerta
- Mensaje descriptivo (ej. "Temperatura alta: 9.5 °C (máximo: 8.0 °C)")
- Badge de severidad: **CRÍTICA** (rojo) o **ADVERTENCIA** (naranja)

### 7. Tabla de Últimas Lecturas

Muestra las últimas **100 lecturas** generadas, con opción de refrescar manualmente.

---

## 📊 Tipos de Dispositivos

| ID | Tipo | Clave | Cantidad | Rango Temp. °C | Rango HR % | Aplicación |
|----|------|-------|----------|----------------|------------|------------|
| 1 | 🧊 Vitrina Refrigerada | `vitrina_refrigerada` | 46 | 2.0 – 8.0 | — | Pasillos, farmacia, quirófanos |
| 2 | 🧊 Frigobar | `frigobar` | 33 | 2.0 – 8.0 | — | Enfermerías, pisos, cafetería |
| 3 | 🧊 Refrigerador Combinado (Frío) | `refri_combinado_frio` | 20 | 2.0 – 8.0 | — | Cocina, almacén, comedor |
| 4 | 🧊 Refrigerador Combinado (Congelador) | `refri_combinado_cong` | 20 | **-20.5 – -19.5** | — | Cocina, almacén de congelados |
| 5 | 🧊 Freezer -20°C | `freezer_20` | 13 | **-20.5 – -19.5** | — | Almacén frío, laboratorio, farmacia |
| 6 | 🧊 Vitrina 2 Puertas | `vitrina_2p` | 8 | 2.0 – 8.0 | — | Cafeterías, comedores |
| 7 | 🧊 Freezer -80°C | `freezer_80` | 4 | **-80.5 – -79.5** | — | Biobanco, investigación, patología |
| 8 | 🧊 Freezer Horizontal | `freezer_horizontal` | 4 | **-20.5 – -19.5** | — | Almacén frío, cocina |
| 9 | ⚰️ Cámara Mortuoria | `camara_mortuoria` | 2 | 2.0 – 8.0 | — | Morgue, tanatorio |
| 10 | 🌡️ Monitoreo Ambiental | `ambiental` | 30 | 20.0 – 24.0 | **30% – 60%** | Salas de espera, consultorios, UCI |
| 11 | 🌡️ Termostato con Sonda | `termostato_sonda` | 20 | **-50.0 – 100.0** | — | Calderas, cuartos eléctricos, servidores |
| | **TOTAL** | | **200** | | | |

**Nota**: Los freezers tienen rangos con tolerancia (ej. -20.5 a -19.5 en lugar de -20.0 fijo) para evitar falsas alertas por variaciones normales de operación.

---

## 📡 Conexión con LoRaWAN

### En Modo Simulación (Actual)

El sistema actual **no requiere hardware físico**. El generador de datos mock (`data_generator.py`) simula la llegada de datos LoRaWAN. Esto es ideal para:
- Demostraciones y presentaciones.
- Desarrollo y pruebas de funcionalidad.
- Capacitación del personal.

### En Producción con LoRaWAN Real

Para conectar sensores LoRaWAN reales, se requiere:

1. **Gateway LoRaWAN**: Un gateway (ej. Dragino LG02, RAK7249, Kerlink) instalado en el hospital que cubra todas las áreas.
2. **Servidor de Red**: Cuenta en **The Things Network (TTN)** o **ChirpStack** (on-premise).
3. **Integración MQTT o HTTP**: Configurar un webhook o suscripción MQTT desde el servidor de red hacia el dashboard.

#### Diagrama de Conexión Real

```
[Sensor LoRaWAN] ──RF──▶ [Gateway LoRaWAN] ──IP──▶ [TTN/ChirpStack]
                                                          │
                                                   MQTT/HTTP
                                                          │
                                          ┌───────────────▼──────────┐
                                          │   hospital-lorawan-      │
                                          │   dashboard              │
                                          │                          │
                                          │   data_generator.py      │
                                          │   (deshabilitado en      │
                                          │    producción)           │
                                          └──────────────────────────┘
```

#### Código de Ejemplo para Integración MQTT

```python
# mqtt_integration.py - Recibir datos de TTN vía MQTT
import paho.mqtt.client as mqtt
import json
from database import get_connection

# Configuración TTN
TTN_APP_ID = "tu-app-id"
TTN_ACCESS_KEY = "ttn-account-v2.xxxxxxxxx"
TTN_BROKER = "eu1.cloud.thethings.network"
TTN_PORT = 1883

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje desde TTN."""
    try:
        payload = json.loads(msg.payload)
        # Extraer datos del payload (depende del formato del sensor)
        device_eui = payload.get("end_device_ids", {}).get("dev_eui")
        decoded = payload.get("uplink_message", {}).get("decoded_payload", {})
        
        temperature = decoded.get("temperature")
        humidity = decoded.get("humidity")
        
        if temperature is not None:
            # Buscar el device_id por EUI
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM devices WHERE device_type = ? AND active = 1 LIMIT 1",
                (device_eui,)
            )
            # ... insertar lectura y evaluar alertas
            conn.close()
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

# Configurar cliente MQTT
client = mqtt.Client()
client.username_pw_set(TTN_APP_ID, TTN_ACCESS_KEY)
client.on_message = on_message
client.connect(TTN_BROKER, TTN_PORT, 60)
client.subscribe(f"v3/{TTN_APP_ID}/devices/+/up")
client.loop_forever()
```

---

## 💡 Ejemplos de Uso

### Interpretación del Dashboard

**Escenario 1: Todo normal**
- Todas las cards muestran "Dispositivos OK" = 200.
- Todas las filas tienen badge **OK** verde.
- El panel de alertas muestra "No hay alertas activas" con un check verde.

**Escenario 2: Alerta de temperatura alta**
- La card "Alertas Activas" muestra un número > 0.
- Una o más filas tienen badge **Alerta** rojo pulsante y fondo rojizo.
- La temperatura aparece en 🟠 naranja o 🔴 rojo.
- El panel de alertas muestra una tarjeta con el mensaje: *"Temperatura alta: 9.5 °C (máximo: 8.0 °C)"*.

**Escenario 3: Investigar un dispositivo**
1. Haz clic en el nombre del dispositivo en la tabla. Se selecciona automáticamente en el gráfico.
2. Observa la tendencia de las últimas 60 lecturas (30 minutos).
3. Si la temperatura ha ido subiendo gradualmente, podría indicar una falla incipiente del equipo.

**Escenario 4: Filtrar solo freezers -80°C**
1. En el filtro por tipo, selecciona "Freezer -80°C".
2. La tabla muestra solo los 4 freezers de -80°C.
3. Verifica que todos estén en -80.5°C a -79.5°C.

### Casos de Uso Reales

| Usuario | Acción | Beneficio |
|---------|--------|-----------|
| 🔬 **Técnico de Laboratorio** | Monitorea freezers -80°C del biobanco | Protege muestras de investigación |
| 💊 **Farmacéutico** | Verifica temperatura de vitrinas de medicamentos | Garantiza cadena de frío de vacunas |
| 🏥 **Ingeniero Clínico** | Recibe alertas tempranas de equipos fallando | Programa mantenimiento preventivo |
| 📋 **Administrador** | Revisa reportes históricos de temperatura | Cumple normativas sanitarias |

---

## ⚙️ Calibración y Configuración

### Ajustar Rangos de Temperatura

Todos los rangos se configuran en `config.py` en el diccionario `DEVICE_TYPES`:

```python
DEVICE_TYPES = {
    "vitrina_refrigerada": {
        "count": 46,
        "temp_min": 2.0,      # ← Cambia aquí el límite inferior
        "temp_max": 8.0,      # ← Cambia aquí el límite superior
        "display_name": "Vitrina Refrigerada",
    },
    "ambiental": {
        "count": 30,
        "temp_min": 20.0,
        "temp_max": 24.0,
        "humidity_min": 30.0,   # ← Humedad mínima
        "humidity_max": 60.0,   # ← Humedad máxima
        "display_name": "Monitoreo Ambiental",
    },
    # ... más tipos
}
```

### Ajustar Intervalos de Tiempo

```python
GENERATION_INTERVAL = 30       # Segundos entre rondas de generación de datos
POLLING_INTERVAL = 10          # Segundos entre polling del frontend
LATEST_READINGS_COUNT = 60     # Lecturas en el gráfico de tendencia
ALERTS_DISPLAY_COUNT = 20      # Alertas visibles en el panel
RECENT_READINGS_COUNT = 100    # Lecturas en la tabla de histórico
```

### Ajustar Probabilidad de Fuera de Rango

```python
OUT_OF_RANGE_PROBABILITY = 0.10  # 10% de lecturas fuera de rango
```

### Ajustar la Cantidad de Dispositivos

Para cambiar cuántos dispositivos de cada tipo se crean, modifica el valor `count` en `DEVICE_TYPES`. La próxima vez que se reinicie la aplicación (con la BD vacía), se crearán los nuevos dispositivos.

> **⚠️ Importante**: Si ya existe una BD con datos, los cambios en `DEVICE_TYPES` no se aplicarán automáticamente. Debes eliminar `hospital_lorawan.db` y reiniciar la app.

---

## ⚠️ Advertencias y Precauciones

1.  **Datos simulados**: Por defecto, el sistema genera datos mock. **No uses estos datos para tomar decisiones clínicas o de mantenimiento reales** sin conectar sensores físicos.

2.  **No es un dispositivo médico**: Este sistema es una herramienta de monitoreo, no un equipo médico certificado. No reemplaza los sistemas de control de temperatura propios de cada equipo de refrigeración.

3.  **Validación en producción**: Antes de usar en producción:
    - Conectar a una red LoRaWAN real (TTN o ChirpStack).
    - Deshabilitar el generador mock (`data_generator.py`).
    - Agregar autenticación y HTTPS.
    - Configurar respaldo de BD (SQLite no es ideal para alta concurrencia).
    - Considerar migrar a PostgreSQL para escalabilidad.

4.  **La BD SQLite no es para alta concurrencia**: Si múltiples instancias del dashboard o procesos externos escriben simultáneamente, pueden ocurrir bloqueos. Para producción con muchos sensores, migra a PostgreSQL.

5.  **Sin autenticación**: La versión actual no incluye login. No expongas el dashboard a Internet sin agregar un proxy reverso con autenticación (Nginx + HTTP Basic Auth, o Auth0).

6.  **Rangos de freezers**: Los freezers tienen rangos con tolerancia (±0.5 °C) para evitar falsas alertas. Si tu equipo requiere precisión más estricta, ajusta los rangos en `config.py`.

7.  **Pérdida de datos**: La BD SQLite es un archivo local. Si se corrompe o elimina, se pierde el histórico. Configura respaldos periódicos.

---

## 📄 Licencia y Autor

### Autor

**Wander Cáceres H.** — [@wanderc137](https://github.com/wanderc137)

### Licencia

Este proyecto se distribuye bajo la licencia **MIT**.

```
MIT License

Copyright (c) 2025 Wander Cáceres H.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Agradecimientos

- **[Flask](https://flask.palletsprojects.com/)** — Framework web ligero y poderoso.
- **[Chart.js](https://www.chartjs.org/)** — Librería de gráficos JavaScript de código abierto.
- **[Font Awesome](https://fontawesome.com/)** — Iconografía profesional gratuita.
- **[The Things Network](https://www.thethingsnetwork.org/)** — Red LoRaWAN abierta global.
- **[SQLite](https://www.sqlite.org/)** — Base de datos embebida confiable.

---

<p align="center">
  Hecho con ❤️ para mejorar la seguridad hospitalaria<br>
  <sub>Monitoreando la cadena de frío, salvando vidas</sub>
</p>
