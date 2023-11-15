# import pytz
import datetime
# import dateutil.parser

from datetime import datetime, timedelta
from flask import Blueprint, render_template, session, request, redirect, url_for
from flask_login import current_user, login_required

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
from database.models import FaceSubmissions, QList


coding_test_utils = Blueprint("coding_test_utils", __name__)


PER_PAGE = 10

def convert_to_kst(utc_time_str):
    if utc_time_str is None:
        # utc_time_str이 None일 경우 현재 시간을 사용하거나 오류를 반환
        return datetime.now()

    try:
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        kst_time = utc_time + timedelta(hours=9)
        return kst_time
    except ValueError:
        # 잘못된 시간 형식일 경우 처리
        return datetime.now()


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
    if result == "정답입니다!😊":
        session["is_correct"] = True
    else:
        session["is_correct"] = False

    # JavaScript에서 전송된 추가 데이터를 받음
    face_many = request.form.get("face_many", 0, type=int)
    face_empty = request.form.get("face_empty", 0, type=int)
    face_change = request.form.get("face_change", 0, type=int)
    head_rotation = request.form.get("head_rotation", 0, type=int)

    # 클라이언트로부터 받은 시간 데이터를 파싱
    start_time_str = request.form.get("start_time")
    submission_time_str = request.form.get("submission_time")

    # UTC 시간을 KST로 변환
    start_time = convert_to_kst(start_time_str)
    submission_time = convert_to_kst(submission_time_str)

    # FaceSubmissions 객체 생성
    new_submission = FaceSubmissions(
        q_id=session["q_id"],
        user_id=current_user.get_id(),
        code_content=code,
        start_time=start_time,
        submission_time=submission_time,
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

