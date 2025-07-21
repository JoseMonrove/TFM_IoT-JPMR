# tests/test_ventilador.py
from control.ventilador import VentiladorCtrl

def test_umbral_on_off():
    v = VentiladorCtrl()              # instancia con GPIO simulado
    # estado inicial OFF
    assert v.estado_ventilador is False

    # Por encima del umbral alto → ON
    v.controlar_por_temperatura(28.0)
    assert v.estado_ventilador is True

    # Por debajo del umbral bajo → OFF
    v.controlar_por_temperatura(25.0)
    assert v.estado_ventilador is False
