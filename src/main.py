#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time

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
from sensors.manager import GestorSensores
from control.ventilador import VentiladorCtrl
from utils.temp_cpu import obtener_temperatura_cpu
from utils.csv_export import export_row
from utils.tb_client import publish_telemetry
from utils.git_info import get_git_commit

# ─── CONSTANTES ────────────────────────────────────────────────────────────────
INTERVALO = 30  # segundos entre muestras

# Definimos aquí EL ORDEN en que queremos que aparezcan los campos
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
    # Índices
    "NDVI","GNDVI","NDRE","SAVI","EVI","MCARI","MTVI2",
    "ET","Delta_T","THI","REP","PAR",
    # CPU y Git
    "temperatura_cpu", "git_commit"
]

# ─── FUNCIONES AUXILIARES ─────────────────────────────────────────────────────
def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def print_table(datos: dict):
    clear_screen()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕒 {ts}    (Ctrl+C para salir)\n")
    print(f"{'Campo':<30}Valor")
    print("-" * 50)
    # Recorremos en el orden de CAMPOS_EXPORT (sin timestamp)
    for campo in CAMPOS_EXPORT[1:]:
        val = datos.get(campo, "--")
        if isinstance(val, float):
            val = f"{val:.4f}"
        print(f"{campo:<30}{val}")
    print()

# ─── PROGRAMA PRINCIPAL ────────────────────────────────────────────────────────
def main():
    log.info("▶️ Arrancando sistema headless con CSV, ThingsBoard y Git Info")
    sensores = GestorSensores()
    ventilador = VentiladorCtrl()
    git_commit = get_git_commit()

    try:
        while True:
            # 1) Leer todos los sensores e índices
            datos = sensores.leer_todo()

            # 2) Temperatura CPU
            temp_cpu = obtener_temperatura_cpu()
            datos["temperatura_cpu"] = temp_cpu

            # 3) Git commit
            datos["git_commit"] = git_commit

            # 4) Control ventilador
            ventilador.controlar_por_temperatura(datos.get("temperatura_armario"))
            ventilador.controlar_por_temperatura_cpu(datos.get("temperatura_cpu"))

            # 5) Guardar CSV
            export_row(datos, CAMPOS_EXPORT)

            # 6) Enviar a ThingsBoard
            publish_telemetry(datos)

            # 7) Mostrar por consola
            print_table(datos)

            # 8) Esperar
            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        log.info("🛑 Detenido por usuario")
    finally:
        log.info("🧹 Limpiando sensores y GPIO")
        sensores.cleanup()
        ventilador.cleanup()

if __name__ == "__main__":
    main()
