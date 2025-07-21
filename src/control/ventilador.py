# control/ventilador.py
import logging, threading
log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False
    log.warning("RPi.GPIO no disponible – modo simulación")

# Pines
PIN_VENTILADOR      = 18
PIN_ACTUADOR_CERRAR = 22

# Umbrales armario
TEMP_ON  = 27.0
TEMP_OFF = 26.0

# Umbrales CPU (bajados para que entren en rango real)
CPU_ON   = 60.0
CPU_OFF  = 50.0

# Duración pulso cierre (s)
PULSO_CIERRE = 15.0

class VentiladorCtrl:
    def __init__(self,
                 pin_vent=PIN_VENTILADOR,
                 pin_act=PIN_ACTUADOR_CERRAR,
                 temp_on=TEMP_ON,
                 temp_off=TEMP_OFF):
        self.pin_vent       = pin_vent
        self.pin_act        = pin_act
        self.temp_on        = temp_on
        self.temp_off       = temp_off
        self.estado_vent    = False
        self.estado_act     = False
        self._timer_act     = None

        if GPIO_DISPONIBLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_vent, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin_act,  GPIO.OUT, initial=GPIO.LOW)

        log.info("VentiladorCtrl inicializado")

    def controlar_por_temperatura(self, temp_armario):
        if temp_armario is None:
            return
        if temp_armario >= self.temp_on and not self.estado_vent:
            self._encender()
        elif temp_armario <= self.temp_off and self.estado_vent:
            self._apagar()

    def _encender(self):
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.HIGH)
            GPIO.output(self.pin_act,  GPIO.LOW)
        self.estado_vent = True
        self.estado_act  = False
        self._cancelar_timer()
        log.info("🌡️ Ventilador ON | Compuerta ABIERTA")

    def _apagar(self):
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.LOW)
            GPIO.output(self.pin_act,  GPIO.HIGH)
        self.estado_vent = False
        self.estado_act  = True
        log.info("❄️ Ventilador OFF | Cerrando compuerta…")
        # pulso de cierre
        self._timer_act = threading.Timer(PULSO_CIERRE, self._reset_act)
        self._timer_act.start()

    def _reset_act(self):
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_act, GPIO.LOW)
        self.estado_act = False
        self._timer_act = None
        log.info("🔧 Actuador desactivado (ahorro energía)")

    def _cancelar_timer(self):
        if self._timer_act:
            self._timer_act.cancel()
            self._timer_act = None

    def controlar_por_temperatura_cpu(self,
                                     temp_cpu,
                                     umbral_alta=CPU_ON,
                                     umbral_baja=CPU_OFF):
        if temp_cpu is None:
            return
        if temp_cpu >= umbral_alta and not self.estado_vent:
            if GPIO_DISPONIBLE:
                GPIO.output(self.pin_vent, GPIO.HIGH)
            self.estado_vent = True
            log.info(f"🌡️ Ventilador ON (CPU={temp_cpu:.1f}°C)")
        elif temp_cpu <= umbral_baja and self.estado_vent:
            if GPIO_DISPONIBLE:
                GPIO.output(self.pin_vent, GPIO.LOW)
            self.estado_vent = False
            log.info(f"❄️ Ventilador OFF (CPU={temp_cpu:.1f}°C)")

    def cleanup(self):
        self._cancelar_timer()
        if GPIO_DISPONIBLE:
            GPIO.output(self.pin_vent, GPIO.LOW)
            GPIO.output(self.pin_act,  GPIO.LOW)
