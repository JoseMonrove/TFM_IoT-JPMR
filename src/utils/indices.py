import math

def calcular_indices(datos: dict) -> dict:
    resultados = {}

    # Extraer variables necesarias (usando .get para evitar errores)
    W860 = float(datos.get("W_860nm", 0))
    R610 = float(datos.get("R_610nm", 0))
    C460 = float(datos.get("C_460nm", 0))
    F535 = float(datos.get("F_535nm", 0))
    E510 = float(datos.get("E_510nm", 0))
    L940 = float(datos.get("L_940nm", 0))
    J705 = float(datos.get("J_705nm", 0))
    I645 = float(datos.get("I_645nm", 0))
    luz = float(datos.get("luz", 0))
    Taire = float(datos.get("temperatura", 0))
    HR = float(datos.get("humedad", 0))
    u2 = float(datos.get("velocidad_viento_prom", 0))
    Tsuelo = float(datos.get("temperatura_suelo", 0))

    # NDVI
    if (W860 + R610) != 0:
        resultados["NDVI"] = round((W860 - R610) / (W860 + R610), 3)

    # GNDVI
    if (W860 + E510) != 0:
        resultados["GNDVI"] = round((W860 - E510) / (W860 + E510), 3)

    # NDRE
    if (W860 + J705) != 0:
        resultados["NDRE"] = round((W860 - J705) / (W860 + J705), 3)

    # SAVI
    if (W860 + R610 + 0.5) != 0:
        resultados["SAVI"] = round(1.5 * (W860 - R610) / (W860 + R610 + 0.5), 3)

    # EVI
    num_evi = 2.5 * W860 - R610
    den_evi = W860 + 6 * R610 - 7.5 * C460 + 1
    if den_evi != 0:
        resultados["EVI"] = round(num_evi / den_evi, 3)

    # MCARI
    if R610 != 0:
        mcari = ((F535 - R610) - 0.2 * (F535 - E510)) * (F535 / R610)
        resultados["MCARI"] = round(mcari, 3)

    # MTVI2
    mtvi2 = 1.5 * (1.2 * (L940 - E510) - 2.5 * (R610 - E510))
    resultados["MTVI2"] = round(mtvi2, 3)

    # Evapotranspiración estimada (FAO simplificada)
    try:
        delta = 4098 * (0.6108 * math.exp((17.27 * Taire) / (Taire + 237.3))) / ((Taire + 237.3) ** 2)
        es = 0.6108 * math.exp((17.27 * Taire) / (Taire + 237.3))
        ea = es * (HR / 100)
        gamma = 0.066
        Rn = luz
        G = 0

        if (delta + gamma * (1 + 0.34 * u2)) != 0 and (Taire + 273) != 0:
            ET = (0.408 * delta * (Rn - G) + gamma * 900 / (Taire + 273) * u2 * (es - ea)) / (delta + gamma * (1 + 0.34 * u2))
            resultados["ET"] = round(ET, 3)
    except:
        pass

    # Diferencia temperatura aire-suelo
    resultados["Delta_T"] = round(Taire - Tsuelo, 3)

    # Índice Temperatura-Humedad (THI)
    resultados["THI"] = round(Taire - (0.55 - 0.0055 * HR) * (Taire - 14.5), 3)

    # Red Edge Position (REP)
    denom_rep = I645 - J705
    if denom_rep != 0:
        rep = 700 + 40 * (R610 + L940) / 2 - J705 * (R610 + L940) / denom_rep
        resultados["REP"] = round(rep, 3)

    # PAR estimado
    if luz != 0:
        resultados["PAR"] = round(luz / 54, 3)

    return resultados
