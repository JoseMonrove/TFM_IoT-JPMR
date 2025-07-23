#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from collections import OrderedDict

# ─── AÑADIR SRC/ AL PYTHONPATH ────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ─── LOGGING ───────────────────────────────────────────────────────────────────
from utils.logging_cfg import setup as logging_setup
logging_setup()
import logging
log = logging.getLogger(__name__)

# ─── IMPORTS PRINCIPALES ───────────────────────────────────────────────────────
from sensors.manager      import GestorSensores
from control.ventilador   import VentiladorCtrl
from utils.temp_cpu       import obtener_temperatura_cpu
from utils.csv_export     import export_row
from utils.tb_client      import publish_telemetry
from utils.git_info       import get_git_commit

# ─── CONSTANTES ────────────────────────────────────────────────────────────────
INTERVALO = 30  # segundos entre muestras

CAMPOS_EXPORT = [
    "timestamp",
    # Meteorología
    "direccion_viento", "velocidad_viento_prom", "velocidad_viento_max",
    "temperatura", "humedad", "presion", "luz", "indice_uv", "lluvia",
    # Suelo
    "humedad_suelo", "temperatura_suelo", "conductividad_suelo", "ph_suelo",
    # Armario
    "temperatura_armario", "humedad_armario",
    # Canales espectrales
    "A_410nm","B_435nm","C_460nm","D_485nm","E_510nm","F_535nm","G_560nm",
    "H_585nm","R_610nm","I_645nm","S_680nm","J_705nm","T_730nm","U_760nm",
    "V_810nm","W_860nm","K_900nm","L_940nm","temp_0","temp_1","temp_2",
    # CPU y Git
    "temperatura_cpu", "git_commit"
]

SECCIONES = OrderedDict([
    ("Meteorología", CAMPOS_EXPORT[1:10]),
    ("Suelo",        CAMPOS_EXPORT[10:14]),
    ("Armario",      CAMPOS_EXPORT[14:16]),
    ("Espectral",    CAMPOS_EXPORT[16:37]),
    ("CPU / Git",    ["temperatura_cpu", "git_commit"]),
])

UNIDADES = {
    "direccion_viento":    "°",
    "velocidad_viento_prom":"m/s",
    "velocidad_viento_max": "m/s",
    "temperatura":         "°C",
    "humedad":             "%",
    "presion":             "hPa",
    "luz":                 "lux",
    "indice_uv":           "UVI",
    "lluvia":              "mm",
    "humedad_suelo":       "%",
    "temperatura_suelo":   "°C",
    "conductividad_suelo": "µS/cm",
    "ph_suelo":            "pH",
    "temperatura_armario": "°C",
    "humedad_armario":     "%",
    **{ch: "a.u." for ch in CAMPOS_EXPORT[16:35]},
    "temp_espec_0":              "°C",
    "temp_espec_1":              "°C",
    "temp_espec_2":              "°C",
    "temperatura_cpu":     "°C",
    "git_commit":          "",
}

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def print_table(datos: dict):
    clear_screen()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕒 {ts}    (Ctrl+C para salir)\n")

    W_CAMPO = 30
    W_VALOR = 12
    W_UNIDAD = 12
    line_width = W_CAMPO + W_VALOR + W_UNIDAD + 4

    header = f"{'Campo':<{W_CAMPO}} | {'Valor':>{W_VALOR}} | {'Unidad':<{W_UNIDAD}}"
    print(header)
    print("-" * line_width)

    for titulo, campos in SECCIONES.items():
        print(f"\n {titulo} ".center(line_width, "-"))
        for campo in campos:
            val = datos.get(campo, "--")
            if isinstance(val, float):
                val = f"{val:.4f}"
            unidad = UNIDADES.get(campo, "")
            print(f"{campo:<{W_CAMPO}} | {val:>{W_VALOR}} | {unidad:<{W_UNIDAD}}")
    print()

def main():
    log.info("▶️ Arrancando sistema headless con CSV, ThingsBoard y Git Info")

    # ─── AUTO-GIT ───────────────────────────────────────────────
    from utils.git_auto import auto_commit_and_push
    auto_commit_and_push()
    # ─────────────────────────────────────────────────────────────

    sensores   = GestorSensores()
    ventilador = VentiladorCtrl()
    git_commit = get_git_commit()

    try:
        while True:
            datos = sensores.leer_todo()

            temp_cpu = obtener_temperatura_cpu()
            datos["temperatura_cpu"] = temp_cpu

            datos["git_commit"] = git_commit

            ventilador.controlar_por_temperatura(datos.get("temperatura_armario"))
            ventilador.controlar_por_temperatura_cpu(datos.get("temperatura_cpu"))

            export_row(datos, CAMPOS_EXPORT)

            publish_telemetry(datos)

            print_table(datos)

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        log.info("🛑 Detenido por usuario")
    finally:
        log.info("🧹 Limpiando sensores y GPIO")
        sensores.cleanup()
        ventilador.cleanup()

if __name__ == "__main__":
    main()
