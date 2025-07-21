# utils/git_info.py
import subprocess, os

def get_git_commit() -> str:
    """
    Busca el directorio .git recorriendo hacia arriba desde este fichero,
    devuelve SHA corto o 'unknown' si no lo encuentra.
    """
    # Empieza en la carpeta de este fichero
    path = os.path.abspath(os.path.dirname(__file__))
    # Sube hasta la raíz del sistema de archivos
    while True:
        if os.path.isdir(os.path.join(path, ".git")):
            # Si encontramos .git, devolvemos el commit
            try:
                sha = subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=path,
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                return sha
            except Exception:
                return "unknown"
        # Subimos un nivel
        parent = os.path.dirname(path)
        if parent == path:
            # Llegamos arriba y no hay .git
            return "unknown"
        path = parent
