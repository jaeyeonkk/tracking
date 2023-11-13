
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app import app
from database.database import get_db_connection
from database.models import QList


PER_PAGE = 10 


@app.route("/")
def not_logged_home():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("main.html")


@app.route('/iframe')
def iframe():
    return render_template('iframe.html')


@app.route('/iiframe')
def iiframe():
    return render_template('iiframe.html')


@app.route("/main")
@login_required
def home():
    return render_template("main2.html")


@app.route("/dashboard")
def dashboard():
    page = request.args.get("page", 1, type=int)

    # 페이지 번호가 0이하일 경우 1로 설정
    if page < 1:
        page = 1

    conn = get_db_connection()

    total_tests = conn.query(func.count(QList.q_id)).scalar()

    q_list = (
        conn.query(QList.q_id, QList.q_level, QList.q_name, QList.q_lang)

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


if __name__ == "__main__":
    app.run("0.0.0.0", port="5000", debug=True)