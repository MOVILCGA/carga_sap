from flask import session
from backend.base_datos import engine
from sqlalchemy import text


# =========================
# ?? SESIÓN
# =========================
def iniciar_sesion(usuario):
    session["user"] = usuario


def cerrar_sesion():
    session.pop("user", None)


def esta_logueado():
    return "user" in session


# =========================
# ?? VALIDAR USUARIO (SIN HASH)
# =========================
def validar_usuario(usuario, password):

    # ?? mejor: no traer todo, solo 1 registro
    query = text("""
        SELECT 1
        FROM usuarios
        WHERE username = :user AND password = :pass
        LIMIT 1
    """)

    with engine.connect() as conn:
        resultado = conn.execute(query, {
            "user": usuario.strip(),
            "pass": password.strip()
        }).fetchone()

    return resultado is not None