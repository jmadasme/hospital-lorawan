# 🛠️ Guía del Desarrollador — Hospital LoRaWAN Monitor

**Documentación Técnica para Desarrolladores**  
*Versión 1.0.0 — Junio 2026*

---

## 1. Estructura del Proyecto

```
hospital-lorawan-dashboard/
│
├── app.py                 # Punto de entrada. Inicializa BD, generador y Flask.
├── config.py              # Configuración: rangos, intervalos, puertos.
├── database.py            # CRUD SQLite, helpers de consulta, seed de datos.
├── data_generator.py      # Generador de datos mock LoRaWAN (thread daemon).
├── models.py              # Dataclasses: Device, Reading, Alert.
├── routes.py              # API REST endpoints (Blueprint Flask).
├── requirements.txt       # Dependencias: flask, flask-cors.
├── hospital_lorawan.db    # Base de datos SQLite (se crea al iniciar).
│
├── PLAN.md                # Plan de desarrollo original.
├── AUDIT_REPORT.md        # Reporte de auditoría de código.
├── README.md              # Documentación principal del proyecto.
│
├── docs/
│   ├── datasheet.md       # Documentación de usuario.
│   └── developer.md       # Documentación del desarrollador (este archivo).
│
├── templates/
│   └── dashboard.html     # Plantilla HTML del dashboard (Jinja2).
│
├── static/
│   ├── css/
│   │   └── dashboard.css  # Estilos CSS profesionales.
│   └── js/
│       └── dashboard.js   # Lógica frontend (polling, Chart.js, filtros).
│
└── __pycache__/           # Caché de bytecode Python (generado automáticamente).
```

---

## 2. Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIAGRAMA DE FLUJO DE DATOS                           │
└─────────────────────────────────────────────────────────────────────────┘

  INICIO (app.py)
       │
       ▼
  initialize()
       │
       ├─── 1. initialize_database()  [database.py]
       │        │
       │        ├── create_tables()   → Crea devices, readings, alerts
       │        └── seed_devices()    → Inserta 200 dispositivos
       │
       └─── 2. start_generator()      [data_generator.py]
                │
                ▼
        _generator_loop()  (thread daemon)
                │
                ▼
        LOOP PRINCIPAL (cada 30s):
                │
                ▼
        generate_all_readings()
                │
                ├── query_all("SELECT * FROM devices WHERE active=1")
                │
                ▼
        for each device:
                │
                ├── generate_reading_value()  → temperatura
                ├── generate_humidity_value() → humedad (si aplica)
                │
                ▼
            INSERT INTO readings
                │
                ▼
            ¿Está fuera de rango?
                ├── NO  → Continuar
                │
                └── SÍ → INSERT INTO alerts (severity: warning/critical)
                │
                ▼
        time.sleep(30)

  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

  FRONTEND (dashboard.js)
       │
       ▼
  DOMContentLoaded
       │
       ├── loadInitialData()
       │    ├── fetchStats()              GET /api/stats
       │    ├── fetchDevicesForSelect()   GET /api/devices
       │    ├── fetchAndRenderReadings()  GET /api/readings
       │    └── pollData()
       │         ├── GET /api/readings/current  → renderDevicesTable()
       │         └── GET /api/alerts            → renderAlerts()
       │
       ├── setInterval(pollData, 10000)   ← polling cada 10s
       │
       └── setInterval(updateFooterClock, 1000)

  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

  USUARIO INTERACTÚA
       │
       ├── Selecciona filtro  → applyFilters() → renderDevicesTable()
       │
       ├── Busca dispositivo  → applyFilters() → renderDevicesTable()
       │
       ├── Clic en dispositivo → selectDeviceForChart()
       │    └── GET /api/readings/latest/<id> → updateChart()
       │
       └── Clic "Refrescar"   → refreshData() / refreshReadings()
