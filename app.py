from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy import text
from time import time

from backend.base_datos import engine
from backend.login import validar_usuario, iniciar_sesion, cerrar_sesion, esta_logueado
from backend.excel import leer_excel, procesar_excel, guardar_en_base

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key")

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# 🔐 LOGIN REQUIRED
# =========================
def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not esta_logueado():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# =========================
# 📂 GUARDAR ARCHIVO
# =========================
def guardar_archivo(file):
    if not file or file.filename == "":
        return None

    nombre = secure_filename(file.filename)
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
    file.save(ruta)
    return ruta


# =========================
# ⚠️ ERROR
# =========================
def error(mensaje):
    return render_template("resultado.html", mensaje=mensaje, registros=0)


# =========================
# 🔑 LOGIN
# =========================
def obtener_intentos(ip):
    query = text("""
        SELECT intentos, bloqueado_hasta
        FROM login_intentos
        WHERE ip = :ip
        LIMIT 1
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"ip": ip}).fetchone()

    if result:
        return {"intentos": result[0], "bloqueado_hasta": result[1]}
    else:
        return {"intentos": 0, "bloqueado_hasta": 0}


def guardar_intentos(ip, intentos, bloqueado_hasta):
    query = text("""
        INSERT INTO login_intentos (ip, intentos, bloqueado_hasta)
        VALUES (:ip, :intentos, :bloqueado)
        ON DUPLICATE KEY UPDATE
            intentos = :intentos,
            bloqueado_hasta = :bloqueado
    """)

    with engine.connect() as conn:
        conn.execute(query, {
            "ip": ip,
            "intentos": intentos,
            "bloqueado": bloqueado_hasta
        })
        conn.commit()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("username")
        password = request.form.get("password")
        ip = request.remote_addr

        data = obtener_intentos(ip)

        if data["bloqueado_hasta"] > time():
            return render_template("login.html", error="Demasiados intentos")

        if validar_usuario(usuario, password):
            guardar_intentos(ip, 0, 0)
            iniciar_sesion(usuario)
            return redirect(url_for("index"))
        else:
            data["intentos"] += 1

            if data["intentos"] >= 5:
                data["bloqueado_hasta"] = time() + 60

            guardar_intentos(ip, data["intentos"], data["bloqueado_hasta"])
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


# =========================
# 🔓 LOGOUT
# =========================
@app.route("/logout")
def logout():
    cerrar_sesion()
    return redirect(url_for("login"))


# =========================
# 🏠 HOME
# =========================
@app.route("/")
@login_requerido
def index():
    return render_template("index.html")


# =========================
# 🔥 PROCESOS
# =========================
@app.route("/proceso")
@login_requerido
def proceso():

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT PROCESO
            FROM vista_cm01_final
            WHERE PROCESO IS NOT NULL
            ORDER BY PROCESO
        """))

        procesos = [row[0] for row in result.fetchall()]

    return render_template("proceso.html", procesos=procesos)


# =========================
# 📊 API GRAFICA (ARREGLADA)
# =========================
@app.route("/api/proceso_chart")
@login_requerido
def proceso_chart():

    proceso = request.args.get("proceso")
    sub_proceso = request.args.get("sub_proceso")

    where = "WHERE PROCESO = :proceso"
    params = {"proceso": proceso}

    if sub_proceso:
        where += " AND sub_proceso = :sub_proceso"
        params["sub_proceso"] = sub_proceso

    query = text(f"""
        SELECT 
            Centro,
            Status,
            ROUND(SUM(COALESCE(necesidad, 0)), 0) as total
        FROM vista_cm01_final
        {where}
        GROUP BY Centro, Status
        ORDER BY Centro
    """)

    with engine.connect() as conn:
        result = conn.execute(query, params).fetchall()

    nombres = {
        "1000": "Bogotá",
        "5000": "Cali",
        "6000": "Bucaramanga"
    }

    centros = []
    data_dict = {}
    statuses = set()

    for row in result:
        centro = nombres.get(str(row[0]), str(row[0]))
        status = row[1]
        total = row[2]

        if centro not in centros:
            centros.append(centro)

        statuses.add(status)

        if centro not in data_dict:
            data_dict[centro] = {}

        data_dict[centro][status] = total

    colores = {
        "ABIE": "#f1c40f",     # amarillo
        "NOTP": "#e67e22",     # naranja
        "IMPR": "#3498db",     # azul
        "LIB.": "#3498db"      # también azul
    }   

    datasets = []

    for status in statuses:
        data = []
        for centro in centros:
            data.append(data_dict.get(centro, {}).get(status, 0))

        datasets.append({
            "label": status,
            "data": data,
            "backgroundColor": colores.get(status, "#95a5a6")
        })

    return jsonify({
        "labels": centros,
        "datasets": datasets
    })

