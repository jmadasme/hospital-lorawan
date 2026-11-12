"""
database.py - Inicialización y manejo de la base de datos SQLite

Crea las tablas de devices, readings y alerts.
Proporciona funciones helper para operaciones CRUD.
Siembra 180 dispositivos al iniciar la aplicación.
"""

import sqlite3
import os
import logging
from typing import Optional, Union

from config import DB_PATH, DEVICE_TYPES
from models import Device, Reading, Alert

logger = logging.getLogger(__name__)

# =============================================================================
# Conexión a base de datos
# =============================================================================

def get_connection() -> sqlite3.Connection:
    """Obtiene una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# Creación de tablas
# =============================================================================

def create_tables() -> None:
    """Crea las tablas devices, readings y alerts si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type TEXT NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            temp_min REAL NOT NULL,
            temp_max REAL NOT NULL,
            humidity_min REAL,
            humidity_max REAL,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            reading_id INTEGER,
            parameter TEXT NOT NULL,
            value REAL NOT NULL,
            min_limit REAL,
            max_limit REAL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'warning',
            resolved INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );

        CREATE INDEX IF NOT EXISTS idx_readings_device_id ON readings(device_id);
        CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
        CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON alerts(device_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved);
        CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
    """)

    conn.commit()
    conn.close()
    logger.info("Tablas de base de datos creadas/verificadas correctamente.")


# =============================================================================
# Seed de dispositivos (180 dispositivos)
# =============================================================================

def seed_devices() -> None:
    """
    Siembra los 180 dispositivos en la base de datos si la tabla está vacía.
    Genera nombres descriptivos con numeración y ubicaciones por tipo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si ya hay dispositivos
    cursor.execute("SELECT COUNT(*) FROM devices")
    count = cursor.fetchone()[0]
    if count > 0:
        logger.info(f"Ya existen {count} dispositivos en la BD. Omitiendo seed.")
        conn.close()
        return

    locations_by_type = {
        "vitrina_refrigerada": [
            "Pasillo A", "Pasillo B", "Farmacia Central", "Quirófano 1",
            "Quirófano 2", "Quirófano 3", "Urgencias", "Pediatría",
            "Maternidad", "UCI Neonatal", "UCI Adultos", "Laboratorio",
            "Banco de Sangre", "Consultorio 1", "Consultorio 2",
        ],
        "frigobar": [
            "Enfermería 1", "Enfermería 2", "Enfermería 3", "Piso 1",
            "Piso 2", "Piso 3", "Piso 4", "Piso 5", "Cafetería",
            "Sala de Estar Médicos", "Oficina Administrativa",
        ],
        "refri_combinado_frio": [
            "Cocina", "Almacén Alimentos", "Comedor Personal",
            "Área de Preparación", "Despensa",
        ],
        "refri_combinado_cong": [
            "Cocina", "Almacén Alimentos", "Comedor Personal",
            "Área de Preparación", "Despensa",
        ],
        "freezer_20": [
            "Almacén Frío 1", "Almacén Frío 2", "Laboratorio",
            "Banco de Sangre", "Farmacia",
        ],
        "vitrina_2p": [
            "Cafetería Principal", "Cafetería Staff", "Comedor",
            "Sala de Espera VIP",
        ],
        "freezer_80": [
            "Laboratorio Central", "Biobanco", "Investigación",
            "Patología",
        ],
        "freezer_horizontal": [
            "Almacén Frío 1", "Almacén Frío 2", "Cocina",
            "Despensa",
        ],
        "camara_mortuoria": [
            "Morgue", "Tanatorio",
        ],
        "ambiental": [
            "Sala de Espera", "Pasillo Principal", "Recepción",
            "Consultorio 1", "Consultorio 2", "Consultorio 3",
            "Quirófano 1", "Quirófano 2", "UCI Adultos", "UCI Neonatal",
            "Pediatría", "Maternidad", "Farmacia", "Laboratorio",
            "Radiología",
        ],
        "termostato_sonda": [
            "Caldera 1", "Caldera 2", "Sala de Máquinas",
            "Cuarto Eléctrico", "Cuarto de Servidores",
            "Almacén General", "Archivo", "Vestidores",
        ],
    }

    device_id_counter = 1

    for device_type, config in DEVICE_TYPES.items():
        count = config["count"]
        temp_min = config["temp_min"]
        temp_max = config["temp_max"]
        humidity_min = config.get("humidity_min")
        humidity_max = config.get("humidity_max")
        locations = locations_by_type.get(device_type, ["Sin ubicación"])
        display_name = config.get("display_name", device_type)

        for i in range(1, count + 1):
            # Rotar ubicaciones según el tipo
            location = locations[(i - 1) % len(locations)]

            # Generar nombre: Tipo + número correlativo
            name = f"{display_name} #{device_id_counter:03d}"

            cursor.execute(
                """
                INSERT INTO devices
                    (device_type, name, location, temp_min, temp_max,
                     humidity_min, humidity_max, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (device_type, name, location, temp_min, temp_max,
                 humidity_min, humidity_max),
            )
            device_id_counter += 1

    conn.commit()
    total = device_id_counter - 1
    conn.close()
    logger.info(f"Seed completado: {total} dispositivos insertados.")


# =============================================================================
# Conversión de dict a modelos (dataclasses)
# =============================================================================

def _dict_to_device(data: dict) -> Device:
    """Convierte un dict a Device (filtra solo campos válidos de la dataclass)."""
    valid_fields = Device.__dataclass_fields__.keys()
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return Device(**filtered)


def _dict_to_reading(data: dict) -> Reading:
    """Convierte un dict a Reading (filtra solo campos válidos de la dataclass)."""
    valid_fields = Reading.__dataclass_fields__.keys()
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return Reading(**filtered)


def _dict_to_alert(data: dict) -> Alert:
    """Convierte un dict a Alert (filtra solo campos válidos de la dataclass)."""
    valid_fields = Alert.__dataclass_fields__.keys()
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return Alert(**filtered)


# =============================================================================
# Helpers de consulta (devuelven dicts, compatibles con código existente)
# =============================================================================

def query_all(query: str, params: tuple = ()) -> list:
    """Ejecuta una consulta SELECT y retorna todos los resultados como lista de dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result


def query_one(query: str, params: tuple = ()) -> Optional[dict]:
    """Ejecuta una consulta SELECT y retorna el primer resultado como dict o None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# =============================================================================
# Helpers de consulta con modelos (retornan dataclasses)
# =============================================================================

def query_device(device_id: int) -> Optional[Device]:
    """
    Consulta un dispositivo por ID y retorna un objeto Device.
    Args:
        device_id: ID del dispositivo
    Returns:
        Device o None si no existe
    """
    data = query_one("SELECT * FROM devices WHERE id = ?", (device_id,))
    return _dict_to_device(data) if data else None


def query_all_devices(device_type: Optional[str] = None,
                      search: Optional[str] = None) -> list[Device]:
    """
    Consulta dispositivos activos y retorna lista de objetos Device.
    Args:
        device_type: Filtrar por tipo (opcional)
        search: Término de búsqueda (opcional)
    Returns:
        Lista de objetos Device
    """
    query = "SELECT * FROM devices WHERE active = 1"
    params = []

    if device_type:
        query += " AND device_type = ?"
        params.append(device_type)

    if search:
        query += " AND (name LIKE ? OR location LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    query += " ORDER BY device_type, id"

    rows = query_all(query, tuple(params))
    return [_dict_to_device(row) for row in rows]


def query_latest_reading(device_id: int) -> Optional[Reading]:
    """
    Consulta la última lectura de un dispositivo y retorna un objeto Reading.
    Args:
        device_id: ID del dispositivo
    Returns:
        Reading o None si no hay lecturas
    """
    data = query_one(
        "SELECT * FROM readings WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1",
        (device_id,),
    )
    return _dict_to_reading(data) if data else None


def query_latest_readings(device_id: int, limit: int = 60) -> list[Reading]:
    """
    Consulta las últimas N lecturas de un dispositivo y retorna objetos Reading.
    Args:
        device_id: ID del dispositivo
        limit: Cantidad de lecturas (default 60)
    Returns:
        Lista de objetos Reading en orden ascendente
    """
    rows = query_all(
        """SELECT * FROM readings
           WHERE device_id = ?
           ORDER BY timestamp DESC LIMIT ?""",
        (device_id, limit),
    )
    readings = [_dict_to_reading(row) for row in rows]
    readings.reverse()  # Orden cronológico ascendente
    return readings


def query_active_alerts(device_id: Optional[int] = None,
                        limit: int = 20) -> list[Alert]:
    """
    Consulta alertas activas y retorna objetos Alert.
    Args:
        device_id: Filtrar por dispositivo (opcional)
        limit: Cantidad de alertas (default 20)
    Returns:
        Lista de objetos Alert
    """
    query = """
        SELECT a.* FROM alerts a
        WHERE a.resolved = 0
    """
    params = []

    if device_id:
        query += " AND a.device_id = ?"
        params.append(device_id)

    query += " ORDER BY a.created_at DESC LIMIT ?"
    params.append(limit)

    rows = query_all(query, tuple(params))
    return [_dict_to_alert(row) for row in rows]


def execute(query: str, params: tuple = ()) -> int:
    """
    Ejecuta una sentencia INSERT/UPDATE/DELETE.
    Retorna el lastrowid.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def initialize_database() -> None:
    """Inicializa la BD completa: crea tablas y siembra dispositivos."""
    create_tables()
    seed_devices()
    logger.info("Base de datos inicializada correctamente.")
