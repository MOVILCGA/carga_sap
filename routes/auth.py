from flask import Blueprint, render_template, request, redirect, url_for
from time import time

from backend.login import validar_usuario, iniciar_sesion, cerrar_sesion
from backend.intentos_login import obtener_intentos, guardar_intentos

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
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
            return redirect(url_for("dashboard.index"))

        else:
            data["intentos"] += 1

            if data["intentos"] >= 5:
                data["bloqueado_hasta"] = time() + 60

            guardar_intentos(ip, data["intentos"], data["bloqueado_hasta"])
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    cerrar_sesion()
    return redirect(url_for("auth.login"))