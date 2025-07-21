# sensors/manager.py
"""
GestorSensores
--------------
Versión modular de tu clase original EscadaFinal.py.
"""

import time, logging, os
from pathlib import Path

import numpy as np

# ---------- LOG ----------
log = logging.getLogger(__name__)

# ---------- DEPENDENCIAS OPCIONALES ----------
try:
    import minimalmodbus
    import serial
    MODBUS_DISPONIBLE = True
except ImportError:
    MODBUS_DISPONIBLE = False

try:
    import qwiic_as7265x
    SENSOR_ESPECTRAL_DISPONIBLE = True
except ImportError:
    SENSOR_ESPECTRAL_DISPONIBLE = False

# ---------- CONSTANTES HARDWARE ----------
PUERTO_METEOROLOGICO  = "/dev/ttyAMA2"
DIRECCION_METEOROLOGICO = 1
BAUDRATE_METEOROLOGICO  = 4800

PUERTO_SUELO   = "/dev/ttyAMA4"
DIRECCION_SUELO = 1
BAUDRATE_SUELO  = 9600

PUERTO_XY_MD04   = "/dev/ttyAMA4"
DIRECCION_XY_MD04 = 5
BAUDRATE_XY_MD04  = 9600

# ---------- CLASE PRINCIPAL ----------
class GestorSensores:
    def __init__(self) -> None:
        # Instancias de bajo nivel
        self.sensor_meteorologico = None
        self.sensor_suelo         = None
        self.sensor_xy_md04       = None
        self.sensor_espectral     = None

        # Control de reintentos sensor espectral
        self.reintentos_espectral     = 0
        self.max_reintentos_espectral = 3

        # Info de conexión para el resumen
        self.info_conexion_meteorologico = {"conectado": False, "version": "N/A", "error": None}
        self.info_conexion_suelo         = {"conectado": False, "version": "N/A", "error": None}
        self.info_conexion_xy_md04       = {"conectado": False, "version": "N/A", "error": None}
        self.info_conexion_espectral     = {"conectado": False, "version": "N/A", "error": None}

        log.info("=" * 60)
        log.info("INICIALIZANDO SISTEMA DE SENSORES")
        log.info("=" * 60)

        self.inicializar_sensores()
        self.mostrar_resumen_conexiones()

    # ---------- RESUMEN DE CONEXIONES ----------
    def mostrar_resumen_conexiones(self) -> None:
        sensores = [
            ("Estación Meteorológica", self.info_conexion_meteorologico),
            ("Sensor de Suelo",        self.info_conexion_suelo),
            ("Sensor XY-MD04",         self.info_conexion_xy_md04),
            ("Sensor Espectral",       self.info_conexion_espectral),
        ]
        for nombre, info in sensores:
            estado = "✅" if info["conectado"] else "❌"
            log.info(f"{nombre:25} | {estado} | versión={info['version']} | error={info['error']}")
        log.info("=" * 60)

    # ---------- INICIALIZACIÓN ESPECTRAL ----------
    def inicializar_sensor_espectral(self) -> bool:
        if not SENSOR_ESPECTRAL_DISPONIBLE:
            log.error("Librería qwiic_as7265x no disponible – modo simulación")
            self.info_conexion_espectral = {"conectado": False, "version": "N/A",
                                            "error": "lib no disponible"}
            return False

        for intento in range(self.max_reintentos_espectral):
            try:
                log.info(f"Inicializando AS7265x (intento {intento+1})…")
                self.sensor_espectral = qwiic_as7265x.QwiicAS7265x()
                if not self.sensor_espectral.is_connected():
                    msg = "AS7265x no detectado en el bus I²C"
                    log.error(msg)
                    continue

                if not self.sensor_espectral.begin():
                    msg = "AS7265x no responde al comando begin()"
                    log.error(msg)
                    continue

                tipo  = self.sensor_espectral.get_device_type()
                v_hw  = self.sensor_espectral.get_hardware_version()
                v_fw  = self.sensor_espectral.get_major_firmware_version()
                ver   = f"HW:{v_hw} FW:{v_fw}"
                log.info(f"Sensor AS7265x listo – {ver}")

                self.info_conexion_espectral = {"conectado": True, "version": ver, "error": None}
                self.reintentos_espectral = 0
                return True

            except Exception as e:
                log.error("Error inicializando sensor espectral", exc_info=True)

            time.sleep(2)

        self.sensor_espectral = None
        self.info_conexion_espectral = {"conectado": False, "version": "N/A",
                                        "error": "máx reintentos"}
        return False

    # ---------- INICIALIZAR TODOS LOS SENSORES ----------
    def inicializar_sensores(self) -> None:
        # ---- METEORO ----
        if MODBUS_DISPONIBLE:
            try:
                log.info("Inicializando estación meteorológica…")
                inst = minimalmodbus.Instrument(PUERTO_METEOROLOGICO, DIRECCION_METEOROLOGICO)
                inst.serial.baudrate  = BAUDRATE_METEOROLOGICO
                inst.serial.timeout   = 2
                inst.mode = minimalmodbus.MODE_RTU
                # lectura test
                inst.read_register(0x01F9, 0, signed=True)
                self.sensor_meteorologico = inst
                self.info_conexion_meteorologico = {"conectado": True, "version": "Modbus RTU", "error": None}
                log.info("✅ Estación meteorológica conectada")
            except Exception as e:
                log.error("Error estación meteorológica", exc_info=True)
                self.info_conexion_meteorologico["error"] = str(e)
        else:
            log.error("minimalmodbus NO disponible – sensores en modo simulación")

        # ---- SUELO ----
        if MODBUS_DISPONIBLE:
            try:
                log.info("Inicializando sensor de suelo…")
                inst = minimalmodbus.Instrument(PUERTO_SUELO, DIRECCION_SUELO)
                inst.serial.baudrate = BAUDRATE_SUELO
                inst.serial.timeout  = 2
                inst.mode = minimalmodbus.MODE_RTU
                inst.read_register(0x0000, 0)
                self.sensor_suelo = inst
                self.info_conexion_suelo = {"conectado": True, "version": "Modbus RTU", "error": None}
                log.info("✅ Sensor de suelo conectado")
            except Exception as e:
                log.error("Error sensor suelo", exc_info=True)
                self.info_conexion_suelo["error"] = str(e)

        # ---- XY-MD04 ----
        if MODBUS_DISPONIBLE:
            try:
                log.info("Inicializando sensor XY-MD04…")
                inst = minimalmodbus.Instrument(PUERTO_XY_MD04, DIRECCION_XY_MD04)
                inst.serial.baudrate = BAUDRATE_XY_MD04
                inst.serial.timeout  = 2
                inst.mode = minimalmodbus.MODE_RTU
                inst.read_registers(0x0001, 2, functioncode=4)
                self.sensor_xy_md04 = inst
                self.info_conexion_xy_md04 = {"conectado": True, "version": "Modbus RTU", "error": None}
                log.info("✅ Sensor XY-MD04 conectado")
            except Exception as e:
                log.error("Error XY-MD04", exc_info=True)
                self.info_conexion_xy_md04["error"] = str(e)

        # ---- ESPECTRAL ----
        self.inicializar_sensor_espectral()
    # ---------- MÉTODOS DE LECTURA ----------
    # Cada método devuelve un dict con los mismos campos de tu script original.
    # Si el sensor físico no está disponible se devuelven valores simulados.

    # --- METEOROLÓGICOS ---
    def leer_datos_meteorologicos(self) -> dict:
        if not self.sensor_meteorologico:
            # Simulación
            return {
                "direccion_viento":      np.random.uniform(0, 360),
                "velocidad_viento_prom": np.random.uniform(0, 15),
                "velocidad_viento_max":  np.random.uniform(5, 25),
                "temperatura":           np.random.uniform(15, 35),
                "humedad":               np.random.uniform(30, 90),
                "presion":               np.random.uniform(950, 1050),
                "luz":                   np.random.randint(0, 100000),
                "indice_uv":             np.random.uniform(0, 12),
                "lluvia":                np.random.uniform(0, 5),
            }

        try:
            return {
                "direccion_viento":      self.sensor_meteorologico.read_register(0x01F7, 0),
                "velocidad_viento_prom": self.sensor_meteorologico.read_register(0x01F4, 0) / 100,
                "velocidad_viento_max":  self.sensor_meteorologico.read_register(0x01F5, 0) / 100,
                "temperatura":           self.sensor_meteorologico.read_register(0x01F9, 0, signed=True) / 10,
                "humedad":               self.sensor_meteorologico.read_register(0x01F8, 0) / 10,
                "presion":               self.sensor_meteorologico.read_register(0x01FD, 0),
                "luz":                   self.sensor_meteorologico.read_register(0x0200, 0),
                "indice_uv":             self.sensor_meteorologico.read_register(0x01FE, 0) / 10,
                "lluvia":                self.sensor_meteorologico.read_register(0x0201, 0) / 10,
            }
        except Exception as e:
            log.error("Error leyendo estación meteorológica", exc_info=True)
            return {}

    # --- SUELO ---
    def leer_datos_suelo(self) -> dict:
        if not self.sensor_suelo:
            return {
                "humedad_suelo":      np.random.uniform(20, 80),
                "temperatura_suelo":  np.random.uniform(10, 30),
                "conductividad_suelo": np.random.randint(100, 2000),
                "ph_suelo":           np.random.uniform(5.5, 8.5),
            }

        try:
            return {
                "humedad_suelo":      self.sensor_suelo.read_register(0x0000, 0) / 10,
                "temperatura_suelo":  self.sensor_suelo.read_register(0x0001, 0, signed=True) / 10,
                "conductividad_suelo": self.sensor_suelo.read_register(0x0002, 0),
                "ph_suelo":           self.sensor_suelo.read_register(0x0003, 0) / 10,
            }
        except Exception as e:
            log.error("Error leyendo sensor de suelo", exc_info=True)
            return {}

    # --- XY-MD04 (temperatura/humedad armario) ---
    def leer_datos_xy_md04(self) -> dict:
        if not self.sensor_xy_md04:
            return {
                "temperatura_armario": np.random.uniform(15, 40),
                "humedad_armario":     np.random.uniform(20, 80),
            }

        try:
            regs = self.sensor_xy_md04.read_registers(0x0001, 2, functioncode=4)
            return {
                "temperatura_armario": regs[0] / 10.0,
                "humedad_armario":     regs[1] / 10.0,
            }
        except Exception as e:
            log.error("Error leyendo sensor XY-MD04", exc_info=True)
            return {}

    # --- ESPECTRAL AS7265x ---
    def leer_datos_espectrales(self) -> dict:
        if not self.sensor_espectral:
            # Simulación con valores random
            return {
                "A_410nm": np.random.uniform(10, 100),
                "B_435nm": np.random.uniform(50, 200),
                "C_460nm": np.random.uniform(100, 1000),
                "D_485nm": np.random.uniform(50, 300),
                "E_510nm": np.random.uniform(200, 1500),
                "F_535nm": np.random.uniform(500, 2500),
                "G_560nm": np.random.uniform(400, 2200),
                "H_585nm": np.random.uniform(200, 1200),
                "R_610nm": np.random.uniform(100, 500),
                "I_645nm": np.random.uniform(50, 150),
                "S_680nm": np.random.uniform(200, 1300),
                "J_705nm": np.random.uniform(80, 400),
                "T_730nm": np.random.uniform(30, 100),
                "U_760nm": np.random.uniform(50, 150),
                "V_810nm": np.random.uniform(100, 300),
                "W_860nm": np.random.uniform(90, 250),
                "K_900nm": np.random.uniform(20, 80),
                "L_940nm": np.random.uniform(10, 50),
                "temp_0":  np.random.uniform(20, 30),
                "temp_1":  np.random.uniform(20, 30),
                "temp_2":  np.random.uniform(20, 30),
            }

        try:
            self.sensor_espectral.take_measurements_with_bulb()
            out = {
                "A_410nm": self.sensor_espectral.get_calibrated_a(),
                "B_435nm": self.sensor_espectral.get_calibrated_b(),
                "C_460nm": self.sensor_espectral.get_calibrated_c(),
                "D_485nm": self.sensor_espectral.get_calibrated_d(),
                "E_510nm": self.sensor_espectral.get_calibrated_e(),
                "F_535nm": self.sensor_espectral.get_calibrated_f(),
                "G_560nm": self.sensor_espectral.get_calibrated_g(),
                "H_585nm": self.sensor_espectral.get_calibrated_h(),
                "R_610nm": self.sensor_espectral.get_calibrated_r(),
                "I_645nm": self.sensor_espectral.get_calibrated_i(),
                "S_680nm": self.sensor_espectral.get_calibrated_s(),
                "J_705nm": self.sensor_espectral.get_calibrated_j(),
                "T_730nm": self.sensor_espectral.get_calibrated_t(),
                "U_760nm": self.sensor_espectral.get_calibrated_u(),
                "V_810nm": self.sensor_espectral.get_calibrated_v(),
                "W_860nm": self.sensor_espectral.get_calibrated_w(),
                "K_900nm": self.sensor_espectral.get_calibrated_k(),
                "L_940nm": self.sensor_espectral.get_calibrated_l(),
                "temp_0":  self.sensor_espectral.get_temperature(0),
                "temp_1":  self.sensor_espectral.get_temperature(1),
                "temp_2":  self.sensor_espectral.get_temperature(2),
            }
            self.reintentos_espectral = 0
            return out

        except Exception as e:
            log.error("Error leyendo AS7265x", exc_info=True)
            # intento de reinicialización
            self.reintentos_espectral += 1
            if self.reintentos_espectral <= self.max_reintentos_espectral:
                log.info(f"Reintento espectral {self.reintentos_espectral}")
                if self.inicializar_sensor_espectral():
                    return self.leer_datos_espectrales()
            return {}

    # ---------- LIMPIEZA ----------
    def cleanup(self) -> None:
        try:
            if self.sensor_espectral:
                try:
                    self.sensor_espectral.disable_bulb(0)
                    self.sensor_espectral.disable_bulb(1)
                    self.sensor_espectral.disable_bulb(2)
                except Exception:
                    pass
                self.sensor_espectral = None
                log.info("Limpiado sensor espectral")
        except Exception as e:
            log.error("Error durante cleanup", exc_info=True)
    
    def leer_todo(self):
        datos = {}

        # Lecturas principales
        datos_meteo = self.leer_datos_meteorologicos()
        datos_suelo = self.leer_datos_suelo()
        datos_xy = self.leer_datos_xy_md04()
        datos_espectrales = self.leer_datos_espectrales()

        if datos_meteo:
            datos.update(datos_meteo)
        if datos_suelo:
            datos.update(datos_suelo)
        if datos_xy:
            datos.update(datos_xy)
        if datos_espectrales:
            datos.update(datos_espectrales)

        # Cálculo de índices espectrales
        try:
            from utils.indices import calcular_indices
            indices = calcular_indices(datos)
            datos.update(indices)
        except Exception as e:
            from logging import getLogger
            getLogger("sensors.manager").warning(f"No se calcularon índices: {e}")

        # Añadir temperatura CPU Raspberry Pi
        from utils.temp_cpu import obtener_temperatura_cpu
        temp_cpu = obtener_temperatura_cpu()
        if temp_cpu is not None:
            datos["temperatura_cpu"] = round(temp_cpu, 2)

        return datos

