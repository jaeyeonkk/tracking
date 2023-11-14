
from flask import Blueprint, render_template, request
from datetime import datetime
from flask_login import login_required
from sqlalchemy import func

from database.database import get_db_connection
from database.models import QList, FaceSubmissions, FaceUser


dashboard = Blueprint('dashboard', __name__)

PER_PAGE = 10

@dashboard.route("/dashboard")
@login_required
def admin():
    page = request.args.get("page", 1, type=int)

    # 페이지 번호가 0이하일 경우 1로 설정
    if page < 1:
        page = 1

    conn = get_db_connection()

    total_tests = conn.query(func.count(QList.q_id)).scalar()

    q_list = (
        conn.query(QList.q_id, QList.q_level, QList.q_name, 
                   QList.q_lang, QList.short_description)

        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    conn.close()

    return render_template(
        "dashboard.html",
        q_list=q_list,
        current_page=page,
        total_pages=(total_tests + PER_PAGE - 1) // PER_PAGE,
    )


@dashboard.route("/dashboard_detail/<int:q_id>")
@login_required
def dashboard_detail(q_id):
    conn = get_db_connection()

    q_info = conn.query(QList).filter(QList.q_id == q_id).first()


    submissions = (conn.query(FaceSubmissions, FaceUser.username)
                   .join(FaceUser, FaceSubmissions.user_id == FaceUser.id)
                   .filter(FaceSubmissions.q_id == q_id).all())
    
    # 각 제출에 대해 소요 시간(분과 초) 계산
    for i in range(len(submissions)):
        start_time = submissions[i][0].start_time
        submission_time = submissions[i][0].submission_time

        if start_time and submission_time:
            time_diff = submission_time - start_time
            minutes, seconds = divmod(time_diff.total_seconds(), 60)
            submissions[i] = (*submissions[i], (int(minutes), int(seconds)))  # 기존 튜플에 소요 시간 추가

    conn.close()
    
    return render_template("dashboard_detail.html", q_list=q_info, submissions=submissions)