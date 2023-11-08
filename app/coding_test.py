# import pytz

from datetime import datetime

from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify, Response
from flask_login import login_required

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
from app.tracking import eye_tracking

from database.database import get_db_connection
from database.models import QList

# from sqlalchemy import and_, or_

coding_test = Blueprint("coding_test", __name__)


# 전역 변수
PER_PAGE = 10
face_count = 0
last_face_seen_time = None  # datetime 객체로 초기화하거나 처음 호출 시 현재 시간으로 설정
face_changed = False
head_rotation_alert = False


@coding_test.route("/test_list")
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


@coding_test.route("/test/<int:q_id>")
def test_view(q_id):

    conn = get_db_connection()
    q_info = conn.query(QList).filter(QList.q_id == q_id).first()

    # 현재 시간을 기록
    # seoul_timezone = pytz.timezone("Asia/Seoul")  # 한국 시간
    # start_time = datetime.now(seoul_timezone)

    #  데이터베이스에 테스트 시작 시간 저장
    # student = Student(q_id=q_id, test_start_time=test_start_time)
    # conn.add(student)
    # conn.commit()

    q_info.ex_print = q_info.ex_print.replace("\n", "<br>")
    session["q_id"] = q_id
    conn.close()

    return render_template("test.html", q_list=q_info)


@coding_test.route('/face_info')
def face_info_route():
    global face_count, last_face_seen_time, face_changed, head_rotation_alert
    no_face_for = (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
    return jsonify(face_count=face_count, no_face_for=no_face_for, face_changed=face_changed, head_rotation_alert=head_rotation_alert)


@coding_test.route('/video_feed')
def video_feed():
    return Response(eye_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')


@coding_test.route("/accept_cam/<int:q_id>", methods=['GET', 'POST'])
@login_required
def accept_cam(q_id):
    form = AcceptForm()
    if form.validate_on_submit(): 
        # form 제출 처리(예: 데이터베이스에 데이터 저장)
        return redirect(url_for("coding_test.test_view", q_id=q_id))
    
    return render_template("accept_cam.html", form=form, q_id=q_id)


@coding_test.route("/compile", methods=["POST"])
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


@coding_test.route("/submit", methods=["POST"])
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
