# 📋 Datasheet — Hospital LoRaWAN Monitor

**Documentación de Usuario**  
*Versión 1.0.0 — Junio 2026*

---

## 1. Especificaciones Técnicas

### 1.1 Generales

| Parámetro | Valor |
|-----------|-------|
| **Nombre del Sistema** | Hospital LoRaWAN Monitor |
| **Versión** | 1.0.0 |
| **Tipo** | Dashboard web de monitoreo IoT |
| **Propósito** | Monitoreo en tiempo real de temperatura y humedad en hospitales |
| **Idioma** | Español (México) |
| **Arquitectura** | Cliente-Servidor (Flask + SQLite + Chart.js) |

### 1.2 Capacidad del Sistema

| Parámetro | Valor |
|-----------|-------|
| **Dispositivos monitoreados** | 200 (configurable) |
| **Tipos de dispositivos** | 11 tipos |
| **Intervalo de generación de datos (mock)** | 30 segundos (configurable) |
| **Intervalo de polling frontend** | 10 segundos (configurable) |
| **Lecturas en gráfico de tendencia** | 60 (configurable) |
| **Alertas visibles** | 20 (configurable) |
| **Lecturas en tabla histórica** | 100 (configurable) |
| **Persistencia de datos** | Indefinida (SQLite, sin límite automático) |

### 1.3 Precisión de Simulación Mock

| Tipo de Dispositivo | Desviación Estándar | Variación |
|--------------------|-------------------|-----------|
| Freezers (-80°C, -20°C) | 0.3 °C | Mínima |
| Refrigeración (2-8°C) | 15% del rango | Moderada |
| Ambiental (20-24°C) | 10% del rango | Lenta (inercia térmica) |
| Termostato con sonda | 15% del rango | General |

---

## 2. Requisitos de Hardware

### 2.1 Servidor (Mínimo)

| Componente | Especificación |
|------------|----------------|
| **Procesador** | 2 núcleos, 2.0 GHz (x86_64 o ARM) |
| **RAM** | 1 GB |
| **Almacenamiento** | 500 MB libres + espacio para BD |
| **Red** | Conexión a Internet (para CDN de Chart.js y Font Awesome) |
| **SO** | Linux (Ubuntu 22.04+, Debian 12+, Raspberry Pi OS), macOS 12+, Windows 10+ (WSL2) |

### 2.2 Servidor (Recomendado para Producción)

| Componente | Especificación |
|------------|----------------|
| **Procesador** | 4 núcleos, 2.5 GHz |
| **RAM** | 4 GB |
| **Almacenamiento** | 10 GB SSD (para crecimiento de BD histórica) |
| **Red** | Conexión dedicada, estática o DDNS |
| **Proxy** | Nginx para reverso proxy, SSL, y servir archivos estáticos |

### 2.3 Cliente (Navegador Web)

| Navegador | Versión Mínima |
|-----------|---------------|
| Google Chrome | 90+ |
| Mozilla Firefox | 88+ |
| Microsoft Edge | 90+ |
| Apple Safari | 14+ |
| Opera | 76+ |

**Requisitos del cliente:**
- JavaScript habilitado
- Conexión a Internet (para cargar Chart.js y Font Awesome desde CDN)
- Resolución mínima recomendada: 1280 × 720 px
- Resolución óptima: 1920 × 1080 px

---

## 3. Requisitos de Software

### 3.1 Servidor

| Software | Versión | Propósito |
|----------|---------|-----------|
| Python | 3.10, 3.11, 3.12 | Entorno de ejecución |
| pip | 23+ | Gestor de paquetes |
| Flask | 3.0+ | Framework web |
| Flask-CORS | 4.0+ | Soporte CORS |
| SQLite3 | 3.x (incluido en Python) | Base de datos |

### 3.2 Cliente (Navegador)

No requiere instalación de software adicional. El dashboard es una aplicación web que se accede mediante navegador.

### 3.3 Dependencias Python

