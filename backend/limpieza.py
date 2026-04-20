import pandas as pd


# =========================
# ?? LIMPIAR FECHAS
# =========================
def limpiar_fechas(col):

    # convertir a string limpio
    col = col.astype(str).str.strip()

    # valores basura comunes en SAP
    valores_invalidos = [
        "00/01/1900",
        "0",
        "",
        "nan",
        "None",
        "NaT"
    ]

    col = col.replace(valores_invalidos, None)

    # convertir a fecha
    return pd.to_datetime(col, dayfirst=True, errors="coerce")


# =========================
# ?? ARREGLAR COLUMNAS DUPLICADAS
# =========================
def arreglar_columnas_repetidas(columnas):

    nuevas = []
    contador = {}

    for col in columnas:
        col = str(col).strip()  # ?? limpia espacios invisibles

        if col in contador:
            contador[col] += 1
            nuevas.append(f"{col}_{contador[col]}")  # mejor que punto
        else:
            contador[col] = 0
            nuevas.append(col)

    return nuevas