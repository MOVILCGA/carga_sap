from sqlalchemy import text
from backend.base_datos import engine


def obtener_procesos():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT PROCESO
            FROM vista_cm01_final
            WHERE PROCESO IS NOT NULL
            ORDER BY PROCESO
        """))

        return [row[0] for row in result.fetchall()]


def obtener_grafica_proceso(proceso):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT Centro, COUNT(*) as total
            FROM vista_cm01_final
            WHERE PROCESO = :proceso
            GROUP BY Centro
            ORDER BY Centro
        """), {"proceso": proceso}).fetchall()

    nombres = {
        "1000": "Bogotá",
        "5000": "Cali",
        "6000": "Bucaramanga"
    }

    labels = []
    values = []

    for row in result:
        centro = str(row[0])
        labels.append(nombres.get(centro, centro))
        values.append(row[1])

    return labels, values


def obtener_dashboard(page, per_page, sort, order):
    offset = (page - 1) * per_page

    with engine.connect() as conn:

        columnas_query = conn.execute(text("SELECT * FROM vista_cm01_final LIMIT 1"))
        columnas = list(columnas_query.keys())

        if sort not in columnas:
            sort = columnas[0]

        if order not in ["asc", "desc"]:
            order = "asc"

        query = f"""
            SELECT *
            FROM vista_cm01_final
            ORDER BY `{sort}` {order}
            LIMIT :limit OFFSET :offset
        """

        datos = conn.execute(text(query), {
            "limit": per_page,
            "offset": offset
        }).fetchall()

        total = conn.execute(text("SELECT COUNT(*) FROM vista_cm01_final")).scalar()

        total_pages = (total // per_page) + (1 if total % per_page else 0)

    return columnas, datos, total_pages