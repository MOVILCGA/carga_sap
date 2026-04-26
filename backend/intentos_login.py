from sqlalchemy import text
from backend.base_datos import engine


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
        return {
            "intentos": result[0],
            "bloqueado_hasta": result[1]
        }
    else:
        return {
            "intentos": 0,
            "bloqueado_hasta": 0
        }


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