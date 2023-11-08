import html
import pytz

from datetime import datetime

from flask import Blueprint, render_template, session, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from app.compile import (
    c_compile_code,
    python_run_code,
    cpp_compile_code,
    java_compile_run_code,
    grade_code,
)
from database.database import get_db_connection
from database.models import QList, Student

from sqlalchemy import and_, or_

coding_test = Blueprint("coding_test", __name__)

PER_PAGE = 10

@login_required
@coding_test.route("/test_list")
def test_list():
    page = request.args.get("page", 1, type=int)

    # 페이지 번호가 0이하일 경우 1로 설정
    if page < 1:
        page = 1

    levels = [html.escape(level) for level in request.args.getlist("levels")]
    languages = [html.escape(language) for language in request.args.getlist("languages")]

    filters = []
    level_filters = []
    language_filters = []

    for level in levels:
        level_filters.append(QList.q_level == level)

    for lang in languages:
        language_filters.append(QList.q_lang == lang)

    if level_filters:
        filters.append(or_(*level_filters))

    if language_filters:
        filters.append(or_(*language_filters))

    conn = get_db_connection()

    total_tests = conn.query(func.count(QList.q_id)).filter(and_(*filters)).scalar()

    q_list = (
        conn.query(QList.q_id, QList.q_level, QList.q_name, QList.q_lang)
        .filter(and_(*filters))
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    conn.close()

    return render_template(
        "test_list.html",
        q_list=q_list,
        current_page=page,
        total_pages=(total_tests + PER_PAGE - 1) // PER_PAGE,
    )


@coding_test.route("/test/<int:q_id>")
def test_view(q_id):

    conn = get_db_connection()
    q_info = conn.query(QList).filter(QList.q_id == q_id).first()

    # # 현재 시간을 기록
    # seoul_timezone = pytz.timezone("Asia/Seoul")  # 한국 시간
    # test_start_time = datetime.now(seoul_timezone)

    # # 데이터베이스에 테스트 시작 시간 저장
    # student = Student(q_id=q_id, test_start_time=test_start_time)
    # conn.add(student)
    # conn.commit()

    q_info.ex_print = q_info.ex_print.replace("\n", "<br>")
    session["q_id"] = q_id
    conn.close()

    return render_template("test.html", q_list=q_info)


@coding_test.route("/accept_cam/<int:q_id>", methods=['GET', 'POST'])
def accept_cam(q_id):
    session["q_id"] = q_id

    if request.method == "POST":
        name = request.form.get("name")
        q_id = request.form.get("q_id")  # 추가된 문제 번호
        test_start_time = request.form.get("test_start_time")  # 추가된 시작 시간

        if name:
            db_session = get_db_connection()

            # 현재 시간을 기록
            seoul_timezone = pytz.timezone("Asia/Seoul")  # 한국 시간
            test_start_time = datetime.now(seoul_timezone)

            new_student = Student(name=name, q_id=q_id, test_start_time=test_start_time)  # 이름, 문제 번호, 시작 시간 저장
            db_session.add(new_student)
            db_session.commit()
            db_session.close()

            session["q_id"] = q_id
            return redirect(url_for("coding_test.test_view", q_id=q_id))

    return render_template("accept_cam.html", q_id=q_id)



@coding_test.route("/compile", methods=["POST"])
def compile():
    code = request.form.get("code")
    language = request.form.get("language")

    session["language"] = language  # 언어 정보를 세션에 저장

    if language == "python":
        output_str = python_run_code(code)
    elif language == "c":
        output_str = c_compile_code(code)
    elif language == "c++":
        output_str = cpp_compile_code(code)
    elif language == "java":
        output_str = java_compile_run_code(code)

    return output_str


@coding_test.route("/submit", methods=["POST"])
def submit():
    conn = get_db_connection()

    code = request.form.get("code")
    language = request.form.get("language")

    session["language"] = language

    if language == "python":
        output_str = python_run_code(code)
    elif language == "c":
        output_str = c_compile_code(code)
    elif language == "c++":
        output_str = cpp_compile_code(code)
    elif language == "java":
        output_str = java_compile_run_code(code)

    q_info = conn.query(QList).filter(QList.q_id == session["q_id"]).first()
    expected_output = q_info.answer

    result = grade_code(output_str, expected_output)

    # 채점 결과를 세션에 저장
    if result == "정답입니다!":
        session["is_correct"] = True
    else:
        session["is_correct"] = False

    conn.close()

    return result  # 채점 결과를 반환