```
flask>=3.0.0
flask-cors>=4.0.0
```

### 3.4 Dependencias Frontend (CDN)

| Librería | CDN | Propósito |
|----------|-----|-----------|
| Chart.js 4.4+ | `cdn.jsdelivr.net` | Gráficos de tendencia |
| Font Awesome 6.5+ | `cdnjs.cloudflare.com` | Iconografía |

---

## 4. Guía de Usuario

### 4.1 Cómo Iniciar la Aplicación

#### Desde la terminal

```bash
# 1. Activar entorno virtual
cd hospital-lorawan-dashboard
source venv/bin/activate    # Linux/macOS
# o
venv\Scripts\Activate       # Windows

# 2. Ejecutar la aplicación
python app.py

# 3. Abrir en el navegador
# http://localhost:5000
```

#### Mensaje de inicio exitoso

```
2026-06-10 14:30:00 [INFO] ============================================================
2026-06-10 14:30:00 [INFO] Iniciando Dashboard de Monitoreo Hospitalario LoRaWAN
2026-06-10 14:30:00 [INFO] ============================================================
2026-06-10 14:30:00 [INFO] Paso 1/2: Inicializando base de datos...
2026-06-10 14:30:00 [INFO] Tablas de base de datos creadas/verificadas correctamente.
2026-06-10 14:30:00 [INFO] Seed completado: 200 dispositivos insertados.
2026-06-10 14:30:00 [INFO] Base de datos inicializada correctamente.
2026-06-10 14:30:00 [INFO] Paso 2/2: Arrancando generador de datos LoRaWAN...
2026-06-10 14:30:00 [INFO] Thread generador de datos iniciado.
2026-06-10 14:30:00 [INFO] Generador de datos iniciado.
2026-06-10 14:30:00 [INFO] ============================================================
2026-06-10 14:30:00 [INFO] Sistema listo. Navega a http://localhost:5000
2026-06-10 14:30:00 [INFO] ============================================================
 * Serving Flask app 'app'
 * Debug mode: on
```

### 4.2 Navegación del Dashboard

#### Vista General

Al cargar el dashboard, verás cinco secciones principales de arriba a abajo:

1. **Barra superior**: Muestra el nombre del sistema, indicador EN VIVO, reloj de última actualización y botón de refrescar.
2. **Cards de resumen**: 5 tarjetas con estadísticas generales del sistema.
3. **Filtros**: Controles para filtrar dispositivos por tipo, nombre/ubicación o estado.
4. **Gráfico de tendencia**: Selecciona un dispositivo para ver su historial de temperatura.
5. **Área principal** (dos columnas):
   - **Izquierda**: Tabla de todos los dispositivos con su última lectura.
   - **Derecha**: Panel de alertas activas.
6. **Tabla de últimas lecturas**: Las 100 lecturas más recientes del sistema.
7. **Footer**: Información de la aplicación y reloj del sistema.

#### Cómo usar los filtros

1. **Filtro por tipo**: Selecciona un tipo de dispositivo del menú desplegable. La tabla se actualiza automáticamente para mostrar solo dispositivos de ese tipo.
2. **Búsqueda**: Escribe en el campo de búsqueda. Puedes buscar por nombre de dispositivo (ej. "Freezer -80°C #155") o por ubicación (ej. "Laboratorio"). La búsqueda es en tiempo real.
3. **Filtro por estado**: Haz clic en **Todos**, **OK** o **Alerta** para filtrar por estado.

#### Cómo usar el gráfico

1. Selecciona un dispositivo del menú desplegable en la sección "Tendencia de Temperatura".
2. El gráfico se actualiza automáticamente mostrando las últimas 60 lecturas.
3. **También puedes hacer clic en el nombre de cualquier dispositivo en la tabla** para seleccionarlo automáticamente en el gráfico.
4. Pasa el mouse sobre los puntos del gráfico para ver valores exactos.
5. El gráfico tiene dos ejes Y:
   - **Izquierdo**: Temperatura en °C (línea azul).
   - **Derecho**: Humedad en %HR (línea verde, solo si aplica).

