"""
app.py - Punto de entrada de la aplicación Flask

Inicializa la base de datos, arranca el generador de datos mock
y registra las rutas de la API. Sirve el dashboard HTML como
página principal.
"""

import os
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Crear aplicación Flask
# =============================================================================

app = Flask(__name__)
CORS(app)  # Habilitar CORS para peticiones cross-origin

# Configuración desde archivo config.py
app.config.from_pyfile("config.py", silent=True)

# =============================================================================
# Inicialización de componentes
# =============================================================================

def initialize() -> None:
    """Inicializa la base de datos y arranca el generador de datos."""
    from database import initialize_database
    from data_generator import start_generator

    logger.info("=" * 60)
    logger.info("Iniciando Dashboard de Monitoreo Hospitalario LoRaWAN")
    logger.info("=" * 60)

    # 1. Inicializar BD (tablas + seed de 180 dispositivos)
    logger.info("Paso 1/2: Inicializando base de datos...")
    initialize_database()
    logger.info("Base de datos lista.")

    # 2. Arrancar generador de datos mock en thread daemon
    logger.info("Paso 2/2: Arrancando generador de datos LoRaWAN...")
    start_generator()
    logger.info("Generador de datos iniciado.")

    logger.info("=" * 60)
    logger.info("Sistema listo. Navega a http://localhost:5000")
    logger.info("=" * 60)


# =============================================================================
# Rutas de la aplicación
# =============================================================================

@app.route("/")
def index():
    """
    Ruta principal: sirve el dashboard HTML.
    """
    return render_template("dashboard.html")


@app.route("/health")
def health():
    """
    Endpoint de salud para verificar que el servidor está funcionando.
    """
    return jsonify({
        "status": "ok",
        "service": "Hospital LoRaWAN Dashboard",
        "version": "1.0.0",
    })


# =============================================================================
# Registrar rutas de la API
# =============================================================================

# Importar y registrar el blueprint de rutas API
from routes import api_bp
app.register_blueprint(api_bp)

# =============================================================================
# Punto de entrada principal
# =============================================================================

if __name__ == "__main__":
    initialize()

    from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
