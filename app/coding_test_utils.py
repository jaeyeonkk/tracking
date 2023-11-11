# import pytz
import datetime

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
from app.csrf_protection import csrf
from app.forms import AcceptForm

from database.database import get_db_connection
from database.models import QList, FaceSubmissions


coding_test_utils = Blueprint("coding_test_utils", __name__)


PER_PAGE = 10


@coding_test_utils.route("/test_list")
@login_required
def test_list():
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
        "test_list.html",
        q_list=q_list,
        current_page=page,
        total_pages=(total_tests + PER_PAGE - 1) // PER_PAGE,
    )


@coding_test_utils.route("/accept_cam/<int:q_id>", methods=['GET', 'POST'])
@login_required
def accept_cam(q_id):
    form = AcceptForm()
    if form.validate_on_submit(): 
        # form 제출 처리(예: 데이터베이스에 데이터 저장)
        return redirect(url_for("coding_test_tracking.test_view", q_id=q_id))
    
    return render_template("accept_cam.html", form=form, q_id=q_id)


@coding_test_utils.route("/compile", methods=["POST"])
@csrf.exempt
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


@coding_test_utils.route("/submit", methods=["POST"])
@csrf.exempt
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

    # JavaScript에서 전송된 추가 데이터를 받음
    face_many = request.form.get("face_many", 0, type=int)
    face_empty = request.form.get("face_empty", 0, type=int)
    face_change = request.form.get("face_change", 0, type=int)
    head_rotation = request.form.get("head_rotation", 0, type=int)

    # FaceSubmissions 객체 생성
    new_submission = FaceSubmissions(
        q_id=session["q_id"],
        user_id=current_user.get_id(),
        code_content=code,
        start_time=session.get("start_time", datetime.datetime.now()),
        submission_time=datetime.datetime.now(),
        is_correct=session.get("is_correct", False),
        compile_result=output_str,
        language=language,
        face_many=face_many,
        face_empty=face_empty,
        face_change=face_change,
        head_rotation=head_rotation
    )

    # 데이터베이스에 저장
    conn.add(new_submission)
    conn.commit()

    conn.close()

    return result  # 채점 결과를 반환


# @coding_test.route("/save_code", methods=["POST"])
# @csrf.exempt
# def code_save():
#     try:
#         db_session = get_db_connection()

#         q_id = request.form.get("q_id")
#         user_id = request.form.get("user_id")
#         code_content = request.form.get("code_content")
#         language = request.form.get("language")
#         compile_result = request.form.get("compile_result")
#         is_correct = session.pop("is_correct", None)

#         # 데이터베이스에 저장
#         new_submission = CodeSubmission(
#             q_id=q_id,
#             user_id=user_id,
#             code_content=code_content,
#             language=language,
#             compile_result=compile_result,
#             is_correct=is_correct,
#         )

#         db_session.add(new_submission)
#         db_session.commit()
#         db_session.close()

#         return jsonify({"message": "Code saved successfully!"})

#     except Exception as e:
#         return jsonify({"error": str(e)})
