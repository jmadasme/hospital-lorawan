"""
config.py - Configuración del Dashboard de Monitoreo Hospitalario LoRaWAN

Define los tipos de dispositivos, rangos de temperatura/humedad
e intervalos de generación de datos y polling.
"""

import os

# =============================================================================
# Configuración de Base de Datos
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hospital_lorawan.db")

# =============================================================================
# Intervalos de tiempo (en segundos)
# =============================================================================
GENERATION_INTERVAL = 30       # Cada 30s se generan lecturas mock
POLLING_INTERVAL = 10          # Frontend polling cada 10s
LATEST_READINGS_COUNT = 60     # Últimas N lecturas para gráficos
ALERTS_DISPLAY_COUNT = 20      # Últimas N alertas a mostrar
RECENT_READINGS_COUNT = 100    # Últimas N lecturas en tabla de histórico

# =============================================================================
# Probabilidad de generar un valor fuera de rango (0.0 - 1.0)
# =============================================================================
OUT_OF_RANGE_PROBABILITY = 0.10

# =============================================================================
# Definición de tipos de dispositivos
# =============================================================================
# Cada entrada contiene:
#   count: cantidad de dispositivos de este tipo
#   temp_min / temp_max: límites de temperatura
#   humidity_min / humidity_max: límites de humedad (opcional, solo si aplica)
#   display_name: nombre para mostrar en el dashboard
DEVICE_TYPES = {
    "vitrina_refrigerada": {
        "count": 46,
        "temp_min": 2.0,
        "temp_max": 8.0,
        "display_name": "Vitrina Refrigerada",
    },
    "frigobar": {
        "count": 33,
        "temp_min": 2.0,
        "temp_max": 8.0,
        "display_name": "Frigobar",
    },
    "refri_combinado_frio": {
        "count": 20,
        "temp_min": 2.0,
        "temp_max": 8.0,
        "display_name": "Refrigerador Combinado (Frío)",
    },
    "refri_combinado_cong": {
        "count": 20,
        "temp_min": -20.5,
        "temp_max": -19.5,
        "display_name": "Refrigerador Combinado (Congelador)",
    },
    "freezer_20": {
        "count": 13,
        "temp_min": -20.5,
        "temp_max": -19.5,
        "display_name": "Freezer -20°C",
    },
    "vitrina_2p": {
        "count": 8,
        "temp_min": 2.0,
        "temp_max": 8.0,
        "display_name": "Vitrina 2 Puertas",
    },
    "freezer_80": {
        "count": 4,
        "temp_min": -80.5,
        "temp_max": -79.5,
        "display_name": "Freezer -80°C",
    },
    "freezer_horizontal": {
        "count": 4,
        "temp_min": -20.5,
        "temp_max": -19.5,
        "display_name": "Freezer Horizontal",
    },
    "camara_mortuoria": {
        "count": 2,
        "temp_min": 2.0,
        "temp_max": 8.0,
        "display_name": "Cámara Mortuoria",
    },
    "ambiental": {
        "count": 30,
        "temp_min": 20.0,
        "temp_max": 24.0,
        "humidity_min": 30.0,
        "humidity_max": 60.0,
        "display_name": "Monitoreo Ambiental",
    },
    "termostato_sonda": {
        "count": 20,
        "temp_min": -50.0,
        "temp_max": 100.0,
        "display_name": "Termostato con Sonda",
    },
}

# =============================================================================
# Configuración del servidor Flask
# =============================================================================
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True
