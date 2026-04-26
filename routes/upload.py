from flask import Blueprint, render_template, request
from sqlalchemy import inspect

from backend.base_datos import engine
from backend.excel import leer_excel, procesar_excel, guardar_en_base
from backend.archivos import guardar_archivo

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload_form")
def upload_form():
    tablas = inspect(engine).get_table_names()
    return render_template("upload.html", tablas=tablas)


@upload_bp.route("/preview", methods=["POST"])
def preview():

    file = request.files.get("file")
    ruta = guardar_archivo(file)

    if not ruta:
        return render_template("resultado.html", mensaje="Error", registros=0)

    df = leer_excel(ruta)
    df, cambios = procesar_excel(df)

    tabla_html = df.head(10).to_html(classes="table table-striped", index=False)

    return render_template("preview.html", tabla=tabla_html, cambios=cambios, archivo=ruta)


@upload_bp.route("/upload", methods=["POST"])
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