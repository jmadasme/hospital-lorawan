"""
data_generator.py - Generador de datos mock LoRaWAN

Simula la llegada de datos desde dispositivos LoRaWAN cada 30 segundos.
Genera lecturas realistas con variación gaussiana alrededor del punto medio
del rango. Un 10% de las lecturas son valores fuera de rango para probar alertas.

Ejecuta en un thread daemon que se inicia con la aplicación.
"""

import threading
import time
import random
import logging
from datetime import datetime
from typing import Optional

from config import (
    GENERATION_INTERVAL,
    OUT_OF_RANGE_PROBABILITY,
    DEVICE_TYPES,
)
from database import get_connection, query_all, execute

logger = logging.getLogger(__name__)


# =============================================================================
# Generación de valores realistas
# =============================================================================

def _gaussian_value(center: float, min_val: float, max_val: float,
                    std_dev_factor: float = 0.15) -> float:
    """
    Genera un valor con distribución gaussiana alrededor de `center`,
    limitado al rango [min_val, max_val].

    Args:
        center: Valor central (punto medio del rango)
        min_val: Límite inferior
        max_val: Límite superior
        std_dev_factor: Fracción del rango total para la desviación estándar

    Returns:
        float: Valor generado
    """
    if min_val == max_val:
        # Para dispositivos con rango fijo (freezers), añadir pequeña
        # variación alrededor del valor fijo
        std_dev = abs(min_val) * 0.02 + 0.3
        value = random.gauss(min_val, std_dev)
    else:
        range_size = max_val - min_val
        std_dev = range_size * std_dev_factor
        value = random.gauss(center, std_dev)

    return round(max(min_val, min(max_val, value)), 2)


def _is_temperature_stable(device_type: str) -> bool:
    """
    Determina si un tipo de dispositivo tiene temperatura estable
    (freezers, cámaras de frío). Estos tienen variación mínima.
    """
    stable_types = {"freezer_80", "freezer_20", "freezer_horizontal",
                    "refri_combinado_cong"}
    return device_type in stable_types


def generate_reading_value(device_type: str, temp_min: float,
                           temp_max: float) -> float:
    """
    Genera un valor de temperatura para un dispositivo.
    Aplica un 10% de probabilidad de generar un valor fuera de rango.

    Args:
        device_type: Tipo de dispositivo
        temp_min: Límite inferior de temperatura
        temp_max: Límite superior de temperatura

    Returns:
        float: Valor de temperatura generado
    """
    center = (temp_min + temp_max) / 2.0

    # 10% de probabilidad de valor fuera de rango
    is_out_of_range = random.random() < OUT_OF_RANGE_PROBABILITY

    if is_out_of_range:
        # Generar valor fuera de rango: entre 5% y 30% fuera del límite
        range_size = max(abs(temp_max - temp_min), 1.0)
        offset = random.uniform(0.05, 0.30) * range_size
        if random.random() < 0.5:
            # Fuera por encima
            return round(temp_max + offset, 2)
        else:
            # Fuera por debajo
            return round(temp_min - offset, 2)

    if _is_temperature_stable(device_type):
        # Freezers: variación muy pequeña
        std_dev = 0.3
        value = random.gauss(center, std_dev)
        return round(max(temp_min - 0.5, min(temp_max + 0.5, value)), 2)

    return _gaussian_value(center, temp_min, temp_max)


def generate_humidity_value(humidity_min: float,
                            humidity_max: float) -> Optional[float]:
    """
    Genera un valor de humedad relativa para dispositivos ambientales.
    Aplica un 10% de probabilidad de generar un valor fuera de rango.

    Args:
        humidity_min: Límite inferior de humedad
        humidity_max: Límite superior de humedad

    Returns:
        float: Valor de humedad generado o None si no aplica
    """
    if humidity_min is None or humidity_max is None:
        return None

    center = (humidity_min + humidity_max) / 2.0

    # 10% de probabilidad de valor fuera de rango
    is_out_of_range = random.random() < OUT_OF_RANGE_PROBABILITY

    if is_out_of_range:
        range_size = max(humidity_max - humidity_min, 1.0)
        offset = random.uniform(0.05, 0.30) * range_size
        if random.random() < 0.5:
            return round(min(humidity_max + offset, 100.0), 2)
        else:
            return round(max(0.0, humidity_min - offset), 2)

    return _gaussian_value(center, humidity_min, humidity_max, std_dev_factor=0.1)


# =============================================================================
# Inserción de lecturas y evaluación de alertas
# =============================================================================

