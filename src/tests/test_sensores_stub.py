# tests/test_sensores_stub.py
from sensors.manager import GestorSensores

def test_keys_meteorologicos():
    g = GestorSensores()
    datos = g.leer_datos_meteorologicos()

    # Las claves básicas deben existir
    for clave in ("temperatura", "humedad", "luz"):
        assert clave in datos, f"Falta {clave}"