```

---

## 3. Explicación Detallada de Cada Archivo

### 3.1 `app.py` — Punto de Entrada

**Propósito**: Arranca la aplicación Flask, inicializa la base de datos, registra las rutas y lanza el generador de datos.

**Flujo de arranque**:

1. Crea la app Flask con `Flask(__name__)`.
2. Habilita CORS con `flask_cors.CORS(app)`.
3. Carga configuración desde `config.py`.
4. Define la función `initialize()` que:
   - Llama a `database.initialize_database()` (crea tablas + seed).
   - Llama a `data_generator.start_generator()` (inicia thread daemon).
5. Define ruta raíz `GET /` → renderiza `dashboard.html`.
6. Define ruta `GET /health` → retorna JSON de salud.
7. Registra el Blueprint de rutas API desde `routes.py`.
8. En `if __name__ == "__main__"`: llama a `initialize()` y arranca Flask.

**Funciones clave**:

| Función | Descripción |
|---------|-------------|
| `initialize()` | Orquesta la inicialización de BD y generador |
| `index()` | Sirve el dashboard HTML |
| `health()` | Endpoint de verificación de salud |

### 3.2 `config.py` — Configuración

**Propósito**: Concentra todas las constantes de configuración del sistema en un solo lugar.

**Secciones**:

- **DB_PATH**: Ruta absoluta al archivo SQLite.
- **Intervalos**: `GENERATION_INTERVAL` (30s), `POLLING_INTERVAL` (10s).
- **Cantidades**: `LATEST_READINGS_COUNT` (60), `ALERTS_DISPLAY_COUNT` (20), `RECENT_READINGS_COUNT` (100).
- **Probabilidad**: `OUT_OF_RANGE_PROBABILITY` (0.10).
- **DEVICE_TYPES**: Diccionario con 11 tipos, cada uno con `count`, `temp_min`, `temp_max`, opcionalmente `humidity_min`/`humidity_max`, y `display_name`.
- **Flask**: `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`.

**Constantes principales**:

```python
DB_PATH = os.path.join(BASE_DIR, "hospital_lorawan.db")
GENERATION_INTERVAL = 30       # segundos
POLLING_INTERVAL = 10          # segundos
OUT_OF_RANGE_PROBABILITY = 0.10  # 10%
```

### 3.3 `models.py` — Modelos de Datos

**Propósito**: Define las dataclasses que representan las entidades del dominio.

**Clases**:

| Clase | Campos | Propósito |
|-------|--------|-----------|
| `Device` | `id`, `device_type`, `name`, `location`, `temp_min`, `temp_max`, `humidity_min`, `humidity_max`, `active` | Representa un sensor físico |
| `Reading` | `id`, `device_id`, `temperature`, `humidity`, `timestamp` | Una lectura de sensor |
| `Alert` | `id`, `device_id`, `reading_id`, `parameter`, `value`, `min_limit`, `max_limit`, `message`, `severity`, `resolved`, `created_at` | Alerta generada |

Cada clase tiene un método `to_dict()` que serializa usando `dataclasses.asdict()` para respuestas JSON.

**Uso**: Las dataclasses se usan en `database.py` como tipos de retorno tipados para las funciones `query_device()`, `query_latest_reading()`, etc.

### 3.4 `database.py` — Base de Datos

**Propósito**: Maneja toda la interacción con SQLite: conexión, creación de tablas, seed de datos y consultas.

**Funciones principales**:

| Función | Retorno | Descripción |
|---------|---------|-------------|
| `get_connection()` | `sqlite3.Connection` | Conexión con row_factory=Row, WAL mode, foreign keys |
| `create_tables()` | `None` | Crea devices, readings, alerts con índices |
| `seed_devices()` | `None` | Inserta 200 dispositivos con nombres y ubicaciones |
| `query_all(query, params)` | `list[dict]` | SELECT genérico, retorna lista de dicts |
| `query_one(query, params)` | `dict` o `None` | SELECT genérico, retorna un dict |
| `query_device(device_id)` | `Device` o `None` | Dispositivo por ID |
| `query_all_devices(type, search)` | `list[Device]` | Dispositivos con filtros |
| `query_latest_reading(device_id)` | `Reading` o `None` | Última lectura de un dispositivo |
| `query_latest_readings(device_id, limit)` | `list[Reading]` | Últimas N lecturas |
| `query_active_alerts(device_id, limit)` | `list[Alert]` | Alertas activas |
| `execute(query, params)` | `int` | INSERT/UPDATE/DELETE, retorna lastrowid |
| `initialize_database()` | `None` | Orquesta create_tables + seed_devices |

**Helpers de conversión**: `_dict_to_device()`, `_dict_to_reading()`, `_dict_to_alert()` convierten diccionarios a dataclasses, filtrando solo campos válidos.

### 3.5 `data_generator.py` — Generador de Datos Mock

**Propósito**: Simula la llegada de datos desde sensores LoRaWAN reales. Ejecuta en un thread daemon independiente.

**Funciones clave**:

| Función | Descripción |
|---------|-------------|
| `_gaussian_value(center, min_val, max_val, std_dev_factor)` | Genera valor con distribución gaussiana limitado al rango |
| `_is_temperature_stable(device_type)` | True para freezers (variación mínima) |
| `generate_reading_value(device_type, temp_min, temp_max)` | Genera temperatura con 10% de probabilidad de fuera de rango |
| `generate_humidity_value(humidity_min, humidity_max)` | Genera humedad (solo para ambientales) |
| `insert_reading_and_check_alerts(...)` | Inserta lectura y evalúa alertas |
| `generate_all_readings()` | Genera lecturas para todos los dispositivos activos |
| `start_generator()` | Inicia el thread daemon |
| `stop_generator()` | Detiene el generador |

**Algoritmo de generación de temperatura**:

```
1. Calcular punto medio: center = (temp_min + temp_max) / 2
2. 10% probabilidad de valor fuera de rango:
   - Elegir dirección (arriba/abajo)
   - Desviación: 5%-30% del rango