### 4.3 Interpretación de Alertas

#### Tipos de alerta

| Severidad | Color | Descripción | Ejemplo |
|-----------|-------|-------------|---------|
| **Advertencia** | 🟠 Naranja | Desviación menor a 2 °C del límite | Temperatura: 8.5 °C (máx: 8.0 °C) |
| **Crítica** | 🔴 Rojo | Desviación mayor a 2 °C del límite | Temperatura: 12.3 °C (máx: 8.0 °C) |

#### Indicadores visuales

| Elemento | Estado OK | Estado Alerta |
|----------|-----------|---------------|
| **Badge en tabla** | ✅ Verde fijo | 🔴 Rojo pulsante |
| **Fila en tabla** | Fondo blanco | Fondo rojizo translúcido |
| **Temperatura** | Texto verde | Texto naranja o rojo |
| **Panel de alertas** | Mensaje "No hay alertas activas" | Tarjetas con mensaje y severidad |
| **Card de resumen** | "Alertas Activas: 0" | "Alertas Activas: N" |

#### ¿Qué hacer ante una alerta?

1. **Identifica** qué dispositivo está en alerta (revisa la tabla o el panel de alertas).
2. **Investiga** la tendencia seleccionando el dispositivo en el gráfico.
3. **Determina** si es una variación momentánea o una tendencia al alza/baja.
4. **Actúa**: Si es crítica, verifica físicamente el equipo. Si es una falsa alarma, ajusta los rangos en `config.py`.

### 4.4 Exportación de Datos

Actualmente el dashboard no incluye un botón de exportación nativo. Sin embargo, puedes exportar datos de las siguientes formas:

#### Opción 1: Desde el navegador (tabla visible)

```javascript
// Copia y pega en la consola del navegador (F12)
// para exportar la tabla de dispositivos como CSV
function exportTableToCSV() {
    const rows = document.querySelectorAll('#devicesTable tr');
    let csv = [];
    for (let row of rows) {
        let cols = row.querySelectorAll('td, th');
        let vals = [];
        for (let col of cols) {
            vals.push('"' + col.innerText.replace(/"/g, '""') + '"');
        }
        csv.push(vals.join(','));
    }
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dispositivos.csv';
    a.click();
}
exportTableToCSV();
```

#### Opción 2: Consultando la API directamente

```bash
# Exportar todos los dispositivos
curl http://localhost:5000/api/devices > dispositivos.json

# Exportar últimas 1000 lecturas
curl "http://localhost:5000/api/readings?limit=1000" > lecturas.json

# Exportar alertas activas
curl http://localhost:5000/api/alerts > alertas.json

# Estadísticas generales
curl http://localhost:5000/api/stats > stats.json
```

#### Opción 3: Desde la base de datos SQLite

```bash
# Exportar a CSV usando sqlite3
sqlite3 hospital_lorawan.db -header -csv \
  "SELECT d.name, d.device_type, d.location, r.temperature, r.humidity, r.timestamp
   FROM readings r JOIN devices d ON r.device_id = d.id
   ORDER BY r.timestamp DESC LIMIT 1000;" > export_lecturas.csv
```

### 4.5 Mantenimiento

#### Reinicio de la aplicación

```bash
# Detener con Ctrl+C y volver a ejecutar
python app.py
```

#### Limpieza de la base de datos

Si la BD crece demasiado, puedes limpiar lecturas antiguas:

```bash
# Conectarse a la BD
sqlite3 hospital_lorawan.db

# Eliminar lecturas con más de 30 días
DELETE FROM readings WHERE timestamp < datetime('now', '-30 days');

# Eliminar alertas resueltas con más de 30 días
DELETE FROM alerts WHERE resolved = 1 AND created_at < datetime('now', '-30 days');

# Vaciar espacio no utilizado (VACUUM)
VACUUM;

# Salir
.exit
```

