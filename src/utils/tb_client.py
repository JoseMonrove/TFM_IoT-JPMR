# tb_client.py
import requests
import logging

log = logging.getLogger(__name__)

VPS_URL = "http://217.154.101.202:5000/datos"  # sin barra al final

def publish_telemetry(payload: dict) -> None:
    """Envía el diccionario a tu backend Flask vía HTTP POST."""
    try:
        response = requests.post(VPS_URL, json=payload, timeout=5)
        response.raise_for_status()
    except Exception:
        log.error("Error enviando datos al VPS", exc_info=True)
