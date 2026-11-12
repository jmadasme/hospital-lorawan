"""
routes.py - Rutas y endpoints de la API REST del Dashboard Hospitalario LoRaWAN

Define todos los endpoints listados en PLAN.md para servir datos
de dispositivos, lecturas, alertas y estadísticas al frontend.
"""

import logging
from flask import Blueprint, jsonify, request

from database import query_all, query_one
from config import LATEST_READINGS_COUNT, ALERTS_DISPLAY_COUNT, RECENT_READINGS_COUNT
from data_generator import generate_all_readings

logger = logging.getLogger(__name__)

# Blueprint para organizar las rutas de la API
api_bp = Blueprint("api", __name__)


# =============================================================================
# Endpoint: Listar todos los dispositivos
# =============================================================================

@api_bp.route("/api/devices", methods=["GET"])
def get_devices():
    """
    GET /api/devices
    Lista todos los dispositivos activos.
    Query params:
        - device_type (opcional): Filtrar por tipo de dispositivo
        - search (opcional): Buscar por nombre o ubicación
    """
    device_type = request.args.get("device_type")
    search = request.args.get("search")

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

    devices = query_all(query, tuple(params))
    return jsonify({"success": True, "data": devices, "count": len(devices)})


# =============================================================================
# Endpoint: Detalle de un dispositivo
# =============================================================================

@api_bp.route("/api/devices/<int:device_id>", methods=["GET"])
def get_device(device_id: int):
    """
    GET /api/devices/<id>
    Retorna el detalle de un dispositivo específico,
    incluyendo su última lectura.
    """
    device = query_one("SELECT * FROM devices WHERE id = ?", (device_id,))
    if not device:
        return jsonify({"success": False, "error": "Dispositivo no encontrado"}), 404

    # Obtener última lectura
    last_reading = query_one(
        "SELECT * FROM readings WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1",
        (device_id,),
    )
    if last_reading:
        device["last_reading"] = last_reading
    else:
        device["last_reading"] = None

    return jsonify({"success": True, "data": device})


# =============================================================================
# Endpoint: Últimas lecturas
# =============================================================================

@api_bp.route("/api/readings", methods=["GET"])
def get_readings():
    """
    GET /api/readings
    Retorna lecturas recientes.
    Query params:
        - limit (opcional): Cantidad de lecturas (default: 100)
        - device_id (opcional): Filtrar por dispositivo
    """
    limit = request.args.get("limit", RECENT_READINGS_COUNT, type=int)
    device_id = request.args.get("device_id", type=int)

    query = """
        SELECT r.*, d.name as device_name, d.device_type
        FROM readings r
        JOIN devices d ON r.device_id = d.id
    """
    params = []

    if device_id:
        query += " WHERE r.device_id = ?"
        params.append(device_id)

    query += " ORDER BY r.timestamp DESC LIMIT ?"
    params.append(limit)

    readings = query_all(query, tuple(params))
    return jsonify({"success": True, "data": readings, "count": len(readings)})


# =============================================================================
# Endpoint: Última lectura de cada dispositivo
# =============================================================================

@api_bp.route("/api/readings/current", methods=["GET"])
def get_current_readings():
    """
    GET /api/readings/current
    Retorna la última lectura de cada dispositivo activo,
    incluyendo estado de alerta.
    """
    query = """
        SELECT
            d.id as device_id,
            d.device_type,
            d.name,
            d.location,
            d.temp_min,
            d.temp_max,
            d.humidity_min,
            d.humidity_max,
            r.id as reading_id,
            r.temperature,
            r.humidity,
            r.timestamp,
            a.id as alert_id,
            a.severity as alert_severity,
            a.message as alert_message
        FROM devices d
        LEFT JOIN readings r ON r.id = (
            SELECT id FROM readings
            WHERE device_id = d.id
            ORDER BY timestamp DESC LIMIT 1
        )
        LEFT JOIN alerts a ON a.id = (
            SELECT id FROM alerts
            WHERE device_id = d.id AND resolved = 0
            ORDER BY created_at DESC LIMIT 1
        )
        WHERE d.active = 1
        ORDER BY d.device_type, d.id
    """

    readings = query_all(query)

    # Procesar para determinar estado
    result = []
    for row in readings:
        status = "ok"
        if row.get("alert_id"):
            status = "alert"

        # Determinar si lectura actual está fuera de rango
        if row.get("temperature") is not None:
            temp = row["temperature"]
            if temp < row["temp_min"] or temp > row["temp_max"]:
                status = "alert"
            elif (row.get("humidity") is not None
                  and row.get("humidity_min") is not None
                  and row.get("humidity_max") is not None):
                hum = row["humidity"]
                if hum < row["humidity_min"] or hum > row["humidity_max"]:
                    status = "alert"

        row["status"] = status
        result.append(row)

    return jsonify({"success": True, "data": result, "count": len(result)})


# =============================================================================
# Endpoint: Últimas N lecturas de un dispositivo (para gráficos)
# =============================================================================

