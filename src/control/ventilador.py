# control/ventilador.py

"""
VentiladorCtrl
==============
Lógica de control para:
 • Ventiladores de 12 V (PIN_VENTILADOR)
 • Actuadores lineales que cierran la compuerta (PIN_ACTUADOR_CERRAR)

Comportamiento:
------------------------------------------------------------------
Temp_armario ≥ TEMPERATURA_UMBRAL_ALTA  ➜  Ventilador ON, compuerta ABIERTA
Temp_armario ≤ TEMPERATURA_UMBRAL_BAJA ➜  Ventilador OFF,    compuerta CERRADA
            (pulso de PULSO_ACTUADOR_S s al actuador; luego se desacopla)
------------------------------------------------------------------

Esta clase **ya NO** contempla control por temperatura de CPU.  
La lectura de CPU puede hacerse por separado sin afectar a estos actuadores.
"""

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

# ---------------- CONSTANTES -------------------
PIN_VENTILADOR       = 18   # GPIO 18 (BCM)
PIN_ACTUADOR_CERRAR  = 22   # GPIO 22 (BCM)

TEMPERATURA_UMBRAL_ALTA = 27.0   # °C – encender ventilador
TEMPERATURA_UMBRAL_BAJA = 26.0   # °C – apagar ventilador

PULSO_ACTUADOR_S      = 15.0    # segundos que permanece HIGH el actuador al cerrar

class VentiladorCtrl:
    def __init__(
        self,
        pin_ventilador: int = PIN_VENTILADOR,
        pin_actuador_cerrar: int = PIN_ACTUADOR_CERRAR,
        temp_on: float = TEMPERATURA_UMBRAL_ALTA,
        temp_off: float = TEMPERATURA_UMBRAL_BAJA,
    ) -> None:
        # Pines y umbrales
        self.pin_ventilador      = pin_ventilador
        self.pin_actuador_cerrar = pin_actuador_cerrar
        self.temp_on             = temp_on
        self.temp_off            = temp_off

        # Estados internos
        self.estado_ventilador = False   # False = OFF
        self.estado_actuador   = False   # False = compuerta relajada
        self._timer_actuador   = None

        # Configuración GPIO
        if GPIO_DISPONIBLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_ventilador, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin_actuador_cerrar, GPIO.OUT, initial=GPIO.LOW)

        # Callback externo para cambios de estado del ventilador
        self.callback_estado_ventilador = None

        log.info("VentiladorCtrl inicializado")

    def controlar_por_temperatura(self, temperatura: float | None) -> None:
        """
        Control principal: llamar a este método en cada ciclo de lectura.
        Solo actúa si temperatura no es None.
        """
        if temperatura is None:
            return

        # Encender ventilador y abrir compuerta
        if temperatura >= self.temp_on and not self.estado_ventilador:
            self._ventilador_on()

        # Apagar ventilador y cerrar compuerta
        elif temperatura <= self.temp_off and self.estado_ventilador:
            self._ventilador_off()

    # ================== ACCIONES LOW-LEVEL ============================
    def _ventilador_on(self) -> None:
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_ventilador, GPIO.HIGH)      # Ventilador ON
            GPIO.output(self.pin_actuador_cerrar, GPIO.LOW)  # Compuerta ABIERTA

        self.estado_ventilador = True
        self.estado_actuador   = False
        self._cancelar_timer_actuador()

        log.info("🌡️ Ventilador ON  |  Compuerta ABIERTA")
        if self.callback_estado_ventilador:
            self.callback_estado_ventilador(True)

    def _ventilador_off(self) -> None:
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_ventilador, GPIO.LOW)        # Ventilador OFF
            GPIO.output(self.pin_actuador_cerrar, GPIO.HIGH)  # Inicia cierre

        self.estado_ventilador = False
        self.estado_actuador   = True

        log.info("❄️ Ventilador OFF | Cerrando compuerta…")
        if self.callback_estado_ventilador:
            self.callback_estado_ventilador(False)

        # Tras PULSO_ACTUADOR_S segundos, desactiva el actuador
        self._timer_actuador = threading.Timer(PULSO_ACTUADOR_S, self._reset_actuador)
        self._timer_actuador.start()

    def _reset_actuador(self) -> None:
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_actuador_cerrar, GPIO.LOW)
        self.estado_actuador = False
        self._timer_actuador = None
        log.info("🔧 Actuador desactivado (ahorro de energía)")

    def _cancelar_timer_actuador(self) -> None:
        if self._timer_actuador:
            self._timer_actuador.cancel()
            self._timer_actuador = None

    # ================== LIMPIEZA GLOBAL ===============================
    def cleanup(self) -> None:
        """
        Llamar al cerrar el programa para asegurar que todos los
        pines quedan en estado LOW y no quedan timers activos.
        """
        self._cancelar_timer_actuador()
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_ventilador, GPIO.LOW)
            GPIO.output(self.pin_actuador_cerrar, GPIO.LOW)
        log.info("VentiladorCtrl limpiado")
