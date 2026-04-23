from flask import Flask, render_template, request, redirect, url_for, session
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
# 🔐 DECORADOR LOGIN
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
# ⚠️ RESPUESTA ERROR
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
# 🏠 HOME (MULTI FILTRO)
# =========================
@app.route("/")
@login_requerido
def index():

    page = int(request.args.get("page", 1))
    sort = request.args.get("sort", "")
    order = request.args.get("order", "asc")

    # 🔥 MULTI FILTROS
    columnas_filtro = request.args.getlist("column[]")
    valores_filtro = request.args.getlist("search[]")

    per_page = 50
    offset = (page - 1) * per_page

    try:
        with engine.connect() as conn:

            # 🔹 columnas
            columnas_query = conn.execute(text("SELECT * FROM vista_cm01_final LIMIT 1"))
            columnas = list(columnas_query.keys())

            # 🔥 WHERE DINÁMICO
            where_parts = []
            params = {}

            for i, (col, val) in enumerate(zip(columnas_filtro, valores_filtro)):
                if col in columnas and val:
                    key = f"search{i}"
                    where_parts.append(f"`{col}` LIKE :{key}")
                    params[key] = f"%{val}%"

            where_clause = ""
            if where_parts:
                where_clause = "WHERE " + " AND ".join(where_parts)

            # 🔃 ORDER
            if sort not in columnas:
                sort = columnas[0]

            if order not in ["asc", "desc"]:
                order = "asc"

            query = f"""
                SELECT *
                FROM vista_cm01_final
                {where_clause}
                ORDER BY `{sort}` {order}
                LIMIT :limit OFFSET :offset
            """

            params["limit"] = per_page
            params["offset"] = offset

            datos = conn.execute(text(query), params).fetchall()

            # COUNT
            count_query = f"SELECT COUNT(*) FROM vista_cm01_final {where_clause}"
            total = conn.execute(text(count_query), params).scalar()

            total_pages = (total // per_page) + (1 if total % per_page else 0)

        return render_template(
            "index.html",
            columnas=columnas,
            datos=datos,
            page=page,
            total_pages=total_pages,
            sort=sort,
            order=order,
            filtros=list(zip(columnas_filtro, valores_filtro))
        )

    except Exception as e:
        return render_template(
            "index.html",
            columnas=[],
            datos=[],
            error=str(e),
            page=1,
            total_pages=1,
            sort="",
            order="asc",
            filtros=[]
        )


# =========================
# 📤 FORMULARIO SUBIDA
# =========================
@app.route("/upload_form")
@login_requerido
def upload_form():
    from sqlalchemy import inspect
    tablas = inspect(engine).get_table_names()
    return render_template("upload.html", tablas=tablas)


# =========================
# 👁️ PREVIEW
# =========================
@app.route("/preview", methods=["POST"])
@login_requerido
def preview():
    file = request.files.get("file")
    ruta = guardar_archivo(file)

    if not ruta:
        return error("No seleccionaste archivo")

    try:
        df_original = leer_excel(ruta)
        df_procesado, cambios = procesar_excel(df_original.copy())

        tabla_html = df_procesado.head(10).to_html(
            classes="table table-striped",
            index=False
        )

        return render_template(
            "preview.html",
            tabla=tabla_html,
            cambios=cambios,
            archivo=ruta,
            accion=request.form.get("accion"),
            tabla_crear=request.form.get("tabla_crear"),
            tabla_existente=request.form.get("tabla_existente")
        )

    except Exception as e:
        return error(f"Error en preview: {str(e)}")


# =========================
# 📤 SUBIR A DB
# =========================
@app.route("/upload", methods=["POST"])
@login_requerido
def upload():

    ruta = request.form.get("file_name")

    if not ruta:
        return error("Archivo no encontrado")

    accion = request.form.get("accion")

    if accion == "crear":
        nombre_tabla = request.form.get("tabla_crear")
    elif accion == "agregar":
        nombre_tabla = request.form.get("tabla_existente")
    else:
        return error("Acción inválida")

    try:
        df = leer_excel(ruta)
        df, _ = procesar_excel(df)

        mensaje, registros = guardar_en_base(
            df,
            nombre_tabla,
            engine,
            accion
        )

        return render_template(
            "resultado.html",
            mensaje=mensaje,
            registros=registros
        )

    except Exception as e:
        return error(f"Error: {str(e)}")


# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)