def insert_reading_and_check_alerts(device_id: int, device_type: str,
                                    temp_min: float, temp_max: float,
                                    humidity_min: Optional[float],
                                    humidity_max: Optional[float]) -> None:
    """
    Genera una lectura para un dispositivo, la inserta en BD y
    crea una alerta si está fuera de rango.

    Args:
        device_id: ID del dispositivo
        device_type: Tipo de dispositivo
        temp_min: Límite inferior de temperatura
        temp_max: Límite superior de temperatura
        humidity_min: Límite inferior de humedad
        humidity_max: Límite superior de humedad
    """
    temperature = generate_reading_value(device_type, temp_min, temp_max)
    humidity = generate_humidity_value(humidity_min, humidity_max)

    conn = get_connection()
    cursor = conn.cursor()

    # Insertar lectura
    cursor.execute(
        """INSERT INTO readings (device_id, temperature, humidity)
           VALUES (?, ?, ?)""",
        (device_id, temperature, humidity),
    )
    reading_id = cursor.lastrowid

    # Evaluar alertas de temperatura
    if temperature < temp_min or temperature > temp_max:
        if temperature < temp_min:
            message = (
                f"Temperatura baja: {temperature}°C "
                f"(mínimo: {temp_min}°C)"
            )
        else:
            message = (
                f"Temperatura alta: {temperature}°C "
                f"(máximo: {temp_max}°C)"
            )

        severity = "critical" if abs(temperature - temp_min) > 2.0 or \
            abs(temperature - temp_max) > 2.0 else "warning"

        cursor.execute(
            """INSERT INTO alerts
               (device_id, reading_id, parameter, value,
                min_limit, max_limit, message, severity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (device_id, reading_id, "temperature", temperature,
             temp_min, temp_max, message, severity),
        )
        logger.warning(f"ALERTA [{device_id}] {message}")

    # Evaluar alertas de humedad
    if humidity is not None and humidity_min is not None and humidity_max is not None:
        if humidity < humidity_min or humidity > humidity_max:
            if humidity < humidity_min:
                message = (
                    f"Humedad baja: {humidity}% HR "
                    f"(mínimo: {humidity_min}% HR)"
                )
            else:
                message = (
                    f"Humedad alta: {humidity}% HR "
                    f"(máximo: {humidity_max}% HR)"
                )

            severity = "warning"

            cursor.execute(
                """INSERT INTO alerts
                   (device_id, reading_id, parameter, value,
                    min_limit, max_limit, message, severity)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (device_id, reading_id, "humidity", humidity,
                 humidity_min, humidity_max, message, severity),
            )
            logger.warning(f"ALERTA [{device_id}] {message}")

    conn.commit()
    conn.close()


# =============================================================================
# Generación masiva de lecturas para todos los dispositivos
# =============================================================================

def generate_all_readings() -> int:
    """
    Genera una lectura para cada dispositivo activo en la base de datos.

    Returns:
        int: Número de lecturas generadas
    """
    devices = query_all(
        "SELECT id, device_type, temp_min, temp_max, "
        "humidity_min, humidity_max FROM devices WHERE active = 1"
    )

    count = 0
    for device in devices:
        insert_reading_and_check_alerts(
            device_id=device["id"],
            device_type=device["device_type"],
            temp_min=device["temp_min"],
            temp_max=device["temp_max"],
            humidity_min=device.get("humidity_min"),
            humidity_max=device.get("humidity_max"),
        )
        count += 1

    logger.info(f"Generadas {count} lecturas para {len(devices)} dispositivos.")
    return count


# =============================================================================
# Thread de generación periódica
# =============================================================================

_generator_thread: Optional[threading.Thread] = None
_running = False


def _generator_loop() -> None:
    """Loop principal del generador: ejecuta generación cada N segundos."""
    global _running
    logger.info(
        f"Generador de datos iniciado. Intervalo: {GENERATION_INTERVAL}s"
    )

    # Generar lecturas inmediatamente al arrancar
    try:
        generate_all_readings()
    except Exception as e:
        logger.error(f"Error en generación inicial: {e}")

    while _running:
        time.sleep(GENERATION_INTERVAL)
        try:
            generate_all_readings()
        except Exception as e:
            logger.error(f"Error en generación de lecturas: {e}")


def start_generator() -> None:
    """Inicia el thread daemon del generador de datos."""
    global _generator_thread, _running
    if _generator_thread is not None and _generator_thread.is_alive():
        logger.warning("El generador ya está en ejecución.")
        return

    _running = True
    _generator_thread = threading.Thread(target=_generator_loop, daemon=True)
    _generator_thread.start()
    logger.info("Thread generador de datos iniciado.")


def stop_generator() -> None:
    """Detiene el generador de datos."""
    global _running
    _running = False
    logger.info("Generador de datos detenido.")
