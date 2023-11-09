import os
import cv2
import dlib
import numpy as np
from app import app

from concurrent.futures import ThreadPoolExecutor


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