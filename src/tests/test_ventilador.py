import pytest
from control.ventilador import VentiladorCtrl, PULSO_CIERRE

@pytest.fixture
def v():
    """Instancia limpia para cada test."""
    return VentiladorCtrl()

def test_encender_ventilador_y_compuerta_abierta(v):
    # Llamamos directamente al método que enciende el ventilador y abre la compuerta
    v._encender()
    assert v.estado_vent       is True,  "El ventilador debería quedar encendido"
    assert v.estado_ventilador is True,  "Alias estado_ventilador debe ser True"
    assert v.estado_act        is False, "El actuador no debe estar activo al encender"

def test_apagar_ventilador_y_compuerta_cerrada(v):
    # Primero lo encendemos para luego apagar
    v._encender()
    # Ahora llamamos al apagado
    v._apagar()
    assert v.estado_vent       is False, "El ventilador debería quedar apagado"
    assert v.estado_ventilador is False, "Alias estado_ventilador debe ser False"
    assert v.estado_act        is True,  "El actuador debe quedar activo al apagar"

def test_reset_actuador(v):
    # Simula un apagado para que el actuador quede activo
    v._apagar()
    assert v.estado_act is True, "Tras apagar, el actuador debería estar activo"
    # Llamamos al reset manual (en lugar de esperar el timer)
    v._reset_act()
    assert v.estado_act is False, "Después de reset, el actuador debe quedar desactivado"

def test_pulso_cierre_programa_timer(v, monkeypatch):
    # Aquí comprobamos que _apagar lanza un timer de la duración correcta
    timers = []
    monkeypatch.setattr("threading.Timer", lambda t, fn: timers.append((t, fn)) or type("T", (), {"start": lambda self: None})())
    # Llamamos al apagado
    v._apagar()
    # Debe haberse creado exactamente un timer
    assert len(timers) == 1
    duracion, funcion = timers[0]
    assert duracion == PULSO_CIERRE, f"El pulso debe durar {PULSO_CIERRE}s"
    assert funcion == v._reset_act, "El timer debe llamar a _reset_act"

def test_control_manual_apertura_cierre(v):
    # Alternando manualmente los pines
    # Abrir (ventilador ON, compuerta abierta)
    v._encender()
    # Cerrar (ventilador OFF, compuerta activa)
    v._apagar()
    # Volver a abrir
    v._encender()
    assert v.estado_vent       is True
    assert v.estado_act        is False