# =========================
# 🔥 API VALORES (FILTRO EXCEL)
# =========================
@app.route("/api/valores_columna")
@login_requerido
def valores_columna():

    columna = request.args.get("columna")

    if not columna:
        return jsonify([])

    query = text(f"""
        SELECT DISTINCT `{columna}`
        FROM vista_cm01_final
        WHERE `{columna}` IS NOT NULL
        ORDER BY `{columna}`
        LIMIT 100
    """)

    with engine.connect() as conn:
        result = conn.execute(query).fetchall()

    valores = [str(row[0]) for row in result]

    return jsonify(valores)


# =========================
# 📊 DASHBOARD (FILTRO EXCEL)
# =========================
@app.route("/dashboard")
@login_requerido
def dashboard():

    page = int(request.args.get("page", 1))
    sort = request.args.get("sort", "")
    order = request.args.get("order", "asc")

    columnas_filtro = request.args.getlist("column[]")
    valores_filtro = request.args.getlist("search[]")

    per_page = 50
    offset = (page - 1) * per_page

    try:
        with engine.connect() as conn:

            columnas_query = conn.execute(text("SELECT * FROM vista_cm01_final LIMIT 1"))
            columnas = list(columnas_query.keys())

            if sort not in columnas:
                sort = columnas[0]

            if order not in ["asc", "desc"]:
                order = "asc"

            # 🔥 WHERE DINÁMICO
            where_clauses = []
            params = {}

            for i, col in enumerate(columnas_filtro):
                if col and i < len(valores_filtro) and valores_filtro[i]:
                    key = f"valor_{i}"
                    where_clauses.append(f"`{col}` LIKE :{key}")
                    params[key] = f"%{valores_filtro[i]}%"

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            query = f"""
                SELECT *
                FROM vista_cm01_final
                {where_sql}
                ORDER BY `{sort}` {order}
                LIMIT :limit OFFSET :offset
            """

            params["limit"] = per_page
            params["offset"] = offset

            datos = conn.execute(text(query), params).fetchall()

            count_query = f"SELECT COUNT(*) FROM vista_cm01_final {where_sql}"
            total = conn.execute(text(count_query), params).scalar()

            total_pages = (total // per_page) + (1 if total % per_page else 0)

        return render_template(
            "dashboard.html",
            columnas=columnas,
            datos=datos,
            page=page,
            total_pages=total_pages,
            sort=sort,
            order=order
        )

    except Exception as e:
        return render_template(
            "dashboard.html",
            columnas=[],
            datos=[],
            error=str(e),
            page=1,
            total_pages=1
        )


# =========================
# 📤 UPLOAD
# =========================
@app.route("/upload_form")
@login_requerido
def upload_form():
    from sqlalchemy import inspect
    tablas = inspect(engine).get_table_names()
    return render_template("upload.html", tablas=tablas)


@app.route("/preview", methods=["POST"])
@login_requerido
def preview():
    file = request.files.get("file")
    ruta = guardar_archivo(file)

    if not ruta:
        return error("No seleccionaste archivo")

    df = leer_excel(ruta)
    df, cambios = procesar_excel(df)

    tabla_html = df.head(10).to_html(classes="table table-striped", index=False)

    return render_template("preview.html", tabla=tabla_html, cambios=cambios, archivo=ruta)


@app.route("/upload", methods=["POST"])
@login_requerido
def upload():

    ruta = request.form.get("file_name")
    accion = request.form.get("accion")

    if accion == "crear":
        tabla = request.form.get("tabla_crear")
    else:
        tabla = request.form.get("tabla_existente")

    df = leer_excel(ruta)
    df, _ = procesar_excel(df)

    mensaje, registros = guardar_en_base(df, tabla, engine, accion)

    return render_template("resultado.html", mensaje=mensaje, registros=registros)


# =========================
# 🔥 API SUBPROCESOS
# =========================
@app.route("/api/subprocesos")
@login_requerido
def subprocesos():

    proceso = request.args.get("proceso")

    query = text("""
        SELECT DISTINCT sub_proceso
        FROM vista_cm01_final
        WHERE PROCESO = :proceso
        AND sub_proceso IS NOT NULL
        ORDER BY sub_proceso
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"proceso": proceso}).fetchall()

    data = [row[0] for row in result]

    return jsonify(data)


# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)