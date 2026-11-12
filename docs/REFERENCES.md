# Referencias y buenas prácticas

**Fuentes utilizadas y lecturas recomendadas para Hospital LoRaWAN Monitor**

Este documento reúne la documentación oficial, estándares y guías que
sostienen las decisiones del proyecto. Cada entrada indica **para qué se usó**
o **qué conviene consultar** antes de modificar esa parte. No sustituye a la
documentación de cada tecnología: la orienta.

> El código de 1.0.0 no conecta hardware real. Las referencias de LoRaWAN,
> TTN, ChirpStack y MQTT aplican al **diseño de integración** descrito en
> [`developer.md`](developer.md), no a una implementación existente.

---

## Índice

1. [Aplicación web](#1-aplicación-web)
2. [Persistencia](#2-persistencia)
3. [Python y concurrencia](#3-python-y-concurrencia)
4. [LoRaWAN y radio](#4-lorawan-y-radio)
5. [Servidores de red e integración](#5-servidores-de-red-e-integración)
6. [Frontend](#6-frontend)
7. [Seguridad](#7-seguridad)
8. [Operación y despliegue](#8-operación-y-despliegue)
9. [Dominio: cadena de frío sanitaria](#9-dominio-cadena-de-frío-sanitaria)
10. [Pruebas y calidad](#10-pruebas-y-calidad)
11. [Licencias de dependencias](#11-licencias-de-dependencias)
12. [Cómo mantener esta lista](#12-cómo-mantener-esta-lista)

---

## 1. Aplicación web

| Recurso | Enlace | Uso en el proyecto |
|---|---|---|
| Flask — documentación oficial | <https://flask.palletsprojects.com/> | Creación de la app, blueprints, `render_template`, `jsonify`, configuración |
| Flask — Quickstart | <https://flask.palletsprojects.com/en/stable/quickstart/> | Rutas, métodos HTTP, manejo de errores |
| Flask — Blueprints | <https://flask.palletsprojects.com/en/stable/blueprints/> | `api_bp` en `routes.py` |
| Flask — Configuración | <https://flask.palletsprojects.com/en/stable/config/> | `app.config.from_pyfile("config.py")` |
| Flask — Testing | <https://flask.palletsprojects.com/en/stable/testing/> | Propuesta de tests con `test_client` |
| Jinja2 | <https://jinja.palletsprojects.com/> | Plantilla `dashboard.html` (sin variables) |
| Werkzeug — debugger | <https://werkzeug.palletsprojects.com/en/stable/debug/> | Por qué `debug=True` no debe exponerse |
| Flask-CORS | <https://flask-cors.readthedocs.io/> | `CORS(app)` global y cómo restringirlo |

### Notas de aplicación

- El proyecto usa el **application factory solo parcialmente**: crea `app` a
  nivel de módulo, no dentro de una función. Eso simplifica `app:app` para
  Gunicorn, pero complica los tests con configuración aislada.
- `CORS(app)` sin argumentos habilita todos los orígenes. La documentación de
  Flask-CORS explica `resources` y `origins` para limitarlo.
- No se usan sesiones, formularios WTForms ni migraciones de Flask.

---

## 2. Persistencia

| Recurso | Enlace | Uso |
|---|---|---|
| SQLite — sitio oficial | <https://www.sqlite.org/> | Motor embebido |
| SQLite — WAL | <https://www.sqlite.org/wal.html> | `PRAGMA journal_mode=WAL` |
| SQLite — foreign keys | <https://www.sqlite.org/foreignkeys.html> | `PRAGMA foreign_keys=ON` por conexión |
| SQLite — backup API | <https://www.sqlite.org/backup.html> | Respaldo consistente con `.backup` |
| SQLite — VACUUM | <https://www.sqlite.org/lang_vacuum.html> | Recuperar espacio tras purgas |
| SQLite — PRAGMA | <https://www.sqlite.org/pragma.html> | `integrity_check`, `user_version`, `wal_checkpoint` |
| SQLite — índices | <https://www.sqlite.org/optoverview.html> | Diseño de los cinco índices |
| SQLite — tipos | <https://www.sqlite.org/datatype3.html> | Flexibilidad de tipos y ausencia de `CHECK` |
| Python — `sqlite3` | <https://docs.python.org/3/library/sqlite3.html> | `Row`, parámetros, transacciones |

### Notas de aplicación

- WAL permite un escritor y varios lectores, pero **no** elimina el bloqueo
  entre dos escritores. Dos instancias de la app compiten por el archivo.
- `PRAGMA foreign_keys` no es persistente: debe ejecutarse en cada conexión,
  tal como hace `get_connection()`.
- `CURRENT_TIMESTAMP` en SQLite devuelve UTC. El frontend agrega `Z` para que
  `Date` lo interprete correctamente; otros clientes deben hacer lo mismo.
- Para retención, `DELETE` no reduce el archivo hasta `VACUUM`. Programarlo
  fuera de horario y con espacio libre suficiente.

### Lecturas recomendadas

- *SQLite is not a toy database* — notas prácticas sobre concurrencia y WAL.
- Documentación de `EXPLAIN QUERY PLAN` para validar que los índices se usan.

---

## 3. Python y concurrencia

| Recurso | Enlace | Uso |
|---|---|---|
| Python — dataclasses | <https://docs.python.org/3/library/dataclasses.html> | `Device`, `Reading`, `Alert` |
| Python — threading | <https://docs.python.org/3/library/threading.html> | Hilo daemon del generador |
| Python — random | <https://docs.python.org/3/library/random.html> | `gauss`, `uniform`, `seed` |
| Python — logging | <https://docs.python.org/3/library/logging.html> | `basicConfig(level=INFO)` |
| Python — venv | <https://docs.python.org/3/library/venv.html> | Entorno virtual |
| PEP 8 | <https://peps.python.org/pep-0008/> | Convenciones de estilo |
| PEP 257 | <https://peps.python.org/pep-0257/> | Docstrings |
| typing | <https://docs.python.org/3/library/typing.html> | Firmas con `Optional`, `list[dict]` |

### Notas de aplicación

- El hilo es `daemon=True`: no impide el cierre del proceso, pero tampoco
  garantiza terminar una ronda en curso. `stop_generator()` no hace `join`.
- `random` no es criptográficamente seguro; es adecuado para simulación, no
  para tokens.
- Los type hints no se validan en ejecución. Un `mypy` estricto detectaría
  inconsistencias entre dataclasses y diccionarios.

---

## 4. LoRaWAN y radio

| Recurso | Enlace | Uso |
|---|---|---|
| LoRa Alliance — especificación LoRaWAN 1.0.4 | <https://lora-alliance.org/resource_hub/lorawan-specification-v1-0-4/> | Marco del protocolo |
| LoRa Alliance — recursos | <https://lora-alliance.org/resource-hub/> | Región, clases, certificación |
| LoRa Alliance — regional parameters | <https://lora-alliance.org/resource_hub/lorawan-regional-parameters/> | Bandas, duty cycle, potencias |
| TTN — LoRaWAN | <https://www.thethingsnetwork.org/docs/lorawan/> | Explicación aplicada de clases y activación |
| TTN — frecuencia y duty cycle | <https://www.thethingsnetwork.org/docs/lorawan/frequency-plans/> | Límites por región |
| Semtech — LoRa | <https://www.semtech.com/lora> | Capa física y transceptores |
| LoRaWAN University | <https://lora-developers.semtech.com/> | Formación técnica gratuita |

### Conceptos que el proyecto asume

| Concepto | Implicación |
|---|---|
| **Clase A** | Dos ventanas RX tras cada uplink; mínimo consumo |
| **OTAA** | Activación por aire; recomendada frente a ABP |
| **Duty cycle** | ~1 % en 868 MHz; condiciona la frecuencia de reporte |
| **Dwell time** | 400 ms en 915 MHz |
| **Payload** | 3–5 bytes suficientes para temperatura, humedad y flags |
| **SF** | SF7 rápido/corto; SF12 lento/largo |
| **ADR** | El servidor de red ajusta la tasa; no implementado en el mock |

### Advertencia de diseño

LoRaWAN **no** es un enlace de tiempo real. Un panel que espera actualización
cada segundos está mal planteado para esta tecnología. El proyecto simula 30 s
para que la demo sea dinámica; un piloto real debería reportar cada 5–15 min,
con watchdog de silencio.

---

## 5. Servidores de red e integración

| Recurso | Enlace | Uso |
|---|---|---|
| The Things Network — documentación | <https://www.thethingsnetwork.org/docs/> | Referencia de Application Server |
| TTN — API v3 | <https://www.thethingsnetwork.org/docs/applications/> | Registro de aplicaciones y claves |
| TTN — MQTT | <https://www.thethingsnetwork.org/docs/applications/mqtt/> | Tópicos `v3/{app}/devices/+/up` |
| TTN — payload formatters | <https://www.thethingsnetwork.org/docs/applications/payload-formatters/> | Decoder JavaScript |
| ChirpStack — documentación | <https://www.chirpstack.io/docs/> | Alternativa autoalojada |
| ChirpStack — integraciones | <https://www.chirpstack.io/docs/chirpstack/integrations/> | MQTT, HTTP, InfluxDB |
| MQTT — especificación | <https://mqtt.org/> | Pub/sub, QoS, sesiones |
| Eclipse Paho MQTT Python | <https://paho-mqtt.readthedocs.io/> | Bridge propuesto |
| Mosquitto | <https://mosquitto.org/> | Broker para pruebas locales |

### Notas de aplicación

- El host MQTT de TTN depende de la región (`eu1`, `nam1`, `au1`). No
  hardcodear uno solo.
- QoS 1 garantiza entrega al menos una vez: **puede duplicar**. El bridge debe
  deduplicar por `(dev_eui, f_cnt)`.
- TLS en 8883. Nunca 1883 en redes compartidas.
- Los payload formatters de TTN se ejecutan en el servidor de red; validar
  igualmente en el bridge.
- ChirpStack expone eventos por MQTT e integraciones HTTP; el diseño de webhook
  aplica a ambos.

---

## 6. Frontend

| Recurso | Enlace | Uso |
|---|---|---|
| Chart.js — documentación | <https://www.chartjs.org/docs/> | Gráfico de línea con dos ejes |
| Chart.js — actualización | <https://www.chartjs.org/docs/latest/developers/updates.html> | `chart.update()` |
| Font Awesome | <https://fontawesome.com/docs> | Iconografía |
| MDN — Fetch API | <https://developer.mozilla.org/es/docs/Web/API/Fetch_API> | Polling de la API |
| MDN — `Date` | <https://developer.mozilla.org/es/docs/Web/JavaScript/Reference/Global_Objects/Date> | Parseo de timestamps UTC |
| MDN — `Intl.DateTimeFormat` | <https://developer.mozilla.org/es/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat> | Formato `es-CL` |
| web.dev — rendimiento | <https://web.dev/learn/performance/> | Coste de reescribir tablas |

### Notas de aplicación

- Chart.js 4.x cambió la configuración de ejes respecto de 3.x. El código usa
  `scales.y`/`scales.y1`, válido en 4.4.1.
- Cargar por CDN simplifica el despliegue, pero crea dependencia de Internet y
  de la disponibilidad de terceros. Para un piloto, alojar localmente.
- `innerHTML` con 200 filas cada 10 s es aceptable en demo, no en producción.
  Considerar `DocumentFragment` o renderizado por fila.

---

## 7. Seguridad

| Recurso | Enlace | Uso |
|---|---|---|
| OWASP Top 10 | <https://owasp.org/www-project-top-ten/> | Marco de riesgos |
| OWASP — Autenticación | <https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html> | Si se añade login |
| OWASP — Cabeceras | <https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html> | Endurecimiento del proxy |
| OWASP — XSS | <https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html> | Escape en el frontend |
| Flask — seguridad | <https://flask.palletsprojects.com/en/stable/web-security/> | Buenas prácticas del framework |
| MDN — CORS | <https://developer.mozilla.org/es/docs/Web/HTTP/CORS> | Configuración de orígenes |
| NIST — ciberseguridad IoT | <https://www.nist.gov/programs-projects/nist-cybersecurity-iot-program> | Contexto de dispositivos |
| CISA — IoT | <https://www.cisa.gov/topics/cyber-threats-and-advisories/internet-things-iot> | Guías de despliegue |

### Riesgos concretos de esta versión

1. **Debug expuesto**: `FLASK_DEBUG=True` habilita el depurador interactivo.
2. **CORS abierto**: cualquier origen puede leer la API desde un navegador.
3. **Sin autenticación**: inventario, histórico y generación son públicos.
4. **`/api/generate` sin control**: escritura masiva trivial.
5. **Sin TLS**: credenciales y datos viajan en claro si se publica directo.
6. **Sin rate limit**: enumeración y denegación de servicio sencillas.

Ninguno se corrige en 1.0.0 porque el objetivo es una demo reproducible. El
checklist de despliegue de `docs/datasheet.md` los enumera.

---

## 8. Operación y despliegue

| Recurso | Enlace | Uso |
|---|---|---|
| Gunicorn | <https://docs.gunicorn.org/> | Servidor WSGI |
| Gunicorn — workers | <https://docs.gunicorn.org/en/stable/design.html> | Por qué un solo worker |
| Nginx | <https://nginx.org/en/docs/> | Proxy inverso y TLS |
| systemd | <https://www.freedesktop.org/software/systemd/man/systemd.service.html> | Unidad de servicio |
| The Twelve-Factor App | <https://12factor.net/> | Configuración por entorno |
| Let's Encrypt | <https://letsencrypt.org/docs/> | Certificados TLS |
| Debian — administración | <https://www.debian.org/doc/manuals/debian-handbook/> | Base del servidor |

### Notas de aplicación

- El generador vive en el proceso: `--workers 1`. Si en el futuro se separa,
  el dashboard puede escalar horizontalmente.
- La configuración actual no usa variables de entorno. Migrar a
  `os.environ` es el primer paso de 12-factor y evita secretos en archivos.
- `ProtectSystem=strict` con `ReadWritePaths` limita la escritura al
  directorio del proyecto, donde vive la base.

---

## 9. Dominio: cadena de frío sanitaria

| Recurso | Enlace | Uso |
|---|---|---|
| OMS — dispositivo de cadena de frío (PQS) | <https://www.who.int/initiatives/performance-qualification-system> | Criterios de equipos de vacunación |
| OMS — cadena de frío | <https://www.who.int/teams/immunization-vaccines-and-biologicals/essential-programme-on-immunization/implementation/cold-chain> | Marco operativo |
| CDC — almacenamiento de vacunas | <https://www.cdc.gov/vaccines/hcp/storage-handling/> | Rangos y buenas prácticas |
| CDC — toolkit de cadena de frío | <https://www.cdc.gov/vaccines/hcp/storage-handling/toolkit.html> | Registros y excursiones |
| AABB — sangre | <https://www.aabb.org/> | Referencia de hemoderivados |
| CLSI — laboratorio | <https://clsi.org/> | Reactivos y calibradores |
| FDA — dispositivos médicos | <https://www.fda.gov/medical-devices> | Contexto regulatorio |

### Cómo se traduce al producto

- Los rangos 2–8 °C, −20 °C y −80 °C son **operativos**, no normativos.
- La normativa exige registro continuo, alarmas y evidencia de revisión. El
  proyecto cubre visualización, no cumplimiento.
- Un sistema real necesita calibración trazable, validación de software y
  gestión de excursiones con acuse. Nada de eso está implementado.
- Las cifras de este repositorio son de demostración: no citarlas como
  validadas.

---

## 10. Pruebas y calidad

| Recurso | Enlace | Uso |
|---|---|---|
| pytest | <https://docs.pytest.org/> | Framework propuesto |
| pytest — fixtures | <https://docs.pytest.org/en/stable/how-to/fixtures.html> | Base temporal por test |
| Coverage.py | <https://coverage.readthedocs.io/> | Cobertura |
| ruff | <https://docs.astral.sh/ruff/> | Linter rápido |
| mypy | <https://mypy.readthedocs.io/> | Tipado estático |
| pre-commit | <https://pre-commit.com/> | Hooks de calidad |

### Estrategia sugerida

1. **Unidad**: `_gaussian_value` respeta límites; severidad se calcula bien.
2. **Integración**: rutas con `test_client` y base temporal.
3. **Contrato**: forma de las respuestas JSON.
4. **Regresión**: una alerta no se resuelve sola (documentar el estado actual).
5. **Carga**: 200 peticiones concurrentes a `/current`.

Advertencia: importar `app` ejecuta código de módulo, pero no `initialize()`
(solo corre bajo `__main__`). Los tests deben inicializar una base temporal y
evitar el hilo generador.

---

## 11. Licencias de dependencias

| Componente | Licencia | Implicación |
|---|---|---|
| Flask | BSD-3-Clause | Uso comercial permitido, conservar aviso |
| Flask-CORS | MIT | Ídem |
| SQLite | Dominio público | Sin restricciones |
| Chart.js | MIT | Ídem |
| Font Awesome Free | CC BY 4.0 (iconos) / MIT (código) | Atribución en iconos |
| Python | PSF License | Ídem |

El proyecto se distribuye bajo **MIT** (`Copyright (c) 2026 jmadasme`). Al
redistribuir, conservar el aviso de licencia y las atribuciones del código
original de la versión 1.0.0 (Wander Cáceres H., @wanderc137).

---

## 12. Cómo mantener esta lista

- Añadir una referencia solo si se usó para una decisión concreta o si es
  necesaria para mantener una parte del código.
- Preferir documentación oficial y estándares sobre blogs.
- Anotar la fecha de consulta cuando la fuente cambie con frecuencia
  (servidores de red, CDN, precios).
- Revisar enlaces al menos una vez por versión mayor.
- No incluir enlaces a credenciales, paneles privados ni recursos que
  requieran cuenta.

### Fuentes descartadas

| Fuente | Motivo |
|---|---|
| Tutoriales de "IoT en 10 minutos" | Simplifican el duty cycle y la seguridad |
| Ejemplos con claves embebidas | Mala práctica, riesgo de copia |
| Foros sin fecha | Información obsoleta sobre TTN v2 |
| Proveedores de sensores sin datasheet | Sin trazabilidad técnica |

---

**Volver a:** [`README.md`](../README.md) · [`datasheet.md`](datasheet.md) ·
[`developer.md`](developer.md)