#### Reset completo (borrar todo y empezar de nuevo)

```bash
# Detener la aplicación (Ctrl+C)
# Eliminar la base de datos
rm hospital_lorawan.db

# Reiniciar la aplicación (se creará una BD nueva)
python app.py
```

#### Verificar integridad de la BD

```bash
sqlite3 hospital_lorawan.db
PRAGMA integrity_check;
-- Debería responder: "ok"
.exit
```

---

## 5. Preguntas Frecuentes (FAQ)

### 5.1 Generales

**P: ¿Necesito hardware LoRaWAN para usar este sistema?**  
R: No. El sistema incluye un generador de datos mock que simula 200 sensores sin hardware. Para uso en producción, se recomienda conectar sensores reales vía TTN o ChirpStack.

**P: ¿Puedo usar este sistema en un hospital real?**  
R: Sí, pero con precaución. El sistema está diseñado para monitoreo, no para control crítico. Asegúrate de conectar sensores reales, configurar HTTPS, agregar autenticación, y validar los rangos con el personal médico.

**P: ¿Cuántos sensores soporta?**  
R: Por defecto 200, pero puedes aumentar la cantidad modificando los `count` en `config.py`. El límite práctico depende de los recursos del servidor (SQLite puede manejar millones de registros sin problemas).

### 5.2 Técnicas

**P: ¿Por qué no veo datos en el dashboard?**  
R: Espera hasta 30 segundos después de iniciar la aplicación para que el generador produzca la primera ronda de datos. Si sigue sin aparecer, revisa la terminal por errores.

**P: ¿El gráfico no se actualiza solo?**  
R: El gráfico se actualiza cuando seleccionas un dispositivo del menú. Los datos en la tabla y las cards se actualizan automáticamente cada 10 segundos.

**P: ¿Puedo cambiar el puerto del servidor?**  
R: Sí. Modifica `FLASK_PORT` en `config.py`:
```python
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8080  # Puerto personalizado
```

**P: ¿Cómo hago accesible el dashboard desde otros dispositivos en la red?**  
R: Por defecto Flask escucha en `0.0.0.0:5000`. Desde otro dispositivo en la misma red, accede a `http://<IP_DEL_SERVIDOR>:5000`. Para saber la IP del servidor, usa `ip addr` (Linux) o `ipconfig` (Windows).

### 5.3 Alertas

**P: ¿Por qué hay tantas alertas de freezers?**  
R: Los freezers tienen rangos ajustados. Si ves falsas alarmas, verifica la tolerancia en `config.py`. Los freezers deben tener `temp_min` y `temp_max` ligeramente diferentes (ej. -20.5 a -19.5) para permitir variaciones normales del ciclo de refrigeración.

**P: ¿Las alertas se resuelven solas?**  
R: En la versión actual, las alertas permanecen activas hasta que se genera una nueva lectura dentro de rango. El generador mock produce lecturas fuera de rango con un 10% de probabilidad, por lo que las alertas pueden persistir varias rondas.

### 5.4 Datos

**P: ¿Los datos persisten al reiniciar la aplicación?**  
R: Sí. SQLite almacena los datos en `hospital_lorawan.db`. Al reiniciar, los datos históricos se conservan.

**P: ¿Puedo borrar los datos históricos?**  
R: Sí. Detén la app, elimina el archivo `hospital_lorawan.db` y reinicia. Se creará una BD nueva.

**P: ¿Los datos generados son realistas?**  
R: El generador usa distribución gaussiana alrededor del punto medio del rango, simulando el comportamiento real de sensores de temperatura. Los freezers tienen variación mínima (±0.5 °C) y los sensores ambientales varían lentamente.

---

## 6. Solución de Problemas (Troubleshooting)

### 6.1 La aplicación no inicia

