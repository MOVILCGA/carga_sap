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
    # normalizar columnas
    # -------------------------
    columnas = [col.lower().strip() for col in df.columns]

    # -------------------------
    # detectar tipo
    # -------------------------
    if "dimensión 1" in columnas:
        tipo = "sap_1"

    elif "centro" in columnas and "proceso" in columnas:
        tipo = "procesos"

    elif "mandt" in columnas and "vbeln" in columnas and "matnr" in columnas:
        tipo = "sap_full"

    elif "centro" in columnas:
        tipo = "sap_2"

    elif "dpto-dest" in columnas and "municipio-dest" in columnas:
        tipo = "logistica"

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
            "subproceso": "sub_proceso",
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

        df = df.rename(columns=nuevas)
        cambios.append("Se estandarizaron nombres de columnas")

        if "turnos" in df.columns:
            df["turnos"] = pd.to_numeric(df["turnos"], errors="coerce")

        if "cant_equipos" in df.columns:
            df["cant_equipos"] = pd.to_numeric(df["cant_equipos"], errors="coerce")

    # =========================
    # 📦 SAP FULL (NUEVO 🔥)
    # =========================
    elif tipo == "sap_full":

        cambios.append("Archivo detectado como SAP FULL")

        mapa = {
            "mandt": "mandt",
            "id": "id",
            "gjahr": "gjahr",
            "mes": "mes",
            "status": "status",
            "origen": "origen",
            "auart": "auart",
            "vkbur": "vkbur",
            "vbeln": "vbeln",
            "posnr": "posnr",
            "vdatu": "vdatu",
            "aufnr": "aufnr",
            "matnr": "matnr",
            "arktx": "descripcion",
            "charg": "lote",
            "mvgr1": "grupo_material",
            "bezei": "descripcion_grupo",
            "ntgew": "peso_neto",
            "gewei": "unidad_peso",
            "netpr": "precio",
            "werks": "centro",
            "vrkme": "unidad_venta",
            "kwmeng": "cantidad",
            "land1": "pais",
            "name1": "cliente",
            "ort01": "ciudad",
            "stras": "direccion",
            "lzone": "zona",
            "deszo": "desc_zona",
            "konda": "condicion",
            "desko": "desc_condicion",
            "car1": "car1",
            "car2": "car2",
            "car3": "car3",
            "car4": "car4",
            "car5": "car5",
            "car6": "car6",
            "car7": "car7",
            "istat_auf": "estado_sistema",
            "ustat_auf": "estado_usuario",
            "waerk": "moneda",
            "kursk": "tasa_cambio",
            "valor_pos": "valor_pos",
            "nw_fh_entrega": "fecha_entrega",
            "valor_ped": "valor_pedido",
            "bname": "usuario",
            "f_registro": "fecha_registro",
            "nombre_usuario": "nombre_usuario"
        }

        nuevas = {}
        for col in df.columns:
            key = col.lower().strip()
            if key in mapa:
                nuevas[col] = mapa[key]

        df = df.rename(columns=nuevas)
        cambios.append("Se estandarizaron columnas SAP FULL")

        # FECHAS
        for col in ["vdatu", "fecha_entrega", "fecha_registro"]:
            if col in df.columns:
                df[col] = limpiar_fechas(df[col])

        # NUMÉRICOS
        for col in ["peso_neto", "precio", "cantidad", "tasa_cambio", "valor_pos", "valor_pedido"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # FORMATO SAP (CLAVES)
        if "vbeln" in df.columns:
            df["vbeln"] = df["vbeln"].astype(str).str.zfill(10)

        if "posnr" in df.columns:
            df["posnr"] = df["posnr"].astype(str).str.zfill(6)

        if "matnr" in df.columns:
            df["matnr"] = df["matnr"].astype(str).str.zfill(18)

        cambios.append("Se normalizaron claves SAP")

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

        if "Fec. Entrega" in df.columns:
            df["Fec. Entrega"] = limpiar_fechas(df["Fec. Entrega"])

    # =========================
    # 📦 SAP 2
    # =========================
    elif tipo == "sap_2":

        cambios.append("Archivo detectado como SAP tipo 2")

        if "Liberación real" in df.columns:
            df["Liberación real"] = limpiar_fechas(df["Liberación real"])

    # =========================
    # 🚚 LOGISTICA
    # =========================
    elif tipo == "logistica":

        cambios.append("Archivo detectado como LOGISTICA")

        mapa = {
            "dpto-dest": "dpto_dest",
            "municipio-dest": "municipio_dest",
            "tiempo entrega": "tiempo_entrega"
        }

        nuevas = {}
        for col in df.columns:
            key = col.lower().strip().replace("\n", " ")
            if key in mapa:
                nuevas[col] = mapa[key]

        df = df.rename(columns=nuevas)

        if "tiempo_entrega" in df.columns:
            df["tiempo_entrega"] = pd.to_numeric(df["tiempo_entrega"], errors="coerce")

    # -------------------------
    # eliminar duplicados
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