3. 90% probabilidad de valor dentro de rango:
   - Freezers: gaussiana con std_dev = 0.3
   - Otros: gaussiana con std_dev = 15% del rango
4. Acotar al rango [min_val, max_val] (excepto fuera de rango)
```

**Algoritmo de evaluación de alertas**:

```
Por cada lectura insertada:
  SI temperatura < temp_min:
    → Alerta "Temperatura baja: X°C (mínimo: Y°C)"
  SI temperatura > temp_max:
    → Alerta "Temperatura alta: X°C (máximo: Y°C)"
  SI humedad no es None Y humedad fuera de rango:
    → Alerta de humedad

  Severidad:
    - critical: |desviación| > 2°C
    - warning: |desviación| ≤ 2°C
```

### 3.6 `routes.py` — API REST

**Propósito**: Define los endpoints de la API REST usando Flask Blueprint.

**Blueprint**: `api_bp` con prefijo (ninguno, las rutas son absolutas como `/api/...`).

**Endpoints**: Ver sección 4.

### 3.7 `templates/dashboard.html` — Frontend HTML

**Propósito**: Plantilla HTML del dashboard. Usa Font Awesome para íconos, Chart.js para gráficos y CSS personalizado.

**Secciones**:
- `<header>`: Barra superior con logo, indicador EN VIVO, reloj.
- `<main>`: Contiene las 7 secciones del dashboard.
- `<footer>`: Información del sistema y reloj.
- `<script>`: Carga `dashboard.js`.

### 3.8 `static/js/dashboard.js` — Lógica Frontend

**Propósito**: Toda la lógica del lado del cliente: polling, renderizado, gráficos, filtros.

**Arquitectura**:

- **Estado global** (`state`): `currentReadings`, `alerts`, `stats`, `statusFilter`, `chart`, `isFirstLoad`.
- **Polling**: `setInterval(pollData, 10000)`.
- **Chart.js**: `getOrCreateChart()` crea/configura el gráfico. `updateChart()` carga datos.
- **Renderizado**: `renderDevicesTable()`, `renderAlerts()`, `renderReadingsTable()`, `renderStats()`.
- **Filtros**: `applyFilters()`, `setStatusFilter()`.
- **Helpers**: `fetchJSON(url)`, `formatDeviceType(type)`, `updateFooterClock()`.

**Funciones principales**:

| Función | Descripción |
|---------|-------------|
| `loadInitialData()` | Carga datos iniciales al cargar la página |
| `pollData()` | Polling periódico: lecturas actuales + alertas + stats |
| `fetchJSON(url)` | Helper fetch con manejo de errores |
| `fetchStats()` | Obtiene y renderiza estadísticas |
| `renderStats(stats)` | Actualiza cards de resumen |
| `updateSummaryCards(readings)` | Calcula y muestra dispositivos OK |
| `fetchDevicesForSelect()` | Puebla el select del gráfico |
| `getOrCreateChart()` | Crea o retorna instancia de Chart.js |
| `updateChart()` | Carga datos en el gráfico |
| `renderDevicesTable(readings)` | Renderiza tabla con filtros |
| `renderAlerts(alerts)` | Renderiza panel de alertas |
| `renderReadingsTable(readings)` | Renderiza tabla de lecturas |
| `applyFilters()` | Aplica filtros de tipo y búsqueda |
| `setStatusFilter(status, btn)` | Cambia filtro de estado |
| `selectDeviceForChart(id, name)` | Selecciona dispositivo en gráfico |
| `refreshData()` | Refresca datos manualmente |
| `refreshReadings()` | Refresca tabla de lecturas |

### 3.9 `static/css/dashboard.css` — Estilos

**Propósito**: Estilos profesionales con tema médico/hospitalario.

**Características**:
- Variables CSS para paleta de colores médicos (azules, verdes, rojos).
- Diseño responsive (3 breakpoints: 1024, 768, 480 px).
- Animaciones: pulso del indicador EN VIVO, fade-in de alertas, spin de refresh.
- Scrollbars personalizados.
- Tablas con cabeceras fijas (sticky headers).

---

## 4. API REST Completa

### 4.1 `GET /api/devices`

Lista todos los dispositivos activos.

**Query params**:

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `device_type` | string | No | Filtrar por tipo (ej. `freezer_80`) |
| `search` | string | No | Buscar por nombre o ubicación |

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "device_type": "vitrina_refrigerada",
      "name": "Vitrina Refrigerada #001",
      "location": "Pasillo A",
      "temp_min": 2.0,
      "temp_max": 8.0,
      "humidity_min": null,
      "humidity_max": null,
      "active": 1
    }
  ],
  "count": 200
}
```

