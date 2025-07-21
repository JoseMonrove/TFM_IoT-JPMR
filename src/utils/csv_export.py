# utils/csv_export.py
import csv, os, logging
from datetime import datetime

log = logging.getLogger(__name__)

CSV_FILE = "datos_muestreo.csv"

def export_row(datos: dict, campos: list[str]) -> None:
    if not datos:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fila = [timestamp]

    for campo in campos[1:]:
        val = datos.get(campo, "--")
        if isinstance(val, float):
            val = round(val, 4)
        fila.append(val)

    nuevo_archivo = not os.path.isfile(CSV_FILE)

    try:
        with open(CSV_FILE, "a", newline="") as f:
            w = csv.writer(f)
            if nuevo_archivo:
                w.writerow(campos)
            w.writerow(fila)
        log.info("Fila añadida a %s", CSV_FILE)
    except Exception:
        log.error("Error guardando CSV", exc_info=True)
