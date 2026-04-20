import pandas as pd
from sqlalchemy import inspect, text
from backend.limpieza import limpiar_fechas, arreglar_columnas_repetidas


# =========================
# 📥 LEER EXCEL
# =========================
def leer_excel(ruta):
    df = pd.read_excel(ruta)
    df.columns = df.columns.astype(str).str.strip()
    return df


# =========================
# 🧹 LIMPIAR STRINGS
# =========================
def limpiar_strings(df):
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
    return df


# =========================
# ⚙️ PROCESAR EXCEL + CAMBIOS
# =========================
def procesar_excel(df):

    cambios = []

    # -------------------------
    # eliminar columnas basura
    # -------------------------
    columnas_antes = df.columns.tolist()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]

    if len(columnas_antes) != len(df.columns):
        cambios.append("Se eliminaron columnas vacías (Unnamed)")

    # -------------------------
    # columnas duplicadas
    # -------------------------
    columnas_antes = df.columns.tolist()
    df.columns = arreglar_columnas_repetidas(df.columns)

    if columnas_antes != df.columns.tolist():
        cambios.append("Se corrigieron nombres de columnas duplicadas")

    # -------------------------
    # limpiar datos
    # -------------------------
    df = df.reset_index(drop=True)
    df = limpiar_strings(df)
    cambios.append("Se limpiaron espacios en textos")

    # -------------------------
    # detectar tipo
    # -------------------------
    columnas = [col.lower().strip() for col in df.columns]

    if "dimensión 1" in columnas:
        tipo = "sap_1"
    elif "centro" in columnas and "proceso" in columnas:
        tipo = "procesos"
    elif "centro" in columnas:
        tipo = "sap_2"
    else:
        raise Exception(f"Tipo de Excel no reconocido.\nColumnas: {df.columns.tolist()}")

    # =========================
    # 📊 PROCESOS
    # =========================
    if tipo == "procesos":

        cambios.append("Archivo detectado como estructura de PROCESOS")

        mapa = {
            "centro": "centro",
            "proceso": "proceso",
            "sub-proceso": "sub_proceso",
            "estatus 2025": "estatus_2025",
            "puesto de trabajo": "puesto_trabajo",
            "centro de costo": "centro_costo",
            "descripción puesto de trabajo": "descripcion_puesto",
            "sub2": "sub2",
            "turnos": "turnos",
            "descripción centro de costo": "descripcion_centro_costo",
            "cant. equipos": "cant_equipos"
        }

        nuevas = {}
        for col in df.columns:
            key = col.lower().strip()
            if key in mapa:
                nuevas[col] = mapa[key]

        if nuevas:
            cambios.append("Se estandarizaron nombres de columnas")

        df = df.rename(columns=nuevas)

        if "turnos" in df.columns:
            df["turnos"] = pd.to_numeric(df["turnos"], errors="coerce")
            cambios.append("Se convirtió 'turnos' a número")

        if "cant_equipos" in df.columns:
            df["cant_equipos"] = pd.to_numeric(df["cant_equipos"], errors="coerce")
            cambios.append("Se convirtió 'cant_equipos' a número")

    # =========================
    # 📦 SAP 1
    # =========================
    elif tipo == "sap_1":

        cambios.append("Archivo detectado como SAP tipo 1")

        columnas_mm = ["Esp/Diam ORG", "Dimensión 1", "Dimensión 2", "Dimensión 3"]

        for col in columnas_mm:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(" mm", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")

        cambios.append("Se convirtieron medidas (mm) a números")

        if "Fec. Entrega" in df.columns:
            df["Fec. Entrega"] = limpiar_fechas(df["Fec. Entrega"])
            cambios.append("Se formateó 'Fec. Entrega' a fecha")

        if "Fcha.Ent.Des." in df.columns:
            df["Fcha.Ent.Des."] = limpiar_fechas(df["Fcha.Ent.Des."])
            cambios.append("Se formateó 'Fcha.Ent.Des.' a fecha")

        if "Unidades" in df.columns:
            df["Unidades"] = pd.to_numeric(df["Unidades"], errors="coerce")
            cambios.append("Se convirtió 'Unidades' a número")

    # =========================
    # 📦 SAP 2
    # =========================
    elif tipo == "sap_2":

        cambios.append("Archivo detectado como SAP tipo 2")

        if "Liberación real" in df.columns:
            df["Liberación real"] = limpiar_fechas(df["Liberación real"])
            cambios.append("Se formateó 'Liberación real' a fecha")

    # -------------------------
    # duplicados
    # -------------------------
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        df = df.drop_duplicates()
        cambios.append(f"Se eliminaron {duplicados} filas duplicadas")

    return df, cambios


# =========================
# 💾 GUARDAR EN DB
# =========================
def guardar_en_base(df, nombre_tabla, engine, accion):

    inspector = inspect(engine)
    tablas = inspector.get_table_names()

    nombre_tabla = nombre_tabla.lower()

    if accion == "crear":
        df.to_sql(nombre_tabla, con=engine, if_exists="replace", index=False)
        return "Tabla creada correctamente", len(df)

    if accion == "agregar":
        if nombre_tabla not in tablas:
            raise Exception("La tabla no existe")

        df.to_sql(nombre_tabla, con=engine, if_exists="append", index=False)
        return "Datos agregados correctamente", len(df)