### 4.2 `GET /api/devices/<device_id>`

Detalle de un dispositivo, incluyendo su última lectura.

**Path params**: `device_id` (int)

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "device_type": "vitrina_refrigerada",
    "name": "Vitrina Refrigerada #001",
    "location": "Pasillo A",
    "temp_min": 2.0,
    "temp_max": 8.0,
    "humidity_min": null,
    "humidity_max": null,
    "active": 1,
    "last_reading": {
      "id": 15234,
      "device_id": 1,
      "temperature": 5.2,
      "humidity": null,
      "timestamp": "2026-06-10 14:30:00"
    }
  }
}
```

**Errores**:
- `404`: Dispositivo no encontrado

### 4.3 `GET /api/readings`

Últimas lecturas del sistema.

**Query params**:

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `limit` | int | No | Cantidad de lecturas (default: 100) |
| `device_id` | int | No | Filtrar por dispositivo |

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": [
    {
      "id": 15234,
      "device_id": 1,
      "temperature": 5.2,
      "humidity": null,
      "timestamp": "2026-06-10 14:30:00",
      "device_name": "Vitrina Refrigerada #001",
      "device_type": "vitrina_refrigerada"
    }
  ],
  "count": 100
}
```

### 4.4 `GET /api/readings/current`

Retorna la **última lectura de cada dispositivo activo**, incluyendo estado de alerta. Es el endpoint principal para el polling del frontend.

**Query params**: Ninguno.

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": [
    {
      "device_id": 1,
      "device_type": "vitrina_refrigerada",
      "name": "Vitrina Refrigerada #001",
      "location": "Pasillo A",
      "temp_min": 2.0,
      "temp_max": 8.0,
      "humidity_min": null,
      "humidity_max": null,
      "reading_id": 15234,
      "temperature": 5.2,
      "humidity": null,
      "timestamp": "2026-06-10 14:30:00",
      "alert_id": null,
      "alert_severity": null,
      "alert_message": null,
      "status": "ok"
    }
  ],
  "count": 200
}
```

**Campos calculados**:

| Campo | Descripción |
|-------|-------------|
| `status` | `"ok"` si está en rango, `"alert"` si fuera de rango o tiene alerta activa |

### 4.5 `GET /api/readings/latest/<device_id>`

Últimas N lecturas de un dispositivo específico. Diseñado para alimentar gráficos Chart.js.

**Path params**: `device_id` (int)

**Query params**: Ninguno (usa `LATEST_READINGS_COUNT` de config.py, default 60).

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": [
    {
      "id": 15234,
      "device_id": 1,
      "temperature": 5.2,
      "humidity": null,
      "timestamp": "2026-06-10 14:30:00",
      "device_name": "Vitrina Refrigerada #001",
      "device_type": "vitrina_refrigerada"
    }
  ],
  "count": 60
}
```

**Nota**: Los datos se retornan en orden cronológico ascendente (el primer elemento es el más antiguo) para facilitar el renderizado del gráfico.

### 4.6 `GET /api/alerts`

Alertas activas (no resueltas).

