# utils/logging_cfg.py
"""
Configuración centralizada de 'logging' para todo el proyecto.
Crea un log rotativo en /var/log/tfm_cm4.log y
muestra también los mensajes por pantalla.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Ruta del archivo de log. Si no existe, se crea automáticamente.
LOG_PATH = Path.home() / "tfm_cm4.log"

def setup(level: int = logging.INFO) -> None:
    """
    Inicializa el sistema de logs.  
    Llamar una sola vez al inicio del programa (en main.py).
    """
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    handlers = [
        RotatingFileHandler(
            LOG_PATH,
            maxBytes=2_000_000,   # 2 MB antes de rotar
            backupCount=7         # conserva 7 archivos antiguos
        ),
        logging.StreamHandler()   # también a la consola
    ]

    logging.basicConfig(level=level, format=fmt, handlers=handlers)
