from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text

from backend.base_datos import engine
from backend.login import esta_logueado

proceso_bp = Blueprint("proceso", __name__)


def login_requerido(f):
    from functools import wraps
    from flask import redirect, url_for

    @wraps(f)
    def decorated(*args, **kwargs):
        if not esta_logueado():
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@proceso_bp.route("/proceso")
@login_requerido
def proceso():

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT PROCESO
            FROM vista_cm01_final
            ORDER BY PROCESO
        """))

        procesos = [row[0] for row in result.fetchall()]

    return render_template("proceso.html", procesos=procesos)


@proceso_bp.route("/api/proceso_chart")
@login_requerido
def proceso_chart():

    proceso = request.args.get("proceso")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT Centro, COUNT(*) as total
            FROM vista_cm01_final
            WHERE PROCESO = :proceso
            GROUP BY Centro
        """), {"proceso": proceso}).fetchall()

    nombres = {
        "1000": "Bogotá",
        "5000": "Cali",
        "6000": "Bucaramanga"
    }

    labels = [nombres.get(str(r[0]), str(r[0])) for r in result]
    values = [r[1] for r in result]

    return jsonify({"labels": labels, "values": values})