**Query params**:

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `limit` | int | No | Cantidad de alertas (default: 20) |
| `device_id` | int | No | Filtrar por dispositivo |

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": [
    {
      "id": 42,
      "device_id": 15,
      "reading_id": 15234,
      "parameter": "temperature",
      "value": 9.5,
      "min_limit": 2.0,
      "max_limit": 8.0,
      "message": "Temperatura alta: 9.5°C (máximo: 8.0°C)",
      "severity": "warning",
      "resolved": 0,
      "created_at": "2026-06-10 14:30:00",
      "device_name": "Vitrina Refrigerada #015",
      "device_type": "vitrina_refrigerada",
      "location": "Farmacia Central"
    }
  ],
  "count": 5
}
```

### 4.7 `GET /api/stats`

Estadísticas generales del sistema.

**Query params**: Ninguno.

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "data": {
    "total_devices": 200,
    "devices_with_alerts": 3,
    "total_readings": 15234,
    "total_alerts": 5,
    "last_update": "2026-06-10 14:30:00",
    "readings_24h": 57600,
    "type_distribution": [
      {"device_type": "ambiental", "count": 30},
      {"device_type": "camara_mortuoria", "count": 2}
    ],
    "recent_alerts": []
  }
}
```

### 4.8 `POST /api/generate`

Fuerza la generación inmediata de una ronda de lecturas para todos los dispositivos.

**Headers**:
- `Content-Type: application/json` o `application/x-www-form-urlencoded`

**Body**: Vacío o `{}`.

**Ejemplo de respuesta**:
```json
{
  "success": true,
  "message": "Generadas 200 lecturas correctamente.",
  "count": 200
}
```

**Errores**:
- `415`: Content-Type no soportado
- `500`: Error interno al generar lecturas

### 4.9 `GET /health`

Verificación de salud del servicio.

**Ejemplo de respuesta**:
```json
{
  "status": "ok",
  "service": "Hospital LoRaWAN Dashboard",
  "version": "1.0.0"
}
```

---

## 5. Base de Datos

### 5.1 Esquema Relacional

```
┌──────────────────────────────────────────────────────────┐
│                      devices                              │
├──────────────┬──────────────┬────────────────────────────┤
│  id          │ INTEGER      │ PK, AUTOINCREMENT          │
│  device_type │ TEXT         │ NOT NULL, índice           │
│  name        │ TEXT         │ NOT NULL, único por tipo   │
│  location    │ TEXT         │ Ubicación física           │
│  temp_min    │ REAL         │ Límite inferior temp.      │
│  temp_max    │ REAL         │ Límite superior temp.      │
│  humidity_min│ REAL         │ NULL si no mide humedad    │
│  humidity_max│ REAL         │ NULL si no mide humedad    │
│  active      │ INTEGER      │ DEFAULT 1, soft-delete     │
└──────────────┴──────────────┴────────────────────────────┘
         │ 1
         │
         │ N
┌──────────────┬──────────────┬────────────────────────────┐
│                      readings                             │
├──────────────┬──────────────┬────────────────────────────┤
│  id          │ INTEGER      │ PK, AUTOINCREMENT          │
│  device_id   │ INTEGER      │ FK → devices(id), ÍNDICE  │
│  temperature │ REAL         │ NOT NULL                   │
│  humidity    │ REAL         │ NULL                       │
│  timestamp   │ DATETIME     │ DEFAULT CURRENT_TIMESTAMP  │
│              │              │ ÍNDICE                     │
└──────────────┴──────────────┴────────────────────────────┘
         │
         │ 0..1
         │
┌──────────────┬──────────────┬────────────────────────────┐
│                      alerts                               │
├──────────────┬──────────────┬────────────────────────────┤
│  id          │ INTEGER      │ PK, AUTOINCREMENT          │
│  device_id   │ INTEGER      │ FK → devices(id), ÍNDICE  │
│  reading_id  │ INTEGER      │ FK → readings(id)         │
│  parameter   │ TEXT         │ 'temperature' o 'humidity' │
│  value       │ REAL         │ Valor que causó la alerta  │
│  min_limit   │ REAL         │ Límite inferior            │
│  max_limit   │ REAL         │ Límite superior            │
│  message     │ TEXT         │ Mensaje descriptivo        │
│  severity    │ TEXT         │ 'warning' o 'critical'     │
│  resolved    │ INTEGER      │ DEFAULT 0, ÍNDICE          │
│  created_at  │ DATETIME     │ DEFAULT CURRENT_TIMESTAMP  │
│              │              │ ÍNDICE                     │
└──────────────┴──────────────┴────────────────────────────┘
```

### 5.2 Índices

