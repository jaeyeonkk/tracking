import time
from flask import Flask, jsonify, render_template, Response
import cv2
import dlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pygame

app = Flask(__name__)

# 효과음
pygame.mixer.init()
pygame.mixer.music.load("pjstall.wav")

# 모델 및 데이터 로더
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
detector = dlib.get_frontal_face_detector()
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

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

    if mouth_movement < 20:
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
                        pygame.mixer.music.play()
                        alert_playing = True
            else:
                if alert_playing:
                    pygame.mixer.music.stop()
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
    global face_count, last_face_seen_time, face_changed, head_rotation_alert
    no_face_for = (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
    return jsonify(face_count=face_count, no_face_for=no_face_for, face_changed=face_changed, head_rotation_alert=head_rotation_alert)

@app.route("/video_feed")
def video_feed():
    return Response(
        eye_tracking(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)