@api_bp.route("/api/readings/latest/<int:device_id>", methods=["GET"])
def get_latest_readings(device_id: int):
    """
    GET /api/readings/latest/<device_id>
    Retorna las últimas N lecturas de un dispositivo específico.
    Útil para alimentar gráficos de tendencia (Chart.js).
    """
    readings = query_all(
        """SELECT r.*, d.name as device_name, d.device_type
           FROM readings r
           JOIN devices d ON r.device_id = d.id
           WHERE r.device_id = ?
           ORDER BY r.timestamp DESC LIMIT ?""",
        (device_id, LATEST_READINGS_COUNT),
    )

    # Invertir para orden cronológico ascendente (mejor para gráficos)
    readings.reverse()

    return jsonify({
        "success": True,
        "data": readings,
        "count": len(readings),
    })


# =============================================================================
# Endpoint: Alertas activas
# =============================================================================

@api_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    """
    GET /api/alerts
    Retorna las últimas alertas activas (no resueltas).
    Query params:
        - limit (opcional): Cantidad de alertas (default: 20)
        - device_id (opcional): Filtrar por dispositivo
    """
    limit = request.args.get("limit", ALERTS_DISPLAY_COUNT, type=int)
    device_id = request.args.get("device_id", type=int)

    query = """
        SELECT a.*, d.name as device_name, d.device_type, d.location
        FROM alerts a
        JOIN devices d ON a.device_id = d.id
        WHERE a.resolved = 0
    """
    params = []

    if device_id:
        query += " AND a.device_id = ?"
        params.append(device_id)

    query += " ORDER BY a.created_at DESC LIMIT ?"
    params.append(limit)

    alerts = query_all(query, tuple(params))
    return jsonify({"success": True, "data": alerts, "count": len(alerts)})


# =============================================================================
# Endpoint: Estadísticas generales
# =============================================================================

@api_bp.route("/api/stats", methods=["GET"])
def get_stats():
    """
    GET /api/stats
    Retorna estadísticas generales del sistema:
    - Total de dispositivos
    - Dispositivos con alerta activa
    - Total de lecturas
    - Total de alertas
    - Última actualización
    - Lecturas en las últimas 24h
    - Distribución por tipo de dispositivo
    """
    total_devices = query_one(
        "SELECT COUNT(*) as count FROM devices WHERE active = 1"
    )

    devices_with_alerts = query_one(
        """SELECT COUNT(DISTINCT a.device_id) as count
           FROM alerts a
           JOIN devices d ON a.device_id = d.id
           WHERE a.resolved = 0 AND d.active = 1"""
    )

    total_readings = query_one("SELECT COUNT(*) as count FROM readings")

    total_alerts = query_one(
        "SELECT COUNT(*) as count FROM alerts WHERE resolved = 0"
    )

    last_update = query_one(
        "SELECT MAX(timestamp) as last_update FROM readings"
    )

    readings_24h = query_one(
        """SELECT COUNT(*) as count FROM readings
           WHERE timestamp >= datetime('now', '-24 hours')"""
    )

    # Distribución por tipo de dispositivo
    type_distribution = query_all(
        """SELECT device_type, COUNT(*) as count
           FROM devices WHERE active = 1
           GROUP BY device_type ORDER BY device_type"""
    )

    # Últimas 5 alertas
    recent_alerts = query_all(
        """SELECT a.*, d.name as device_name
           FROM alerts a
           JOIN devices d ON a.device_id = d.id
           WHERE a.resolved = 0
           ORDER BY a.created_at DESC LIMIT 5"""
    )

    return jsonify({
        "success": True,
        "data": {
            "total_devices": total_devices["count"] if total_devices else 0,
            "devices_with_alerts": (
                devices_with_alerts["count"] if devices_with_alerts else 0
            ),
            "total_readings": total_readings["count"] if total_readings else 0,
            "total_alerts": total_alerts["count"] if total_alerts else 0,
            "last_update": (
                last_update["last_update"] if last_update else None
            ),
            "readings_24h": readings_24h["count"] if readings_24h else 0,
            "type_distribution": type_distribution,
            "recent_alerts": recent_alerts,
        },
    })


# =============================================================================
# Endpoint: Forzar generación de datos mock
# =============================================================================

@api_bp.route("/api/generate", methods=["POST"])
def force_generate():
    """
    POST /api/generate
    Fuerza la generación inmediata de una ronda de lecturas mock.
    Útil para pruebas y debugging.
    """
    # Validación básica de Content-Type
    content_type = request.headers.get("Content-Type", "")
    if not ("application/json" in content_type
            or "application/x-www-form-urlencoded" in content_type):
        return jsonify({
            "success": False,
            "error": "Content-Type no soportado. "
                     "Use application/json o application/x-www-form-urlencoded.",
        }), 415
    try:
        count = generate_all_readings()
        return jsonify({
            "success": True,
            "message": f"Generadas {count} lecturas correctamente.",
            "count": count,
        })
    except Exception as e:
        logger.error(f"Error al forzar generación: {e}")
        return jsonify({
            "success": False,
            "error": f"Error al generar lecturas: {str(e)}",
        }), 500
