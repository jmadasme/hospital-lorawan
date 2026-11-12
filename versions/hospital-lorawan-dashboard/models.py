"""
models.py - Definición de modelos de datos para el Dashboard Hospitalario LoRaWAN

Utiliza dataclasses para representar Device, Reading y Alert.
Facilita la serialización a dict para las respuestas JSON de la API.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Device:
    """Representa un dispositivo sensor LoRaWAN."""
    id: int
    device_type: str
    name: str
    location: Optional[str] = None
    temp_min: float = 0.0
    temp_max: float = 0.0
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    active: int = 1

    def to_dict(self) -> dict:
        """Serializa a dict para respuestas JSON."""
        return asdict(self)


@dataclass
class Reading:
    """Representa una lectura de temperatura/humedad de un dispositivo."""
    id: int
    device_id: int
    temperature: float
    humidity: Optional[float] = None
    timestamp: str = ""

    def to_dict(self) -> dict:
        """Serializa a dict para respuestas JSON."""
        return asdict(self)


@dataclass
class Alert:
    """Representa una alerta generada por una lectura fuera de rango."""
    id: int
    device_id: int
    reading_id: Optional[int] = None
    parameter: str = "temperature"
    value: float = 0.0
    min_limit: Optional[float] = None
    max_limit: Optional[float] = None
    message: str = ""
    severity: str = "warning"
    resolved: int = 0
    created_at: str = ""

    def to_dict(self) -> dict:
        """Serializa a dict para respuestas JSON."""
        return asdict(self)
