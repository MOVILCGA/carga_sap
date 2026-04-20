from flask import Flask, render_template, request, redirect, url_for
import os
from functools import wraps
from werkzeug.utils import secure_filename

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
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("username")
        password = request.form.get("password")

        if validar_usuario(usuario, password):
            iniciar_sesion(usuario)
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Datos incorrectos")

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
    from sqlalchemy import inspect
    tablas = inspect(engine).get_table_names()
    return render_template("index.html", tablas=tablas)


# =========================
# 👁️ PREVIEW + CAMBIOS
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

        # 🔥 AQUÍ YA VIENE CON CAMBIOS
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
# 📤 SUBIR (YA CONFIRMADO)
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

    if not nombre_tabla:
        return error("Debes indicar una tabla")

    try:
        df = leer_excel(ruta)

        # 🔥 IMPORTANTE: ignoramos cambios aquí
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