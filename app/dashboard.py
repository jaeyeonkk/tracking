from flask import Blueprint, request, render_template
from flask_login import login_required

from database.database import get_db_connection
from database.models import QList

from sqlalchemy import func

# auth = Blueprint("auth", __name__)
dashboard = Blueprint("dashboard", __name__)

PER_PAGE = 10

@dashboard.route("/admin")
@login_required
def admin():
    page = request.args.get("page", 1, type=int)

    # 페이지 번호가 0이하일 경우 1로 설정
    if page < 1:
        page = 1

    conn = get_db_connection()

    total_tests = conn.query(func.count(QList.q_id)).scalar()

    q_list = (
        conn.query(QList.q_id, QList.q_level, QList.q_name)
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    conn.close()

    return render_template(
        "admin.html",
        q_list=q_list,
        current_page=page,
        total_pages=(total_tests + PER_PAGE - 1) // PER_PAGE,
    )