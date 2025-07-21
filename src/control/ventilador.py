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
TEMP_ON  = 27.0   # °C – encender ventilador
TEMP_OFF = 26.0   # °C – apagar ventilador y cerrar compuerta

# Umbrales temperatura CPU (para proteger el SoC)
CPU_ON   = 70.0   # °C – encender ventilador si el CPU supera este valor
CPU_OFF  = 60.0   # °C – apagar ventilador si el CPU baja de este valor

# Duración del pulso de cierre del actuador (segundos)
PULSO_CIERRE = 15.0

class VentiladorCtrl:
    """
    Lógica de control para:
    • Ventiladores de 12 V (PIN_VENTILADOR)
    • Actuadores lineales que cierran la compuerta (PIN_ACTUADOR_CERRAR)
    """

    def __init__(
        self,
        pin_vent=PIN_VENTILADOR,
        pin_act=PIN_ACTUADOR_CERRAR,
        temp_on=TEMP_ON,
        temp_off=TEMP_OFF
    ):
        # Pines y umbrales
        self.pin_vent       = pin_vent
        self.pin_act        = pin_act
        self.temp_on        = temp_on
        self.temp_off       = temp_off

        # Estados internos
        self.estado_vent    = False
        self.estado_ventilador = False  # alias para los tests
        self.estado_act     = False
        self._timer_act     = None

        # Configuración GPIO
        if GPIO_DISPONIBLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_vent, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin_act,  GPIO.OUT, initial=GPIO.LOW)

        log.info("VentiladorCtrl inicializado")

    def controlar_por_temperatura(self, temperatura):
        """
        Llama en cada ciclo con la temp. del armario.
        Enciende/apaga ventilador y abre/cierra compuerta.
        """
        if temperatura is None:
            return

        # Encender si supera umbral alto y estaba apagado
        if temperatura >= self.temp_on and not self.estado_vent:
            self._encender()

        # Apagar si baja de umbral bajo y estaba encendido
        elif temperatura <= self.temp_off and self.estado_vent:
            self._apagar()

    def _encender(self):
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.HIGH)   # Ventilador ON
            GPIO.output(self.pin_act,  GPIO.LOW)    # Compuaerta abierta

        self.estado_vent        = True
        self.estado_ventilador = True
        self.estado_act         = False
        self._cancelar_timer()

        log.info("🌡️ Ventilador ON  |  Compuerta ABIERTA")

    def _apagar(self):
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.LOW)    # Ventilador OFF
            GPIO.output(self.pin_act,  GPIO.HIGH)   # Inicia cierre compuerta

        self.estado_vent        = False
        self.estado_ventilador = False
        self.estado_act         = True

        log.info("❄️ Ventilador OFF | Cerrando compuerta…")

        # Después de PULSO_CIERRE segundos liberamos el actuador
        self._timer_act = threading.Timer(PULSO_CIERRE, self._reset_act)
        self._timer_act.start()

    def _reset_act(self):
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_act, GPIO.LOW)    # Compuaerta relajada

        self.estado_act = False
        self._timer_act = None

        log.info("🔧 Actuador desactivado (ahorro energía)")

    def _cancelar_timer(self):
        if self._timer_act:
            self._timer_act.cancel()
            self._timer_act = None

    def controlar_por_temperatura_cpu(
        self,
        temp_cpu,
        umbral_alta=CPU_ON,
        umbral_baja=CPU_OFF
    ):
        """
        Encender/apagar ventilador en función de la temperatura del SoC.
        Protege el CPU cuando sube demasiado o baja de temperatura.
        """
        if temp_cpu is None:
            return

        # Encender si supera umbral crítico
        if temp_cpu >= umbral_alta and not self.estado_vent:
            if GPIO_DISPONIBLE:
                GPIO.output(self.pin_vent, GPIO.HIGH)
            self.estado_vent        = True
            self.estado_ventilador = True

            log.info(f"🌡️ Ventilador ON (CPU={temp_cpu:.1f}°C)")

        # Apagar si baja de temperatura segura
        elif temp_cpu <= umbral_baja and self.estado_vent:
            if GPIO_DISPONIBLE:
                GPIO.output(self.pin_vent, GPIO.LOW)
            self.estado_vent        = False
            self.estado_ventilador = False

            log.info(f"❄️ Ventilador OFF (CPU={temp_cpu:.1f}°C)")

    def cleanup(self):
        """Detiene timers y deja pines en LOW."""
        self._cancelar_timer()
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.LOW)
            GPIO.output(self.pin_act,  GPIO.LOW)
