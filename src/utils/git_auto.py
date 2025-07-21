import subprocess, os, logging, time

log = logging.getLogger(__name__)

def auto_commit_and_push():
    """
    Añade y commitea automáticamente todos los cambios pendientes en el repo,
    con un mensaje que incluye timestamp. Luego hace push al remoto origin/main.
    """
    # Directorio raíz del repo (supone que git_auto.py está en src/utils)
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    try:
        # 1) Añadir todos los cambios
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=False)

        # 2) Comprobar si hay algo realmente para commitear
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_dir
        ).decode().strip()

        if not status:
            log.debug("No hay cambios para commitear.")
            return

        # 3) Commit con timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"Auto-commit: {timestamp}"
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_dir, check=True)
        log.info("Auto-commit realizado: %s", msg)

        # 4) Push al remoto
        subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, check=True)
        log.info("Auto-push a origin/main completado")

    except Exception as e:
        log.warning("Auto-commit/push falló: %s", e, exc_info=True)
