
import os
import time
import cv2
import dlib
import numpy as np
from app import app

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from datetime import datetime

from flask import Blueprint, render_template, session, jsonify, Response
from database.database import get_db_connection
from database.models import QList
from app.tracking_func import (
    compute_face_descriptor,
    is_eye_closed,
    detect_head_rotation)


coding_test_tracking = Blueprint("coding_test_tracking", __name__)


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

executor = ThreadPoolExecutor(max_workers=4)  # 스레드 풀을 생성, 이거 지우면 카메라 안 뜸


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


@coding_test_tracking.route('/face_info')
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


@coding_test_tracking.route('/video_feed')
def video_feed():
    return Response(eye_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')


@coding_test_tracking.route("/test/<int:q_id>")
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


    




