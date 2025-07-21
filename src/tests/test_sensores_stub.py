from sensors.manager import GestorSensores

def test_leer_todo_incluye_campos_basicos_y_indices():
    g = GestorSensores()
    datos = g.leer_todo()

    # Comprueba lecturas básicas de cada sensor
    for campo in ("temperatura", "humedad_suelo", "temperatura_armario"):
        assert campo in datos, f"Falta campo {campo}"

    # Comprueba que calcula algunos índices
    for indice in ("NDVI", "GNDVI", "EVI", "THI"):
        assert indice in datos, f"Falta índice {indice}"