```sql
-- Optimizar consultas por dispositivo
CREATE INDEX idx_readings_device_id ON readings(device_id);

-- Optimizar consultas por rango de tiempo
CREATE INDEX idx_readings_timestamp ON readings(timestamp);

-- Optimizar consultas de alertas por dispositivo
CREATE INDEX idx_alerts_device_id ON alerts(device_id);

-- Optimizar consultas de alertas activas (muy frecuentes)
CREATE INDEX idx_alerts_resolved ON alerts(resolved);

-- Optimizar ordenamiento de alertas recientes
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

### 5.3 Estrategia de Seed

La función `seed_devices()` en `database.py`:

1. Verifica si ya hay dispositivos en la BD (evita duplicados al reiniciar).
2. Para cada tipo en `DEVICE_TYPES`, crea N dispositivos.
3. Genera nombres secuenciales: `"Vitrina Refrigerada #001"`.
4. Asigna ubicaciones rotativas de una lista predefinida.
5. Inserta usando transacción única para velocidad.

### 5.4 Política de Retención de Datos

Actualmente **no hay política automática** de limpieza. La BD crece indefinidamente. Para producción, se recomienda:

```sql
-- Eliminar lecturas con más de 90 días (programar como cron job)
DELETE FROM readings WHERE timestamp < datetime('now', '-90 days');

-- Eliminar alertas resueltas con más de 30 días
DELETE FROM alerts WHERE resolved = 1 AND created_at < datetime('now', '-30 days');

-- Recuperar espacio
VACUUM;
```

---

## 6. Generador de Datos Mock

### 6.1 Estrategia de Simulación

El generador crea datos realistas usando los siguientes principios:

| Principio | Implementación |
|-----------|---------------|
| **Variación natural** | Distribución gaussiana alrededor del punto medio del rango |
| **Estabilidad de freezers** | Desviación estándar muy pequeña (0.3 °C) |
| **Fallos ocasionales** | 10% de probabilidad de valor fuera de rango |
| **Inercia térmica ambiental** | Variación lenta (std_dev_factor bajo) |
| **Saturación** | Valores acotados al rango [min_val, max_val] (excepto fuera de rango) |

### 6.2 ¿Por qué un generador mock?

1. **Desarrollo sin hardware**: Permite desarrollar y probar el dashboard sin necesidad de 200 sensores físicos.
2. **Demostraciones**: Ideal para presentaciones del sistema a stakeholders.
3. **Pruebas de alertas**: El 10% de fallos simulados permite probar el sistema de alertas sin esperar fallas reales.
4. **Pruebas de carga**: Genera datos masivos para probar rendimiento.

### 6.3 Configuración del Generador

```python
# En config.py
GENERATION_INTERVAL = 30       # Cada 30 segundos
OUT_OF_RANGE_PROBABILITY = 0.10  # 10% fuera de rango
```

### 6.4 Ciclo de Vida del Thread

```
start_generator()
  │
  └── _running = True
      └── threading.Thread(target=_generator_loop, daemon=True).start()
           │
           └── _generator_loop():
                 ├── generate_all_readings()  # Inmediato
                 └── while _running:
                       ├── time.sleep(30)
                       └── generate_all_readings()

stop_generator()
  └── _running = False
```

---

## 7. Conexión a LoRaWAN Real

### 7.1 Arquitectura de Producción

```
[Sensor LoRaWAN] ──RF──▶ [Gateway LoRaWAN]
                                │
                        (Internet / 4G)
                                │
                    [Servidor de Red LoRaWAN]
                          (TTN / ChirpStack)
                                │
                         (MQTT / HTTP)
                                │
                    ┌───────────▼───────────┐
                    │  Integración MQTT     │
                    │  (nuevo script)       │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Dashboard (Flask)    │
                    │  (data_generator     │
                    │   deshabilitado)      │
                    └───────────────────────┘
```

### 7.2 Integración con The Things Network (TTN)

Para recibir datos de TTN, necesitas un script separado que actúe como puente MQTT.

**Ejemplo de integración TTN**:

```python
# ttn_listener.py - Escucha datos de TTN y los inserta en la BD
import paho.mqtt.client as mqtt
import json
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración TTN
TTN_APP_ID = "tu-hospital-app"
TTN_ACCESS_KEY = "NNSXS.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
TTN_BROKER = "eu1.cloud.thethings.network"
TTN_PORT = 1883

DB_PATH = "hospital_lorawan.db"

