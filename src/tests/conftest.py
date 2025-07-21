"""
conftest.py
Pytest lo carga automáticamente antes de ejecutar los tests.

Añadimos la carpeta 'src' al sys.path para que los paquetes
'sensors', 'control', 'gui', 'utils' se puedan importar
independientemente del directorio desde el que lancemos pytest.
"""
import sys, pathlib

# /ruta/.../Programación Fase 2/tfm_cm4/src (carpeta donde viven los paquetes)
SRC_DIR = pathlib.Path(__file__).resolve().parents[1]

if SRC_DIR.as_posix() not in sys.path:
    sys.path.insert(0, SRC_DIR.as_posix())
