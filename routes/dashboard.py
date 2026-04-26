from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from functools import wraps

from backend.base_datos import engine
from backend.login import esta_logueado

# 🔥 Blueprint con prefijo
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


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
# 🏠 INDEX (/dashboard/)
# =========================
@dashboard_bp.route("/")
@login_requerido
def index():
    return render_template("index.html")


# =========================
# 📊 DASHBOARD (/dashboard/tabla)
# =========================
@dashboard_bp.route("/tabla")
@login_requerido
def dashboard():

    page = int(request.args.get("page", 1))
    sort = request.args.get("sort", "")
    order = request.args.get("order", "asc")

    # 🔥 filtros tipo Excel
    columnas_filtro = request.args.getlist("column[]")
    valores_filtro = request.args.getlist("search[]")

    per_page = 50
    offset = (page - 1) * per_page

    try:
        with engine.connect() as conn:

            columnas_query = conn.execute(
                text("SELECT * FROM vista_cm01_final LIMIT 1")
            )
            columnas = list(columnas_query.keys())

            # =========================
            # 🔍 WHERE dinámico
            # =========================
            where_clauses = []
            params = {}

            for i, col in enumerate(columnas_filtro):
                if col and i < len(valores_filtro) and valores_filtro[i]:
                    key = f"valor{i}"
                    where_clauses.append(f"`{col}` LIKE :{key}")
                    params[key] = f"%{valores_filtro[i]}%"

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            # =========================
            # 🔽 Orden
            # =========================
            if sort not in columnas:
                sort = columnas[0]

            if order not in ["asc", "desc"]:
                order = "asc"

            # =========================
            # 📊 QUERY
            # =========================
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

            # =========================
            # 🔢 TOTAL
            # =========================
            count_query = f"""
                SELECT COUNT(*)
                FROM vista_cm01_final
                {where_sql}
            """

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