# Mapeo de EUI a device_id (debe estar precargado en la BD)
EUI_TO_DEVICE = {
    "A81758FFFE012345": 1,
    "A81758FFFE012346": 2,
    # ... mapear todos los dispositivos
}

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        dev_eui = payload.get("end_device_ids", {}).get("dev_eui")
        decoded = payload.get("uplink_message", {}).get("decoded_payload", {})
        
        temperature = decoded.get("temperature")
        humidity = decoded.get("humidity")
        device_id = EUI_TO_DEVICE.get(dev_eui)
        
        if device_id and temperature is not None:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO readings (device_id, temperature, humidity) VALUES (?, ?, ?)",
                (device_id, temperature, humidity)
            )
            reading_id = cursor.lastrowid
            
            # Evaluar alertas (reutilizar lógica de data_generator)
            device = cursor.execute(
                "SELECT * FROM devices WHERE id = ?", (device_id,)
            ).fetchone()
            if device:
                temp_min, temp_max = device["temp_min"], device["temp_max"]
                if temperature < temp_min or temperature > temp_max:
                    severity = "critical" if abs(temperature - temp_min) > 2 or \
                        abs(temperature - temp_max) > 2 else "warning"
                    cursor.execute("""
                        INSERT INTO alerts (device_id, reading_id, parameter, value,
                            min_limit, max_limit, message, severity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (device_id, reading_id, "temperature", temperature,
                          temp_min, temp_max,
                          f"Temperatura {'baja' if temperature < temp_min else 'alta'}: "
                          f"{temperature}°C (límite: {temp_min if temperature < temp_min else temp_max}°C)",
                          severity))
            
            conn.commit()
            conn.close()
            logger.info(f"Lectura insertada: device={device_id}, temp={temperature}")
    except Exception as e:
        logger.error(f"Error procesando mensaje TTN: {e}")

client = mqtt.Client()
client.username_pw_set(TTN_APP_ID, TTN_ACCESS_KEY)
client.on_message = on_message
client.connect(TTN_BROKER, TTN_PORT, 60)
client.subscribe(f"v3/{TTN_APP_ID}/devices/+/up")
logger.info("Escuchando datos de TTN...")
client.loop_forever()
```

### 7.3 Integración con ChirpStack

ChirpStack expone una API HTTP REST y también soporta MQTT. La integración es similar a TTN.

### 7.4 Deshabilitar el Generador Mock en Producción

```python
# En app.py, modificar initialize() para no iniciar el generador:
def initialize():
    from database import initialize_database
    # from data_generator import start_generator  ← Comentar
    
    initialize_database()
    # start_generator()  ← No iniciar en producción
```

---

## 8. Cómo Extender el Sistema

### 8.1 Agregar un Nuevo Tipo de Dispositivo

1. **En `config.py`**, agrega una nueva entrada en `DEVICE_TYPES`:
```python
DEVICE_TYPES = {
    # ... tipos existentes ...
    "incubadora_neonatal": {
        "count": 10,
        "temp_min": 34.0,
        "temp_max": 37.0,
        "humidity_min": 40.0,
        "humidity_max": 60.0,
        "display_name": "Incubadora Neonatal",
    },
}
```

2. **En `database.py`**, agrega ubicaciones en `locations_by_type`:
```python
locations_by_type = {
    # ... ubicaciones existentes ...
    "incubadora_neonatal": [
        "UCI Neonatal", "Maternidad", "Pediatría",
    ],
}
```

3. **Opcional: En `data_generator.py`**, si el nuevo tipo tiene comportamiento especial, agrega su lógica en `_is_temperature_stable()`.

4. **Reinicia** la aplicación. Si ya existe una BD, elimínala primero.

### 8.2 Agregar un Nuevo Endpoint a la API

1. **En `routes.py`**, agrega una nueva función con el decorador adecuado:
```python
@api_bp.route("/api/devices/stats/<device_type>", methods=["GET"])
def get_device_type_stats(device_type: str):
    """
    GET /api/devices/stats/<device_type>
    Retorna estadísticas para un tipo específico de dispositivo.
    """
    stats = query_one("""
        SELECT 
            COUNT(*) as total,
            AVG(r.temperature) as avg_temp,
            MIN(r.temperature) as min_temp,
            MAX(r.temperature) as max_temp
        FROM devices d
        LEFT JOIN readings r ON r.device_id = d.id
        WHERE d.device_type = ? AND d.active = 1
    """, (device_type,))
    
    return jsonify({"success": True, "data": stats})
```

2. **Documenta** el nuevo endpoint en el README y en este archivo.

### 8.3 Agregar una Nueva Columna a la BD

1. **En `database.py`**, modifica `create_tables()`:
```python
cursor.executescript("""
    CREATE TABLE IF NOT EXISTS devices (
        -- ... columnas existentes ...
        last_maintenance DATETIME,  -- Nueva columna
        firmware_version TEXT       -- Nueva columna
    );
""")
```

2. **En `models.py`**, agrega el campo a la dataclass:
```python
@dataclass
class Device:
    # ... campos existentes ...
    last_maintenance: Optional[str] = None
    firmware_version: Optional[str] = None
```

3. **En `seed_devices()`**, incluye los nuevos campos.

4. **Actualiza** las consultas SQL según sea necesario.

### 8.4 Agregar Notificaciones (Email/Slack)

Puedes extender `data_generator.py` para enviar notificaciones cuando se genere una alerta crítica:

```python
def insert_reading_and_check_alerts(...):
    # ... código existente ...
    
    if severity == "critical":
        send_alert_notification(device_id, message)

def send_alert_notification(device_id: int, message: str):
    """Envía notificación por email, Slack, etc."""
    # Ejemplo: Integración con Slack Webhook
    import requests
    webhook_url = "https://hooks.slack.com/services/..."
    requests.post(webhook_url, json={"text": f"🚨 {message}"})
```

### 8.5 Migrar de SQLite a PostgreSQL

Para producción con alta concurrencia:

1. Instala `psycopg2-binary` y `sqlalchemy`.
2. Reemplaza `sqlite3.connect()` por `create_engine()` de SQLAlchemy.
3. Cambia los tipos de datos:
   - `INTEGER` → `SERIAL`
   - `REAL` → `DOUBLE PRECISION`
   - `TEXT` → `VARCHAR` o `TEXT`
   - `DATETIME` → `TIMESTAMP`
4. Actualiza las funciones de `database.py` para usar SQLAlchemy.
5. Configura la conexión en `config.py`.

---

## 9. Pruebas y Depuración

### 9.1 Endpoint de Salud

```bash
curl http://localhost:5000/health
# {"status":"ok","service":"Hospital LoRaWAN Dashboard","version":"1.0.0"}
```

### 9.2 Forzar Generación de Datos

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" -d '{}'
# {"success":true,"message":"Generadas 200 lecturas correctamente.","count":200}
```

### 9.3 Verificar Estado de Dispositivos

```bash
# Verificar dispositivos en alerta
curl -s http://localhost:5000/api/readings/current | python3 -m json.tool | grep '"status": "alert"'
```

### 9.4 Depuración de Alertas

```bash
# Ver últimas alertas con detalles
curl -s http://localhost:5000/api/alerts?limit=5 | python3 -m json.tool
```

### 9.5 Monitorear Logs en Tiempo Real

```bash
# Iniciar la app y observar logs
python app.py 2>&1 | grep -E "(ALERTA|ERROR|GENERADOR)"
```

---

## 10. Mejores Prácticas y Convenciones

### 10.1 Estilo de Código

- **Python**: Se sigue PEP 8 (nombres de funciones en `snake_case`, clases en `PascalCase`).
- **JavaScript**: camelCase para variables y funciones.
- **CSS**: BEM-like para clases (ej. `.status-badge`, `.temp-critical`).
- **Comentarios**: Docstrings en formato reStructuredText para funciones Python.
- **Logging**: Usar `logging` con niveles INFO/WARNING/ERROR.

### 10.2 Convenciones de Nombres

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Tipos de dispositivo | `snake_case` | `vitrina_refrigerada` |
| Nombres de dispositivos | Tipo + #ID | `Freezer -80°C #155` |
| Endpoints API | `snake_case` | `/api/readings/current` |
| Archivos Python | `snake_case` | `data_generator.py` |
| Clases Python | `PascalCase` | `class Reading:` |
| Funciones Python | `snake_case` | `generate_all_readings()` |
| Variables JS | `camelCase` | `currentReadings` |

### 10.3 Manejo de Errores

- **Backend**: Las funciones retornan `None` o lanzan excepciones capturadas con try/except.
- **API**: Los errores se retornan como JSON con `{"success": false, "error": "mensaje"}`.
- **Frontend**: Las promesas fetch tienen catch que registra el error en consola.

---

## 11. Referencias

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Chart.js Documentation**: https://www.chartjs.org/docs/
- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **LoRaWAN Specification**: https://lora-alliance.org/resource-hub/lorawan-specification-v1-1/
- **The Things Network**: https://www.thethingsnetwork.org/
- **ChirpStack**: https://www.chirpstack.io/

---

<p align="center">
  <sub>Documentación del desarrollador — Hospital LoRaWAN Monitor v1.0.0</sub><br>
  <sub>© 2026 Wander Cáceres H. — MIT License</sub>
</p>
