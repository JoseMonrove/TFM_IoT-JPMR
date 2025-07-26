# src/control/ventilador.py

import logging
import threading

log = logging.getLogger(__name__)

# ---------------- GPIO OPCIONAL ----------------
try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False
    log.warning("RPi.GPIO no disponible – modo simulación")

# Pines de control
PIN_VENTILADOR      = 18   # GPIO 18 (BCM)
PIN_ACTUADOR_CERRAR = 22   # GPIO 22 (BCM)

# Umbrales temperatura armario
TEMP_ON     = 33.0   # °C – encender ventilador
TEMP_OFF    = 32.9   # °C – apagar ventilador y cerrar compuerta

# Duración del pulso de cierre del actuador (segundos)
PULSO_CIERRE = 15.0

class VentiladorCtrl:
    """
    Lógica de control para:
      • Ventilador 12 V (PIN_VENTILADOR)
      • Actuador lineal (PIN_ACTUADOR_CERRAR)

    Solo se basa en la temperatura del armario:
      Temp ≥ TEMP_ON  → Ventilador ON, compuerta ABIERTA
      Temp ≤ TEMP_OFF → Ventilador OFF, compuerta CERRADA
    """

    def __init__(
        self,
        pin_vent=PIN_VENTILADOR,
        pin_act=PIN_ACTUADOR_CERRAR,
        temp_on=TEMP_ON,
        temp_off=TEMP_OFF
    ):
        # Pines y umbrales
        self.pin_vent        = pin_vent
        self.pin_act         = pin_act
        self.temp_on         = temp_on
        self.temp_off        = temp_off

        # Estados internos
        self.estado_vent       = False  # usado internamente
        self.estado_ventilador = False  # alias para tests
        self.estado_act        = False  # True = compuerta cerrada
        self._timer_act       = None

        # Configuración GPIO
        if GPIO_DISPONIBLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_vent, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin_act,  GPIO.OUT, initial=GPIO.LOW)

        log.info("VentiladorCtrl inicializado (solo temp. armario)")

    def controlar_por_temperatura(self, temperatura: float | None) -> None:
        """
        Llamar en cada ciclo pasándole la temp. del armario.
        """
        if temperatura is None:
            return

        # Encender si supera umbral alto y estaba apagado
        if temperatura >= self.temp_on and not self.estado_vent:
            self._encender()

        # Apagar si baja de umbral bajo y estaba encendido
        elif temperatura <= self.temp_off and self.estado_vent:
            self._apagar()

    def _encender(self) -> None:
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.HIGH)   # Ventilador ON
            GPIO.output(self.pin_act,  GPIO.LOW)    # Compuerta ABIERTA

        self.estado_vent        = True
        self.estado_ventilador = True
        self.estado_act         = False
        self._cancelar_timer()

        log.info(" Ventilador ON  |  Compuerta ABIERTA")

    def _apagar(self) -> None:
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.LOW)    # Ventilador OFF
            GPIO.output(self.pin_act,  GPIO.HIGH)   # Inicia cierre compuerta

        self.estado_vent        = False
        self.estado_ventilador = False
        self.estado_act         = True

        log.info(" Ventilador OFF | Cerrando compuerta…")

        # Tras PULSO_CIERRE segundos, liberar actuador
        self._timer_act = threading.Timer(PULSO_CIERRE, self._reset_act)
        self._timer_act.start()

    def _reset_act(self) -> None:
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_act, GPIO.LOW)    # Compuerta relajada

        self.estado_act = False
        self._timer_act = None

        log.info(" Actuador y ventilador desactivados ")

    def _cancelar_timer(self) -> None:
        if self._timer_act:
            self._timer_act.cancel()
            self._timer_act = None

    def cleanup(self) -> None:
        """Detiene timers y deja todos los pines en LOW."""
        self._cancelar_timer()
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.LOW)
            GPIO.output(self.pin_act,  GPIO.LOW)
        log.info("VentiladorCtrl limpiado")
