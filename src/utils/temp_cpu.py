def obtener_temperatura_cpu() -> float:
    """
    Lee la temperatura del procesador (SoC) del Raspberry Pi desde /sys/class/thermal.
    Devuelve la temperatura en grados Celsius como float.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_miligrados = int(f.read().strip())
            return temp_miligrados / 1000.0
    except Exception as e:
        from logging import getLogger
        getLogger("utils.temp_cpu").warning(f"No se pudo leer temperatura CPU: {e}")
        return None