| Síntoma | Causa posible | Solución |
|---------|---------------|----------|
| `ModuleNotFoundError: No module named 'flask'` | No se instalaron dependencias | Ejecuta `pip install -r requirements.txt` |
| `Address already in use` | El puerto 5000 está ocupado | Cambia `FLASK_PORT` en `config.py` o mata el proceso que usa el puerto |
| `PermissionError: [Errno 13]` | Sin permiso de escritura en el directorio | Asegura que el usuario tenga permisos de escritura para crear `hospital_lorawan.db` |
| Error de sintaxis en Python | Versión incorrecta de Python | Verifica con `python --version` (debe ser 3.10+) |

### 6.2 El dashboard no carga

| Síntoma | Causa posible | Solución |
|---------|---------------|----------|
| Página en blanco | Error en la consola del navegador | Abre F12 → Consola y verifica errores de JavaScript |
| "Failed to load resource" | Sin conexión a Internet (CDN) | Los CDNs de Chart.js y Font Awesome requieren Internet. Descarga las librerías localmente como alternativa |
| Los estilos no se ven | CSS no cargó | Verifica la ruta de `dashboard.css` en el HTML |
| No se ven datos en la tabla | El generador no ha producido datos | Espera 30 segundos o fuerza generación vía POST `/api/generate` |

### 6.3 Problemas con el generador de datos

| Síntoma | Causa posible | Solución |
|---------|---------------|----------|
| No se generan lecturas | Error en el thread del generador | Revisa la terminal en busca de errores. Verifica que `data_generator.py` no tenga excepciones |
| Solo algunos dispositivos tienen datos | Error en la consulta SQL | Revisa que todos los dispositivos tengan `active = 1` en la BD |
| Las lecturas no varían | El generador usa valores constantes | Verifica que `_gaussian_value` se esté ejecutando correctamente. Revisa `OUT_OF_RANGE_PROBABILITY` en `config.py` |

### 6.4 Problemas de rendimiento

| Síntoma | Causa posible | Solución |
|---------|---------------|----------|
| El dashboard carga lento | Muchos datos en BD | Limpia datos antiguos (ver sección 4.5) |
| El gráfico se traba | Muchos puntos de datos | Reduce `LATEST_READINGS_COUNT` en `config.py` |
| Alta carga de CPU | Polling muy frecuente | Aumenta `POLLING_INTERVAL` en `config.py` |

### 6.5 Problemas de visualización

| Síntoma | Causa posible | Solución |
|---------|---------------|----------|
| El gráfico no muestra humedad | El dispositivo no mide humedad | Solo los sensores `ambiental` miden humedad. Selecciona uno de ellos |
| Las alertas no desaparecen | No se han resuelto | Las alertas se resuelven cuando llega una lectura dentro de rango. Si el generador sigue produciendo valores fuera de rango para ese dispositivo, la alerta persistirá |
| Los botones de filtro no funcionan | Error en JavaScript | Revisa la consola del navegador (F12) |

---

## 7. Referencias Rápidas

### 7.1 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Página principal del dashboard |
| GET | `/health` | Verificación de salud del servicio |
| GET | `/api/devices` | Lista de dispositivos |
| GET | `/api/devices/<id>` | Detalle de un dispositivo |
| GET | `/api/readings` | Últimas lecturas |
| GET | `/api/readings/current` | Última lectura de cada dispositivo |
| GET | `/api/readings/latest/<id>` | Últimas N lecturas de un dispositivo |
| GET | `/api/alerts` | Alertas activas |
| GET | `/api/stats` | Estadísticas generales |
| POST | `/api/generate` | Forzar generación de datos |

### 7.2 Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `config.py` | Configuración principal (rangos, intervalos, puertos) |
| `requirements.txt` | Dependencias Python |
| `hospital_lorawan.db` | Base de datos SQLite |

---

<p align="center">
  <sub>Documentación de usuario — Hospital LoRaWAN Monitor v1.0.0</sub><br>
  <sub>© 2026 Wander Cáceres H. — MIT License</sub>
</p>
