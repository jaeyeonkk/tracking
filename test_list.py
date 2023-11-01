import html

from flask import Blueprint, render_template, session, request
from sqlalchemy import func

from app.compile import (
    c_compile_code,
    python_run_code,
    cpp_compile_code,
    java_compile_run_code,
    grade_code,
)

from database.database import get_db_connection
from database.models import QList, CodeSubmission

from sqlalchemy import and_, or_

coding_test = Blueprint("coding_test", __name__)

PER_PAGE = 10


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

    q_info.ex_print = q_info.ex_print.replace("\n", "<br>")

    session["q_id"] = q_id

    conn.close()

    return render_template("test.html", q_list=q_info)


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


@coding_test.route("/answer")
def answer():
    conn = get_db_connection()

    q_info = conn.query(QList).filter(QList.q_id == session["q_id"]).first()

    # 세션의 언어 정보에 따라 C 언어 정답 코드 혹은 Python 정답 코드를 가져옴
    if session["language"] == "c":
        answer = html.escape(q_info.c_answer_code)
    elif session["language"] == "python":
        answer = html.escape(q_info.p_answer_code)
    elif session["language"] == "c++":
        answer = html.escape(q_info.cpp_answer_code)
    elif session["language"] == "java":
        answer = html.escape(q_info.j_answer_code)

    conn.close()

    return "<pre>" + answer + "</pre>"

