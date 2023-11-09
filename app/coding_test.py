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
#from app.tracking import eye_tracking

from database.database import get_db_connection
from database.models import QList, FaceSubmissions

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

    return render_template("test.html", q_list=q_info, q_id=q_id)


# @coding_test.route('/face_info')
# def face_info_route():
#     global face_count, last_face_seen_time, face_changed, head_rotation_alert
#     no_face_for = (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
#     return jsonify(face_count=face_count, no_face_for=no_face_for, face_changed=face_changed, head_rotation_alert=head_rotation_alert)


# @coding_test.route('/video_feed')
# def video_feed():
#     return Response(eye_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')
    



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


import os
import time
import cv2
import dlib
import numpy as np
# import pygame
from app import app

from flask import current_app
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# from database.database import get_db_connection
# from database.models import FaceSubmissions


# 효과음 초기화 및 로드
# pygame.mixer.init()
# sound_file_path = os.path.join(app.root_path, 'static/audio', 'pjstall.wav')
# pygame.mixer.music.load(sound_file_path)

# 모델 로드
models_path = os.path.join(app.root_path, 'models')
predictor_path = os.path.join(models_path, 'shape_predictor_68_face_landmarks.dat')
face_rec_model_path = os.path.join(models_path, 'dlib_face_recognition_resnet_model_v1.dat')


predictor = dlib.shape_predictor(predictor_path)
detector = dlib.get_frontal_face_detector()
face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)


# 전역 변수를 선언하고 초기화
face_count = 0
last_face_seen_time = None
last_face_descriptor = None
face_changed = False
alert_playing = False
eyes_closed_start_time = None
head_rotation_alert = False

executor = ThreadPoolExecutor(max_workers=4)  # 스레드 풀을 생성


# 얼굴 특성 계산 함수
def compute_face_descriptor(frame, landmarks):
    global last_face_descriptor, face_changed
    current_face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)

    if last_face_descriptor and current_face_descriptor:
        diff = sum([(a - b)**2 for a, b in zip(last_face_descriptor, current_face_descriptor)])
        if diff > 0.2:  # 이 값을 조정하여 감지 감도를 변경
            face_changed = True
        else:
            face_changed = False  # 얼굴 특성이 일치할 때 face_changed를 False로 설정
        last_face_descriptor = current_face_descriptor
    elif current_face_descriptor is not None:
        last_face_descriptor = current_face_descriptor
        face_changed = False


# 눈 좌표 추출 함수
def get_eye_landmarks(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    landmarks = []

    for face in faces:
        landmarks.append(predictor(gray, face))

    return landmarks


# 눈 감았는지 확인하는 함수
def is_eye_closed(landmarks):
    left_eye_ratio = (landmarks.part(42).y - landmarks.part(38).y) / (landmarks.part(40).x - landmarks.part(36).x)
    right_eye_ratio = (landmarks.part(47).y - landmarks.part(43).y) / (landmarks.part(45).x - landmarks.part(41).x)

    return left_eye_ratio < 0.2 and right_eye_ratio < 0.2


# 두 점 사이의 거리를 계산하는 함수
def get_distance(p1, p2):
    return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)


# 입술 움직임을 계산하는 함수
def get_mouth_movement(landmarks):
    upper_lip = landmarks.part(51)
    lower_lip = landmarks.part(57)
    return get_distance(upper_lip, lower_lip)


# 고개 회전 감지 함수
def detect_head_rotation(landmarks):
    global head_rotation_alert
    nose_tip = landmarks.part(30)
    mouth_left = landmarks.part(48)
    mouth_right = landmarks.part(54)
    ratio = get_distance(nose_tip, mouth_left) / get_distance(nose_tip, mouth_right)
    mouth_movement = get_mouth_movement(landmarks)

    if mouth_movement < 20: # 입술 움직임에 대한 임계값
        if ratio > 1.2 or ratio < 0.8: # 임계값
            head_rotation_alert = True
        else:
            head_rotation_alert = False
    else:
        head_rotation_alert = False


def eye_tracking():
    global face_count, last_face_seen_time, alert_playing, eyes_closed_start_time, head_rotation_alert

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 15)  # FPS를 15로 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 너비를 640으로 설정
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 높이를 480으로 설정
    frame_count = 0 

    while True:
        ret, frame = cap.read()

        if not ret:
            break
            
        frame = cv2.flip(frame, 1)  # 좌우 반전 적용
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        face_count = len(faces)

        if face_count > 0:
            last_face_seen_time = datetime.now()

        for face in faces:
            landmarks = predictor(gray, face)
            detect_head_rotation(landmarks)

            if is_eye_closed(landmarks):
                if not alert_playing:
                    if eyes_closed_start_time is None:
                        eyes_closed_start_time = time.time()
                    elif time.time() - eyes_closed_start_time > 5:
                        # pygame.mixer.music.play()
                        alert_playing = True
            else:
                if alert_playing:
                #     pygame.mixer.music.stop()
                    alert_playing = False
                eyes_closed_start_time = None
                    
            # 10 프레임마다 얼굴 특성 계산을 수행
            if frame_count % 10 == 0:
                executor.submit(compute_face_descriptor, frame, landmarks)

        frame_count += 1  # 프레임 카운터를 증가
        
        # JPEG 형식으로 인코딩하여 웹페이지에 전송
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

    cap.release()


@app.route('/face_info')
def face_info_route():
    global face_count, last_face_seen_time, face_changed, head_rotation_alert, alert_playing
    no_face_for = (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
    return jsonify(
        face_count=face_count,
        no_face_for=no_face_for,
        face_changed=face_changed,
        head_rotation_alert=head_rotation_alert,
        alert_playing=alert_playing  # 이 값을 추가
    )


@app.route('/video_feed')
def video_feed():
    return Response(eye_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')


