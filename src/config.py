"""Configuración central del proyecto: empresas, fechas y rutas."""
from pathlib import Path

# Cotizamos cada armadora en su bolsa principal
EMPRESAS = {
    "Toyota": "7203.T",        # Tokio (JPY)
    "Volkswagen": "VOW3.DE",   # Frankfurt (EUR)
    "BMW": "BMW.DE",           # Frankfurt (EUR)
    "Mercedes-Benz": "MBG.DE", # Frankfurt (EUR)
    "Stellantis": "STLA",      # Nueva York (USD)
    "General Motors": "GM",    # Nueva York (USD)
    "Ford": "F",               # Nueva York (USD)
    "Tesla": "TSLA",           # Nasdaq (USD)
}

FECHA_INICIO = "2016-01-01"
FECHA_FIN = None  # None = hasta hoy

# Periodo de la crisis de semiconductores (aprox.)
CRISIS_CHIPS = ("2021-01-01", "2022-12-31")

RAIZ = Path(__file__).resolve().parents[1]
DATA_RAW = RAIZ / "data" / "raw"
DATA_PROCESSED = RAIZ / "data" / "processed"
IMAGES = RAIZ / "images"
